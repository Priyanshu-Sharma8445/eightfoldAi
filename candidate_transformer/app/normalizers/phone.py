# app/normalizers/phone.py

from typing import List, Tuple
import phonenumbers

def normalize_phone(phone: str, default_country: str = "US") -> Tuple[str, bool]:
    """
    Normalize a phone number to E.164 format.
    If parsing fails, returns the original trimmed string and False.
    """
    if not phone or not isinstance(phone, str):
        return "", False
    
    cleaned = phone.strip()
    try:
        # Check if the number already has '+' prefix or parse with default country
        parsed = phonenumbers.parse(cleaned, default_country)
        if phonenumbers.is_valid_number(parsed):
            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            return formatted, True
    except Exception:
        # Never crash on malformed inputs
        pass

    return cleaned, False

def normalize_phones(phones: List[str], default_country: str = "US") -> Tuple[List[str], List[bool]]:
    """
    Normalize a list of phone numbers. Returns normalized numbers and a list of success statuses.
    Deduplicates phone numbers while preserving order.
    """
    if not phones:
        return [], []
    
    normalized = []
    statuses = []
    seen = set()
    
    for p in phones:
        if not p or not isinstance(p, str):
            continue
        val, success = normalize_phone(p, default_country)
        if val and val not in seen:
            seen.add(val)
            normalized.append(val)
            statuses.append(success)
            
    return normalized, statuses
