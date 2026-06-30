# app/provenance.py

from typing import List
from app.schemas import ProvenanceSchema

def create_provenance(field: str, source: str, method: str) -> ProvenanceSchema:
    """
    Helper to generate a ProvenanceSchema instance.
    """
    return ProvenanceSchema(
        field=field,
        source=source,
        method=method
    )

def merge_provenance_lists(prov1: List[ProvenanceSchema], prov2: List[ProvenanceSchema]) -> List[ProvenanceSchema]:
    """
    Merge two lists of provenance records, removing exact duplicates.
    """
    seen = set()
    merged = []
    for p in prov1 + prov2:
        key = (p.field, p.source, p.method)
        if key not in seen:
            seen.add(key)
            merged.append(p)
    return merged
