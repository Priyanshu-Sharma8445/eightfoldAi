# app/extractors/csv_reader.py

import csv
import io
import json
import logging
from typing import Optional, List, Dict, Any
from app.schemas import ExtractedProfile, LocationSchema, LinkSchema, ExperienceSchema, EducationSchema
from app.constants import DEFAULT_SOURCE_CONFIDENCE

logger = logging.getLogger(__name__)

def extract_csv(file_content: str, filename: str = "sample.csv") -> ExtractedProfile:
    """
    Extract candidate profile details from a CSV file content.
    Returns an ExtractedProfile. Never crashes on bad/malformed inputs.
    """
    profile = ExtractedProfile(
        source_name=filename,
        source_confidence=DEFAULT_SOURCE_CONFIDENCE.get("csv", 0.95)
    )
    
    if not file_content or not file_content.strip():
        logger.warning(f"Empty content received for source: {filename}")
        return profile
        
    try:
        f = io.StringIO(file_content.strip())
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            logger.warning(f"CSV file has no headers: {filename}")
            return profile
            
        rows = list(reader)
        if not rows:
            logger.warning(f"CSV file contains no rows: {filename}")
            return profile
            
        # Parse the first row representing the candidate
        row = rows[0]
        
        # Lowercase keys and strip spaces for case-insensitive matching
        row_lower = {k.strip().lower(): v for k, v in row.items() if k}
        
        def get_value(keys: List[str]) -> Optional[str]:
            for k in keys:
                if k.lower() in row_lower:
                    val = row_lower[k.lower()]
                    return val.strip() if val else None
            return None

        # 1. Full name
        first_name = get_value(["first_name", "first name", "fname"])
        last_name = get_value(["last_name", "last name", "lname"])
        full_name = get_value(["full_name", "name", "candidate_name", "candidate name"])
        if full_name:
            profile.full_name = full_name
        elif first_name or last_name:
            profile.full_name = f"{first_name or ''} {last_name or ''}".strip()
            
        # 2. Emails
        emails_str = get_value(["emails", "email", "email_address", "email address"])
        if emails_str:
            profile.emails = [e.strip() for e in emails_str.replace(";", ",").split(",") if e.strip()]
            
        # 3. Phones
        phones_str = get_value(["phones", "phone", "phone_number", "phone number", "mobile", "telephone"])
        if phones_str:
            profile.phones = [p.strip() for p in phones_str.replace(";", ",").split(",") if p.strip()]
            
        # 4. Location
        city = get_value(["city", "town"])
        region = get_value(["region", "state", "province"])
        country = get_value(["country", "nation"])
        loc_str = get_value(["location", "address"])
        
        if city or region or country:
            profile.location = LocationSchema(city=city, region=region, country=country)
        elif loc_str:
            parts = [p.strip() for p in loc_str.split(",") if p.strip()]
            if len(parts) == 3:
                profile.location = LocationSchema(city=parts[0], region=parts[1], country=parts[2])
            elif len(parts) == 2:
                profile.location = LocationSchema(city=parts[0], country=parts[1])
            else:
                profile.location = LocationSchema(city=loc_str)
                
        # 5. Links
        linkedin = get_value(["linkedin", "linkedin_url", "linkedin url"])
        github = get_value(["github", "github_url", "github url"])
        portfolio = get_value(["portfolio", "portfolio_url", "portfolio url", "website"])
        links_str = get_value(["links", "urls"])
        
        links_list = []
        if linkedin:
            links_list.append(LinkSchema(category="linkedin", url=linkedin))
        if github:
            links_list.append(LinkSchema(category="github", url=github))
        if portfolio:
            links_list.append(LinkSchema(category="portfolio", url=portfolio))
        if links_str:
            for l in links_str.replace(";", ",").split(","):
                if l.strip():
                    links_list.append(LinkSchema(category="other", url=l.strip()))
        profile.links = links_list
        
        # 6. Headline
        profile.headline = get_value(["headline", "title", "job_title", "summary", "professional summary"])
        
        # 7. Years of experience
        y_exp = get_value(["years_experience", "years_exp", "experience_years", "experience"])
        if y_exp:
            try:
                digits = "".join([c for c in y_exp if c.isdigit() or c == "."])
                profile.years_experience = float(digits) if digits else None
            except Exception:
                pass
                
        # 8. Skills
        skills_str = get_value(["skills", "skills_list", "keywords", "technologies"])
        if skills_str:
            profile.skills = [s.strip() for s in skills_str.replace(";", ",").split(",") if s.strip()]
            
        # 9. Experience JSON or text
        exp_val = get_value(["experience_list", "experience_detail", "experience"])
        if exp_val:
            try:
                parsed_exp = json.loads(exp_val)
                if isinstance(parsed_exp, list):
                    profile.experience = [
                        ExperienceSchema(
                            job_title=item.get("job_title"),
                            company=item.get("company"),
                            start_date=item.get("start_date"),
                            end_date=item.get("end_date"),
                            description=item.get("description")
                        )
                        for item in parsed_exp if isinstance(item, dict)
                    ]
            except Exception:
                profile.experience = [ExperienceSchema(description=exp_val)]
                
        # 10. Education JSON or text
        edu_val = get_value(["education_list", "education_detail", "education"])
        if edu_val:
            try:
                parsed_edu = json.loads(edu_val)
                if isinstance(parsed_edu, list):
                    profile.education = [
                        EducationSchema(
                            institution=item.get("institution"),
                            degree=item.get("degree"),
                            major=item.get("major"),
                            start_date=item.get("start_date"),
                            end_date=item.get("end_date")
                        )
                        for item in parsed_edu if isinstance(item, dict)
                    ]
            except Exception:
                profile.education = [EducationSchema(institution=edu_val)]
                
    except Exception as e:
        logger.error(f"Error reading CSV content: {str(e)}", exc_info=True)
        # return empty/partial profile instead of crashing
        
    return profile
