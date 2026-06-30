# app/confidence.py

import logging
from typing import List
from app.schemas import CanonicalProfile, ExtractedProfile

logger = logging.getLogger(__name__)

def calculate_overall_confidence(
    canonical: CanonicalProfile,
    sources: List[ExtractedProfile],
    conflict_count: int,
    phone_successes: List[bool],
    date_successes: List[bool]
) -> float:
    """
    Compute a numeric confidence score (0.0 to 1.0) based on:
    - Max source confidence (40% weight)
    - Completeness of candidate fields (40% weight)
    - Normalization success rate (20% weight)
    - Conflict penalty (-0.05 per resolved conflict)
    """
    if not sources:
        return 0.0
        
    # 1. Base Source Confidence (Highest source confidence)
    max_source_conf = max(s.source_confidence for s in sources)
    
    # 2. Field Completeness
    completeness_fields = [
        bool(canonical.full_name),
        bool(canonical.emails),
        bool(canonical.phones),
        bool(canonical.location and (canonical.location.city or canonical.location.country)),
        bool(canonical.links),
        bool(canonical.headline),
        canonical.years_experience is not None,
        bool(canonical.skills),
        bool(canonical.experience),
        bool(canonical.education)
    ]
    completeness = sum(completeness_fields) / len(completeness_fields)
    
    # 3. Normalization Success
    total_normalizations = len(phone_successes) + len(date_successes)
    successful_normalizations = sum(phone_successes) + sum(date_successes)
    
    normalization_rate = 1.0
    if total_normalizations > 0:
        normalization_rate = successful_normalizations / total_normalizations
        
    # 4. Conflict Penalty
    # Deduced from conflicts during merger
    conflict_penalty = 0.05 * conflict_count
    
    # Weight components
    score = (max_source_conf * 0.4) + (completeness * 0.4) + (normalization_rate * 0.2) - conflict_penalty
    
    # Clamp between 0.0 and 1.0
    final_score = max(0.0, min(1.0, score))
    
    logger.info(
        f"Confidence breakdown - Base: {max_source_conf:.2f}, Completeness: {completeness:.2f}, "
        f"Norm Rate: {normalization_rate:.2f}, Penalty: {conflict_penalty:.2f} -> Final: {final_score:.4f}"
    )
    
    return round(final_score, 4)
