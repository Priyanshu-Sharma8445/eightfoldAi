# app/normalizers/email.py

from typing import List

def normalize_email(email: str) -> str:
    """
    Lowercase, trim spaces of an email.
    """
    if not email:
        return ""
    return email.strip().lower()

def normalize_emails(emails: List[str]) -> List[str]:
    """
    Normalize list of emails: lowercase, trim, and remove duplicates keeping order.
    """
    if not emails:
        return []
    normalized = []
    seen = set()
    for e in emails:
        if not e or not isinstance(e, str):
            continue
        cleaned = normalize_email(e)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            normalized.append(cleaned)
    return normalized
