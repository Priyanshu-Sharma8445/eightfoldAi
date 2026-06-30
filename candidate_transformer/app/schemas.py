# app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional

class LocationSchema(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

class LinkSchema(BaseModel):
    category: str  # "github", "linkedin", "portfolio", "other"
    url: str

class ExperienceSchema(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class EducationSchema(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ProvenanceSchema(BaseModel):
    field: str
    source: str
    method: str  # "extracted", "parsed", "normalized", etc.

# Raw Profile Extracted from a Single Source
class ExtractedProfile(BaseModel):
    source_name: str
    source_confidence: float
    full_name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    location: Optional[LocationSchema] = None
    links: List[LinkSchema] = Field(default_factory=list)
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceSchema] = Field(default_factory=list)
    education: List[EducationSchema] = Field(default_factory=list)

# Canonical/Merged Candidate Profile
class CanonicalProfile(BaseModel):
    candidate_id: str
    full_name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    location: Optional[LocationSchema] = None
    links: List[LinkSchema] = Field(default_factory=list)
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceSchema] = Field(default_factory=list)
    education: List[EducationSchema] = Field(default_factory=list)
    provenance: List[ProvenanceSchema] = Field(default_factory=list)
    overall_confidence: float = 1.0
