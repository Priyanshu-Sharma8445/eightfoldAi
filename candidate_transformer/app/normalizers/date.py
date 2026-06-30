# app/normalizers/date.py

import re
from typing import Optional

MONTH_MAP = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12"
}

def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """
    Normalize date strings into YYYY-MM.
    If month unavailable, use YYYY.
    If impossible, return None.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    cleaned = date_str.strip().lower()
    
    # 1. YYYY-MM-DD or YYYY-MM (e.g., 2023-05-12 or 2023-05)
    match1 = re.search(r'\b(\d{4})[-/](\d{1,2})\b', cleaned)
    if match1:
        year, month = match1.group(1), int(match1.group(2))
        if 1 <= month <= 12:
            return f"{year}-{month:02d}"
            
    # 2. MM/YYYY or MM-YYYY (e.g., 05/2023 or 5-2023)
    match2 = re.search(r'\b(\d{1,2})[-/](\d{4})\b', cleaned)
    if match2:
        month, year = int(match2.group(1)), match2.group(2)
        if 1 <= month <= 12:
            return f"{year}-{month:02d}"
            
    # 3. Month Name + Year (e.g., "Jan 2023", "January, 2023")
    months_pattern = '|'.join(MONTH_MAP.keys())
    match3 = re.search(rf'\b({months_pattern})\w*\b\s*,?\s*\b(\d{{4}})\b', cleaned)
    if match3:
        month_name, year = match3.group(1), match3.group(2)
        return f"{year}-{MONTH_MAP[month_name]}"
        
    # 3b. Year + Month Name (e.g., "2023 Jan")
    match3_rev = re.search(rf'\b(\d{{4}})\b\s*,?\s*\b({months_pattern})\w*\b', cleaned)
    if match3_rev:
        year, month_name = match3_rev.group(1), match3_rev.group(2)
        return f"{year}-{MONTH_MAP[month_name]}"

    # 4. YYYY only (e.g., 2023)
    match4 = re.search(r'\b(\d{4})\b', cleaned)
    if match4:
        year = int(match4.group(1))
        if 1900 <= year <= 2100:
            return str(year)
            
    return None
