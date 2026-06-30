# app/main.py

import os
import sys
import json
import argparse
import logging
from typing import List, Tuple, Optional
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

# Add current directory to path if not present for import stability
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import RuntimeConfig
from app.pipeline.pipeline import run_pipeline

# Initialize Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Source Candidate Data Transformer API",
    description="Transforms, normalizes, and merges candidate profiles from multiple sources into a canonical profile.",
    version="1.0.0"
)

def load_config(config_path: str) -> RuntimeConfig:
    """
    Load RuntimeConfig from file path. Resolves path relative to project root if needed.
    """
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return RuntimeConfig(**data)
            
    # Attempt relative path resolution
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resolved_path = os.path.join(base_dir, config_path)
    if os.path.exists(resolved_path):
        with open(resolved_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return RuntimeConfig(**data)
            
    logger.warning(f"Config path '{config_path}' not found. Using default config.")
    # Fallback: empty config maps to default candidate schema projection
    return RuntimeConfig()

@app.post("/transform")
async def transform(
    files: Optional[List[UploadFile]] = File(None),
    csv: UploadFile = File(None),
    resume: UploadFile = File(None),
    config_json: Optional[str] = Form(None)
):
    """
    POST endpoint to transform multiple candidate source profiles.
    Accepts multiple uploaded files (CSV or TXT resume) and an optional projection config.
    """
    sources_data: List[Tuple[str, str]] = []
    
    # Process files uploaded in list
    if files:
        for file in files:
            content = await file.read()
            try:
                content_str = content.decode("utf-8")
            except UnicodeDecodeError:
                content_str = content.decode("latin-1")
            sources_data.append((file.filename, content_str))
            
    # Process explicit csv file
    if csv:
        content = await csv.read()
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            content_str = content.decode("latin-1")
        sources_data.append((csv.filename, content_str))
        
    # Process explicit resume file
    if resume:
        content = await resume.read()
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            content_str = content.decode("latin-1")
        sources_data.append((resume.filename, content_str))

    if not sources_data:
        raise HTTPException(
            status_code=400,
            detail="No files uploaded. Provide file(s) under 'files', 'csv', or 'resume' multi-part parameters."
        )

    # Parse config
    if config_json:
        try:
            config_dict = json.loads(config_json)
            config = RuntimeConfig(**config_dict)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Malformed config JSON: {str(e)}")
    else:
        config = load_config("configs/default.json")

    try:
        result = run_pipeline(sources_data, config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"Type mismatch validation: {str(e)}")
    except Exception as e:
        logger.error("Error occurred in transform pipeline", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

def run_cli():
    """
    Entrypoint for CLI execution.
    """
    parser = argparse.ArgumentParser(description="Multi-Source Candidate Data Transformer CLI")
    parser.add_argument("--csv", help="Path to structured candidate CSV")
    parser.add_argument("--resume", help="Path to unstructured candidate resume TXT")
    parser.add_argument("--config", default="configs/default.json", help="Path to projection config JSON")
    parser.add_argument("--server", action="store_true", help="Launch FastAPI Web Server instead of CLI run")
    parser.add_argument("--host", default="127.0.0.1", help="Web server host")
    parser.add_argument("--port", type=int, default=8000, help="Web server port")
    
    args = parser.parse_args()
    
    if args.server:
        logger.info(f"Starting server on {args.host}:{args.port}...")
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)
        return

    # Check for CLI pipeline execution inputs
    if not args.csv and not args.resume:
        logger.error("Error: You must provide at least --csv or --resume, or use --server to start the API.")
        parser.print_help()
        sys.exit(1)
        
    sources_data: List[Tuple[str, str]] = []
    
    # Read CSV
    if args.csv:
        if not os.path.exists(args.csv):
            logger.error(f"File not found: {args.csv}")
            sys.exit(1)
        with open(args.csv, "r", encoding="utf-8", errors="ignore") as f:
            sources_data.append((os.path.basename(args.csv), f.read()))
            
    # Read Resume
    if args.resume:
        if not os.path.exists(args.resume):
            logger.error(f"File not found: {args.resume}")
            sys.exit(1)
        with open(args.resume, "r", encoding="utf-8", errors="ignore") as f:
            sources_data.append((os.path.basename(args.resume), f.read()))

    # Load configuration
    config = load_config(args.config)
    
    try:
        result = run_pipeline(sources_data, config)
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Transformation failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # If no parameters are passed but execution is script, run CLI parser (which prints help or accepts params)
    # If '--server' or files are passed, argparse handles it.
    run_cli()
