# app/normalizers/skill.py

from typing import List, Dict, Optional
from app.constants import SKILL_DICTIONARY

def normalize_skill(skill: str, skill_dict: Optional[Dict[str, str]] = None) -> str:
    """
    Normalize different spellings of skills to a canonical name.
    If not in the dictionary, returns the original trimmed string.
    """
    if not skill or not isinstance(skill, str):
        return ""
    
    cleaned = skill.strip()
    dict_to_use = skill_dict if skill_dict is not None else SKILL_DICTIONARY
    
    # Convert dictionary keys to lowercase for robust lookup
    lookup_dict = {k.lower(): v for k, v in dict_to_use.items()}
    
    key = cleaned.lower()
    if key in lookup_dict:
        return lookup_dict[key]
        
    return cleaned

def normalize_skills(skills: List[str], skill_dict: Optional[Dict[str, str]] = None) -> List[str]:
    """
    Normalize list of skills, removing duplicates while preserving order.
    """
    if not skills:
        return []
    
    normalized = []
    seen = set()
    for s in skills:
        if not s or not isinstance(s, str):
            continue
        # Split skills that might be comma-separated inside raw data
        parts = [p.strip() for p in s.split(',')] if ',' in s else [s]
        for part in parts:
            cleaned = normalize_skill(part, skill_dict)
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                normalized.append(cleaned)
                
    return normalized
