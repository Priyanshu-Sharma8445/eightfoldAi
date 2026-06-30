# app/projection.py

import re
import logging
from typing import Any, Dict, Optional, List
from app.schemas import CanonicalProfile
from app.config import RuntimeConfig, FieldConfig
from app.normalizers.phone import normalize_phone

logger = logging.getLogger(__name__)

def resolve_from_path(data: Dict[str, Any], path: str) -> Any:
    """
    Resolve value from nested dictionary using dot and bracket notation.
    E.g., "emails[0]", "location.city", "full_name".
    """
    parts = path.split('.')
    current = data
    for part in parts:
        # Check for list indexing: name[index]
        match = re.match(r'^(\w+)\[(\d+)\]$', part)
        if match:
            field_name = match.group(1)
            index = int(match.group(2))
            if not isinstance(current, dict) or field_name not in current:
                return None
            lst = current[field_name]
            if not isinstance(lst, list) or index >= len(lst):
                return None
            current = lst[index]
        else:
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
            
    return current

def cast_type(value: Any, target_type: str) -> Any:
    """
    Cast value to target data type: string, integer, float, list, object.
    """
    if value is None:
        return None
        
    try:
        if target_type == "string":
            return str(value)
        elif target_type == "integer":
            return int(float(value))
        elif target_type == "float":
            return float(value)
        elif target_type == "list":
            if isinstance(value, list):
                return value
            return [value]
        elif target_type == "object":
            return value
    except Exception as e:
        logger.warning(f"Failed to cast value {value} to type {target_type}: {str(e)}")
        
    return value

def project_profile(canonical: CanonicalProfile, config: RuntimeConfig) -> Dict[str, Any]:
    """
    Project canonical candidate profile into customized dictionary structure based on RuntimeConfig.
    Handles missing values, type casting, field mapping, and metadata toggles.
    """
    canonical_dict = canonical.model_dump()
    output: Dict[str, Any] = {}
    
    if config.fields:
        for field_cfg in config.fields:
            # Resolve value from canonical profile dictionary
            source_path = field_cfg.from_field if field_cfg.from_field else field_cfg.path
            value = resolve_from_path(canonical_dict, source_path)
            
            # Apply E164 normalization logic dynamically if specified in custom normalize option
            if field_cfg.normalize == "E164" and value and isinstance(value, str):
                normalized_val, _ = normalize_phone(value)
                value = normalized_val
                
            # Handle missing values
            if value is None or value == "" or (isinstance(value, list) and not value):
                if field_cfg.required:
                    if config.on_missing == "error":
                        raise ValueError(f"Required field '{field_cfg.path}' is missing (mapped from '{source_path}').")
                    elif config.on_missing == "omit":
                        continue
                    else:  # "null"
                        output[field_cfg.path] = None
                else:
                    if config.on_missing == "omit":
                        continue
                    else:  # "null"
                        output[field_cfg.path] = None
            else:
                # Cast to requested type
                output[field_cfg.path] = cast_type(value, field_cfg.type)
    else:
        # Default output schema mapping (exclude provenance and overall_confidence, which are handled at root level)
        default_fields = [
            "candidate_id", "full_name", "emails", "phones", "location", "links",
            "headline", "years_experience", "skills", "experience", "education"
        ]
        for field in default_fields:
            val = canonical_dict.get(field)
            if val is None or val == "":
                if config.on_missing == "omit":
                    continue
                else:
                    output[field] = None
            else:
                output[field] = val
                
    # Add metadata fields if toggled
    if config.include_provenance:
        output["provenance"] = canonical_dict.get("provenance", [])
    if config.include_confidence:
        output["overall_confidence"] = canonical_dict.get("overall_confidence", 1.0)
        
    return output
