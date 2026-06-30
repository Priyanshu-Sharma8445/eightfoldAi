# app/normalizers/location.py

from typing import Union, Dict, Optional
from app.schemas import LocationSchema
from app.constants import COUNTRY_MAPPING

def normalize_country(country: Optional[str]) -> Optional[str]:
    """
    Normalize country to ISO-3166 alpha-2 format if recognizable.
    """
    if not country:
        return None
    
    cleaned = country.strip().lower()
    
    # Check constants mapping first (e.g. uk -> GB)
    if cleaned in COUNTRY_MAPPING:
        return COUNTRY_MAPPING[cleaned]
        
    # If already a 2-letter alpha code, return it uppercase
    if len(cleaned) == 2 and cleaned.isalpha():
        return cleaned.upper()
        
    # Standardize capitalized representation if not found in dictionary
    return country.strip().title()

def normalize_location(loc: Union[str, LocationSchema, Dict, None]) -> LocationSchema:
    """
    Normalize location details into a standard LocationSchema with city, region, country.
    Accepts comma-separated strings, dictionaries, or LocationSchema objects.
    """
    if not loc:
        return LocationSchema()
        
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    
    if isinstance(loc, str):
        parts = [p.strip() for p in loc.split(",") if p.strip()]
        if len(parts) == 3:
            city, region, country = parts[0], parts[1], normalize_country(parts[2])
        elif len(parts) == 2:
            # Detect if second part is a country or region
            c_norm = normalize_country(parts[1])
            if c_norm and len(c_norm) == 2 and c_norm.isupper():
                city, country = parts[0], c_norm
            else:
                city, region = parts[0], parts[1]
        elif len(parts) == 1:
            c_norm = normalize_country(parts[0])
            if c_norm and len(c_norm) == 2 and c_norm.isupper():
                country = c_norm
            else:
                city = parts[0]
    elif isinstance(loc, dict):
        city = loc.get("city")
        region = loc.get("region")
        country = normalize_country(loc.get("country"))
    elif hasattr(loc, "city"):  # LocationSchema or similar
        city = getattr(loc, "city", None)
        region = getattr(loc, "region", None)
        country = normalize_country(getattr(loc, "country", None))
        
    return LocationSchema(
        city=city.strip() if city else None,
        region=region.strip() if region else None,
        country=country
    )
