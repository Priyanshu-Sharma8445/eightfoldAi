# app/pipeline/pipeline.py

import os
import logging
from typing import List, Tuple, Dict, Any, Optional
from app.config import RuntimeConfig
from app.schemas import ExtractedProfile, CanonicalProfile
from app.extractors.csv_reader import extract_csv
from app.extractors.resume_txt import extract_resume_txt
from app.normalizers.email import normalize_emails
from app.normalizers.phone import normalize_phones
from app.normalizers.date import normalize_date
from app.normalizers.skill import normalize_skills
from app.normalizers.location import normalize_location
from app.normalizers.links import normalize_links
from app.merger import merge_profiles
from app.confidence import calculate_overall_confidence
from app.projection import project_profile
from app.validator import validate_projected_json

logger = logging.getLogger(__name__)

def detect_source_type(filename: str) -> str:
    """
    Detect the type of input source based on file extension.
    Defaults to 'resume' (text) if unrecognizable.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.csv':
        return 'csv'
    return 'resume'

def extract_source(file_content: str, filename: str) -> ExtractedProfile:
    """
    Detect source type and parse content.
    Never crashes; returns empty/partial profile on errors.
    """
    source_type = detect_source_type(filename)
    if source_type == 'csv':
        logger.info(f"Extracting structured CSV data from: {filename}")
        return extract_csv(file_content, filename)
    else:
        logger.info(f"Extracting unstructured Resume TXT data from: {filename}")
        return extract_resume_txt(file_content, filename)

def normalize_profile(profile: ExtractedProfile) -> Tuple[ExtractedProfile, List[bool], List[bool]]:
    """
    Normalize all fields in an ExtractedProfile.
    Returns the normalized profile, phone normalization success list, and date normalization success list.
    """
    # 1. Email Normalization
    profile.emails = normalize_emails(profile.emails)
    
    # 2. Phone Normalization
    normalized_phones, phone_statuses = normalize_phones(profile.phones)
    profile.phones = normalized_phones
    
    # 3. Location Normalization
    if profile.location:
        profile.location = normalize_location(profile.location)
        
    # 4. Links Normalization
    profile.links = normalize_links(profile.links)
    
    # 5. Skill Normalization
    profile.skills = normalize_skills(profile.skills)
    
    # 6. Dates in Experience & Education Normalization
    date_statuses = []
    
    # Experience dates
    for exp in profile.experience:
        if exp.start_date:
            norm_start = normalize_date(exp.start_date)
            # If date was present but normalized to None, it's a normalization failure
            date_statuses.append(norm_start is not None)
            exp.start_date = norm_start
            
        if exp.end_date:
            # Handle standard "Present" representation cleanly
            if exp.end_date.strip().lower() in ["present", "current"]:
                date_statuses.append(True)
            else:
                norm_end = normalize_date(exp.end_date)
                date_statuses.append(norm_end is not None)
                exp.end_date = norm_end
                
    # Education dates
    for edu in profile.education:
        if edu.start_date:
            norm_start = normalize_date(edu.start_date)
            date_statuses.append(norm_start is not None)
            edu.start_date = norm_start
            
        if edu.end_date:
            norm_end = normalize_date(edu.end_date)
            date_statuses.append(norm_end is not None)
            edu.end_date = norm_end
            
    return profile, phone_statuses, date_statuses

def run_pipeline(
    sources_data: List[Tuple[str, str]],  # List of (filename, file_content)
    config: RuntimeConfig
) -> Dict[str, Any]:
    """
    Execute the full Multi-Source Candidate Data Transformer pipeline:
    Detect Source -> Extract -> Normalize -> Merge -> Confidence -> Projection -> Validation.
    """
    logger.info("Executing candidate transformation pipeline.")
    
    extracted_profiles: List[ExtractedProfile] = []
    all_phone_statuses: List[bool] = []
    all_date_statuses: List[bool] = []
    
    # Step 1 & 2: Extract
    for filename, content in sources_data:
        profile = extract_source(content, filename)
        
        # Step 3: Normalize
        norm_profile, phone_stats, date_stats = normalize_profile(profile)
        extracted_profiles.append(norm_profile)
        
        all_phone_statuses.extend(phone_stats)
        all_date_statuses.extend(date_stats)
        
    # Step 4: Merge
    canonical_profile, conflict_count = merge_profiles(extracted_profiles)
    
    # Step 5: Confidence Calculation
    overall_conf = calculate_overall_confidence(
        canonical_profile,
        extracted_profiles,
        conflict_count,
        all_phone_statuses,
        all_date_statuses
    )
    canonical_profile.overall_confidence = overall_conf
    
    # Step 6: Projection
    projected_json = project_profile(canonical_profile, config)
    
    # Step 7: Validation
    validate_projected_json(projected_json, config)
    
    logger.info("Pipeline executed successfully.")
    return projected_json
