# app/validator.py

import logging
from typing import Dict, Any
from app.config import RuntimeConfig

logger = logging.getLogger(__name__)

def validate_projected_json(data: Dict[str, Any], config: RuntimeConfig) -> bool:
    """
    Validates that the projected JSON matches type and requirement constraints.
    Raises ValueError or TypeError on validation failure.
    """
    if config.fields:
        for field in config.fields:
            name = field.path
            is_present = name in data
            val = data.get(name)
            
            # Check requirements
            if field.required and (not is_present or val is None or val == "" or (isinstance(val, list) and not val)):
                raise ValueError(f"Validation Error: Required field '{name}' is missing or empty in projected JSON.")
                
            # Check types
            if is_present and val is not None:
                if field.type == "string" and not isinstance(val, str):
                    raise TypeError(f"Validation Error: Field '{name}' must be of type string, got {type(val).__name__}.")
                elif field.type == "integer" and not isinstance(val, int):
                    raise TypeError(f"Validation Error: Field '{name}' must be of type integer, got {type(val).__name__}.")
                elif field.type == "float" and not isinstance(val, (int, float)):
                    raise TypeError(f"Validation Error: Field '{name}' must be of type float, got {type(val).__name__}.")
                elif field.type == "list" and not isinstance(val, list):
                    raise TypeError(f"Validation Error: Field '{name}' must be of type list, got {type(val).__name__}.")
                elif field.type == "object" and not isinstance(val, dict):
                    raise TypeError(f"Validation Error: Field '{name}' must be of type object, got {type(val).__name__}.")
    else:
        # Default Schema Validation
        # candidate_id, full_name, emails, phones, location, links, skills, experience, education are required
        # Note: location can be null if not found, but must be in JSON as a dict or None
        required_keys = ["candidate_id", "full_name", "emails", "phones", "links", "skills", "experience", "education"]
        for key in required_keys:
            if key not in data or data[key] is None or (isinstance(data[key], list) and not data[key] and key in ["emails", "phones"]):
                # Allow empty lists for skills, links, experience, education, but name, emails, phones must be populated
                if key in ["candidate_id", "full_name", "emails", "phones"]:
                    raise ValueError(f"Validation Error: Default required field '{key}' is missing or empty.")
                    
        # Validate data types for default fields
        type_checks = {
            "candidate_id": str,
            "full_name": str,
            "emails": list,
            "phones": list,
            "location": (dict, type(None)),
            "links": list,
            "headline": (str, type(None)),
            "years_experience": (int, float, type(None)),
            "skills": list,
            "experience": list,
            "education": list
        }
        for field, expected in type_checks.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected):
                    raise TypeError(f"Validation Error: Default field '{field}' must be of type {expected}, got {type(data[field]).__name__}.")
                    
    logger.info("Projected JSON output validated successfully.")
    return True
