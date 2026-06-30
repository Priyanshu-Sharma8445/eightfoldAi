# app/normalizers/links.py

import re
from urllib.parse import urlparse
from typing import List, Union, Dict
from app.schemas import LinkSchema
from app.constants import LINK_CATEGORIES

def normalize_link(url: Union[str, Dict, LinkSchema]) -> LinkSchema:
    """
    Normalize and categorize a single link.
    """
    if not url:
        return LinkSchema(category="other", url="")
        
    cleaned_url = ""
    if isinstance(url, str):
        cleaned_url = url.strip()
    elif isinstance(url, dict):
        cleaned_url = url.get("url", "").strip()
    elif hasattr(url, "url"):
        cleaned_url = getattr(url, "url", "").strip()
        
    if not cleaned_url:
        return LinkSchema(category="other", url="")
        
    # Ensure protocol prefix exists for proper domain parsing
    url_for_parsing = cleaned_url
    if not re.match(r'^https?://', cleaned_url, re.IGNORECASE):
        url_for_parsing = "https://" + cleaned_url
        
    try:
        parsed = urlparse(url_for_parsing)
        domain = parsed.netloc.lower()
    except Exception:
        domain = ""
        
    # Match category based on domain mappings
    category = "other"
    for dom, cat in LINK_CATEGORIES.items():
        if dom in domain:
            category = cat
            break
            
    if category == "other":
        # Heuristic keywords indicating a personal/developer portfolio
        portfolio_keywords = ["portfolio", "blog", "website", "personal", "github.io", "gitlab.io", "bitbucket.io", ".dev", ".me"]
        if any(kw in url_for_parsing.lower() for kw in portfolio_keywords):
            category = "portfolio"
        elif domain and not any(social in domain for social in ["google.com", "facebook.com", "twitter.com", "x.com", "instagram.com", "youtube.com"]):
            # Personal custom domains default to portfolio
            category = "portfolio"
            
    return LinkSchema(category=category, url=cleaned_url)

def normalize_links(links: List[Union[str, Dict, LinkSchema]]) -> List[LinkSchema]:
    """
    Normalize a list of links, removing duplicates by URL.
    """
    if not links:
        return []
        
    normalized = []
    seen = set()
    for l in links:
        norm = normalize_link(l)
        if norm.url and norm.url not in seen:
            seen.add(norm.url)
            normalized.append(norm)
            
    return normalized
