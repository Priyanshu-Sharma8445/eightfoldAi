# app/extractors/resume_txt.py

import re
import logging
from typing import List, Optional
from app.schemas import ExtractedProfile, LocationSchema, LinkSchema, ExperienceSchema, EducationSchema
from app.constants import DEFAULT_SOURCE_CONFIDENCE

logger = logging.getLogger(__name__)

def extract_resume_txt(file_content: str, filename: str = "resume.txt") -> ExtractedProfile:
    """
    Extract candidate profile details from an unstructured Resume TXT file.
    Returns an ExtractedProfile. Never crashes on bad/malformed inputs.
    """
    profile = ExtractedProfile(
        source_name=filename,
        source_confidence=DEFAULT_SOURCE_CONFIDENCE.get("resume", 0.85)
    )
    
    if not file_content or not file_content.strip():
        logger.warning(f"Empty content received for source: {filename}")
        return profile
        
    lines = [line.strip() for line in file_content.splitlines()]
    non_empty_lines = [line for line in lines if line]
    
    # 1. Emails Extraction
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    emails = re.findall(email_regex, file_content)
    seen_emails = set()
    profile.emails = [e.strip() for e in emails if not (e.strip() in seen_emails or seen_emails.add(e.strip()))]

    # 2. Phones Extraction
    phone_regex = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_regex, file_content)
    seen_phones = set()
    profile.phones = [p.strip() for p in phones if not (p.strip() in seen_phones or seen_phones.add(p.strip()))]

    # 3. Links Extraction
    link_regex = r'https?://[^\s,]+|www\.[^\s,]+'
    links = re.findall(link_regex, file_content)
    seen_links = set()
    link_schemas = []
    for url in links:
        cleaned_url = url.strip().rstrip(".").rstrip(",")
        if cleaned_url and cleaned_url not in seen_links:
            seen_links.add(cleaned_url)
            category = "other"
            if "linkedin.com" in cleaned_url:
                category = "linkedin"
            elif "github.com" in cleaned_url:
                category = "github"
            link_schemas.append(LinkSchema(category=category, url=cleaned_url))
    profile.links = link_schemas

    # 4. Full Name Extraction
    # Heuristic: the first short, non-header line that has 2-4 words, with no digits, emails, or links
    name_found = False
    for line in non_empty_lines[:6]:
        words = line.split()
        if (
            not re.search(email_regex, line) and
            not re.search(link_regex, line) and
            not re.search(phone_regex, line) and
            not any(kw in line.lower() for kw in ["resume", "cv", "curriculum", "contact", "email", "phone", "profile", "summary", "skills", "experience", "education"])
            and len(words) >= 2
            and len(words) <= 4
            and not any(char.isdigit() for char in line)
        ):
            profile.full_name = line
            name_found = True
            break
            
    if not name_found and non_empty_lines:
        profile.full_name = non_empty_lines[0][:100]

    # 5. Segment into Sections
    sections = {}
    current_section = "header"
    sections[current_section] = []
    
    section_headers = {
        "skills": ["skills", "technical skills", "technologies", "core competencies", "expertise", "proficiencies", "skills summary"],
        "experience": ["experience", "work experience", "professional experience", "employment history", "employment", "work history", "history"],
        "education": ["education", "academic background", "degrees", "academic qualifications", "credentials"],
        "summary": ["summary", "professional summary", "headline", "about me", "profile", "objective"]
    }
    
    for line in lines:
        cleaned_line = line.lower().strip(":").strip()
        matched_section = None
        for sec_name, keywords in section_headers.items():
            if cleaned_line in keywords or any(cleaned_line == kw for kw in keywords):
                matched_section = sec_name
                break
                
        if matched_section:
            current_section = matched_section
            sections[current_section] = []
        else:
            sections[current_section].append(line)

    # 6. Headline / Summary
    candidate_headline = None
    try:
        name_idx = non_empty_lines.index(profile.full_name)
        if len(non_empty_lines) > name_idx + 1:
            potential_headline = non_empty_lines[name_idx + 1]
            if (
                not re.search(email_regex, potential_headline) and
                not re.search(phone_regex, potential_headline) and
                len(potential_headline.split()) > 1 and
                len(potential_headline.split()) < 10 and
                not any(kw in potential_headline.lower() for kw in ["resume", "cv", "contact", "email", "phone"])
            ):
                candidate_headline = potential_headline
    except Exception:
        pass

    summary_lines = sections.get("summary", [])
    cleaned_summary = [l.strip() for l in summary_lines if l.strip()]

    if candidate_headline:
        profile.headline = candidate_headline
    elif cleaned_summary:
        profile.headline = " ".join(cleaned_summary)[:250]

    # 7. Years of Experience Extraction
    y_exp_regex = r'\b(\d+(?:\.\d+)?)\+?\s*(?:yrs|years?)\b'
    experience_matches = re.findall(y_exp_regex, file_content, re.IGNORECASE)
    if experience_matches:
        try:
            profile.years_experience = float(experience_matches[0])
        except Exception:
            pass

    # 8. Skills Extraction
    skill_lines = sections.get("skills", [])
    skills_list = []
    for line in skill_lines:
        if not line or not line.strip():
            continue
        cleaned_line = line.replace("•", "").replace("-", "").strip()
        if not cleaned_line:
            continue
        # Split on comma if present, otherwise treat line as skill
        parts = [p.strip() for p in cleaned_line.split(",") if p.strip()]
        if len(parts) > 1:
            skills_list.extend(parts)
        else:
            skills_list.append(cleaned_line)
    profile.skills = skills_list

    # 9. Location Extraction
    # Search the header lines for "City, State" or "City, Country"
    loc_found = False
    for line in sections.get("header", []) + sections.get("summary", []):
        match_loc = re.search(r'\b([A-Za-z\s]{3,20}),\s*([A-Za-z\s]{2,20})\b', line)
        if match_loc and not re.search(email_regex, line) and not re.search(phone_regex, line) and "resume" not in line.lower():
            city, region = match_loc.group(1).strip(), match_loc.group(2).strip()
            profile.location = LocationSchema(city=city, region=region)
            loc_found = True
            break

    # 10. Experience Parsing
    exp_lines = sections.get("experience", [])
    experience_items = []
    current_item = None
    
    date_pattern = r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}|\b\d{4}|\b\d{1,2}/\d{4}'
    date_range_pattern = rf'({date_pattern})\s*(?:-|to)\s*({date_pattern}|present|current)'
    
    recent_lines = []
    for line in exp_lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
        
        date_match = re.search(date_range_pattern, cleaned_line, re.IGNORECASE)
        if date_match:
            if current_item:
                experience_items.append(current_item)
                
            start_date, end_date = date_match.group(1).strip(), date_match.group(2).strip()
            line_no_dates = re.sub(date_range_pattern, "", cleaned_line, flags=re.IGNORECASE).strip(" |(),-")
            
            job_title = None
            company = None
            title_company_line = ""
            
            if len(line_no_dates.split()) >= 2:
                # Job title and company on same line
                title_company_line = line_no_dates
            elif recent_lines:
                # Job title and company on line above
                title_company_line = recent_lines.pop()
                
            if title_company_line:
                if " at " in title_company_line.lower():
                    parts = re.split(r'\s+at\s+', title_company_line, flags=re.IGNORECASE)
                    job_title, company = parts[0].strip(), parts[1].strip()
                elif " - " in title_company_line:
                    parts = title_company_line.split(" - ")
                    job_title, company = parts[0].strip(), parts[1].strip()
                elif " | " in title_company_line:
                    parts = title_company_line.split(" | ")
                    job_title, company = parts[0].strip(), parts[1].strip()
                else:
                    job_title = title_company_line
            else:
                job_title = "Position"
                
            current_item = ExperienceSchema(
                job_title=job_title,
                company=company,
                start_date=start_date,
                end_date=end_date,
                description=""
            )
            recent_lines = []
        else:
            if current_item:
                desc_line = cleaned_line.strip(" •-*")
                if desc_line:
                    if current_item.description:
                        current_item.description += "\n" + desc_line
                    else:
                        current_item.description = desc_line
            else:
                recent_lines.append(cleaned_line)
                
    if current_item:
        experience_items.append(current_item)
    profile.experience = experience_items

    # 11. Education Parsing
    edu_lines = sections.get("education", [])
    education_items = []
    current_edu = None
    
    edu_inst_keywords = ["university", "college", "school", "institute", "polytechnic"]
    degree_keywords = ["b.s.", "b.a.", "m.s.", "ph.d.", "bachelor", "master", "doctor", "phd", "btech", "mtech", "b.tech", "m.tech", "bsc", "msc"]
    
    for line in edu_lines:
        if not line.strip():
            continue
            
        has_inst = any(kw in line.lower() for kw in edu_inst_keywords)
        has_degree = any(kw in line.lower() for kw in degree_keywords)
        edu_date_matches = re.findall(r'\b\d{4}\b', line)
        
        if has_inst:
            if current_edu:
                education_items.append(current_edu)
                
            parts = [p.strip() for p in line.split(",") if p.strip()]
            inst = parts[0]
            degree = parts[1] if len(parts) > 1 else None
            
            start_date, end_date = None, None
            if len(edu_date_matches) >= 2:
                start_date, end_date = edu_date_matches[0], edu_date_matches[1]
            elif len(edu_date_matches) == 1:
                end_date = edu_date_matches[0]
                
            current_edu = EducationSchema(
                institution=inst,
                degree=degree,
                start_date=start_date,
                end_date=end_date
            )
        elif has_degree and current_edu:
            current_edu.degree = line.strip()
        else:
            if current_edu:
                if len(edu_date_matches) >= 2:
                    current_edu.start_date, current_edu.end_date = edu_date_matches[0], edu_date_matches[1]
                elif len(edu_date_matches) == 1:
                    current_edu.end_date = edu_date_matches[0]
                    
    if current_edu:
        education_items.append(current_edu)
    profile.education = education_items

    return profile
