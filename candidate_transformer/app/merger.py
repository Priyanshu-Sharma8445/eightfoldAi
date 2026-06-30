# app/merger.py

import hashlib
from typing import List, Tuple, Dict, Any, Optional
from app.schemas import CanonicalProfile, ExtractedProfile, LocationSchema, LinkSchema, ExperienceSchema, EducationSchema, ProvenanceSchema
from app.provenance import create_provenance, merge_provenance_lists

def generate_deterministic_id(emails: List[str], full_name: Optional[str]) -> str:
    """
    Generate a deterministic candidate_id using a hash of the primary email or name.
    """
    if emails:
        base = emails[0].lower().strip()
    elif full_name:
        base = full_name.lower().strip()
    else:
        base = "unknown_candidate"
        
    sha = hashlib.sha256(base.encode('utf-8')).hexdigest()
    return f"cand_{sha[:12]}"

def resolve_scalar_conflict(
    val1: Any, conf1: float, src1: str,
    val2: Any, conf2: float, src2: str,
    field_name: str
) -> Tuple[Any, float, str, bool]:
    """
    Compare two values. Returns (selected_value, selected_confidence, selected_source, conflict_occurred).
    """
    if val1 is None or val1 == "":
        return val2, conf2, src2, False
    if val2 is None or val2 == "":
        return val1, conf1, src1, False
        
    if val1 == val2:
        return val1, conf1, src1, False
        
    # Different values: conflict occurred
    conflict = True
    if conf1 > conf2:
        return val1, conf1, src1, conflict
    elif conf2 > conf1:
        return val2, conf2, src2, conflict
    else:
        # Equal confidence: deterministic rules
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            # Pick the larger number (e.g. years_experience)
            if val1 >= val2:
                return val1, conf1, src1, conflict
            return val2, conf2, src2, conflict
        else:
            # Pick longest string representation
            str1, str2 = str(val1), str(val2)
            if len(str1) >= len(str2):
                return val1, conf1, src1, conflict
            return val2, conf2, src2, conflict

def merge_profiles(profiles: List[ExtractedProfile]) -> Tuple[CanonicalProfile, int]:
    """
    Merge multiple extracted source profiles into one canonical profile.
    Returns the CanonicalProfile and the count of resolved conflicts.
    """
    if not profiles:
        return CanonicalProfile(candidate_id="cand_empty"), 0

    # Sort profiles by confidence descending, then by source name ascending
    sorted_profiles = sorted(profiles, key=lambda p: (p.source_confidence, p.source_name), reverse=True)
    
    # Initialize canonical candidate field states
    full_name: Optional[str] = None
    fn_conf, fn_src = 0.0, ""
    
    headline: Optional[str] = None
    hl_conf, hl_src = 0.0, ""
    
    years_exp: Optional[float] = None
    ye_conf, ye_src = 0.0, ""
    
    # Location components
    city: Optional[str] = None
    city_conf, city_src = 0.0, ""
    region: Optional[str] = None
    region_conf, region_src = 0.0, ""
    country: Optional[str] = None
    country_conf, country_src = 0.0, ""
    
    # List aggregations
    emails_list: List[str] = []
    phones_list: List[str] = []
    skills_list: List[str] = []
    links_list: List[LinkSchema] = []
    experience_list: List[ExperienceSchema] = []
    education_list: List[EducationSchema] = []
    
    provenance_records: List[ProvenanceSchema] = []
    conflict_count = 0

    for prof in sorted_profiles:
        src = prof.source_name
        conf = prof.source_confidence
        
        # 1. Full name
        if prof.full_name:
            val, selected_conf, selected_src, is_conflict = resolve_scalar_conflict(
                full_name, fn_conf, fn_src,
                prof.full_name, conf, src, "full_name"
            )
            full_name = val
            fn_conf, fn_src = selected_conf, selected_src
            if is_conflict:
                conflict_count += 1
                
        # 2. Headline
        if prof.headline:
            val, selected_conf, selected_src, is_conflict = resolve_scalar_conflict(
                headline, hl_conf, hl_src,
                prof.headline, conf, src, "headline"
            )
            headline = val
            hl_conf, hl_src = selected_conf, selected_src
            if is_conflict:
                conflict_count += 1
                
        # 3. Years Experience
        if prof.years_experience is not None:
            val, selected_conf, selected_src, is_conflict = resolve_scalar_conflict(
                years_exp, ye_conf, ye_src,
                prof.years_experience, conf, src, "years_experience"
            )
            years_exp = val
            ye_conf, ye_src = selected_conf, selected_src
            if is_conflict:
                conflict_count += 1
                
        # 4. Location Sub-fields
        if prof.location:
            if prof.location.city:
                val, selected_conf, selected_src, is_conflict = resolve_scalar_conflict(
                    city, city_conf, city_src,
                    prof.location.city, conf, src, "location.city"
                )
                city = val
                city_conf, city_src = selected_conf, selected_src
                if is_conflict:
                    conflict_count += 1
                    
            if prof.location.region:
                val, selected_conf, selected_src, is_conflict = resolve_scalar_conflict(
                    region, region_conf, region_src,
                    prof.location.region, conf, src, "location.region"
                )
                region = val
                region_conf, region_src = selected_conf, selected_src
                if is_conflict:
                    conflict_count += 1
                    
            if prof.location.country:
                val, selected_conf, selected_src, is_conflict = resolve_scalar_conflict(
                    country, country_conf, country_src,
                    prof.location.country, conf, src, "location.country"
                )
                country = val
                country_conf, country_src = selected_conf, selected_src
                if is_conflict:
                    conflict_count += 1

        # 5. List items (Union with ordering)
        # Emails
        for email in prof.emails:
            if email not in emails_list:
                emails_list.append(email)
                provenance_records.append(create_provenance("emails", src, "extracted"))
                
        # Phones
        for phone in prof.phones:
            if phone not in phones_list:
                phones_list.append(phone)
                provenance_records.append(create_provenance("phones", src, "extracted"))
                
        # Skills
        for skill in prof.skills:
            if skill not in skills_list:
                skills_list.append(skill)
                provenance_records.append(create_provenance("skills", src, "extracted"))
                
        # Links
        for link in prof.links:
            # deduplicate by URL
            if not any(l.url == link.url for l in links_list):
                links_list.append(link)
                provenance_records.append(create_provenance("links", src, "extracted"))
                
        # Experience (deduplicate by company and job title)
        for exp in prof.experience:
            matched = False
            for existing in experience_list:
                # If same company and job title, choose the one with higher confidence/fuller description
                if existing.company and exp.company and existing.company.lower() == exp.company.lower() and \
                   existing.job_title and exp.job_title and existing.job_title.lower() == exp.job_title.lower():
                    matched = True
                    # If existing description is shorter or start_date is missing, merge/replace
                    if not existing.start_date and exp.start_date:
                        existing.start_date = exp.start_date
                    if not existing.end_date and exp.end_date:
                        existing.end_date = exp.end_date
                    if (existing.description or "") < (exp.description or ""):
                        existing.description = exp.description
                    break
            if not matched:
                experience_list.append(exp)
                provenance_records.append(create_provenance("experience", src, "extracted"))
                
        # Education (deduplicate by institution and degree)
        for edu in prof.education:
            matched = False
            for existing in education_list:
                if existing.institution and edu.institution and existing.institution.lower() == edu.institution.lower() and \
                   (existing.degree or "").lower() == (edu.degree or "").lower():
                    matched = True
                    if not existing.start_date and edu.start_date:
                        existing.start_date = edu.start_date
                    if not existing.end_date and edu.end_date:
                        existing.end_date = edu.end_date
                    break
            if not matched:
                education_list.append(edu)
                provenance_records.append(create_provenance("education", src, "extracted"))

    # Add scalar provenances
    if full_name:
        provenance_records.append(create_provenance("full_name", fn_src, "extracted"))
    if headline:
        provenance_records.append(create_provenance("headline", hl_src, "extracted"))
    if years_exp is not None:
        provenance_records.append(create_provenance("years_experience", ye_src, "extracted"))
    if city:
        provenance_records.append(create_provenance("location.city", city_src, "extracted"))
    if region:
        provenance_records.append(create_provenance("location.region", region_src, "extracted"))
    if country:
        provenance_records.append(create_provenance("location.country", country_src, "extracted"))

    # Construct overall LocationSchema
    location_schema = LocationSchema(city=city, region=region, country=country) if (city or region or country) else None

    # Deterministic candidate ID
    candidate_id = generate_deterministic_id(emails_list, full_name)

    canonical = CanonicalProfile(
        candidate_id=candidate_id,
        full_name=full_name,
        emails=emails_list,
        phones=phones_list,
        location=location_schema,
        links=links_list,
        headline=headline,
        years_experience=years_exp,
        skills=skills_list,
        experience=experience_list,
        education=education_list,
        provenance=provenance_records,
        overall_confidence=1.0  # Computed in next step
    )

    return canonical, conflict_count
