# tests/test_pipeline.py

import pytest
from app.schemas import ExtractedProfile, LocationSchema, LinkSchema, ExperienceSchema
from app.merger import merge_profiles
from app.pipeline.pipeline import run_pipeline
from app.config import RuntimeConfig, FieldConfig
from app.projection import project_profile
from app.validator import validate_projected_json

def test_conflict_resolution_and_merging():
    # Source 1: CSV (Higher confidence)
    p1 = ExtractedProfile(
        source_name="source1.csv",
        source_confidence=0.95,
        full_name="Jane Doe",
        emails=["jane.doe@example.com"],
        phones=["+14155552671"],
        location=LocationSchema(city="Seattle", country="US"),
        years_experience=8.5,
        skills=["Python", "React"]
    )
    
    # Source 2: Resume (Lower confidence, but has different name, headline, years_experience)
    p2 = ExtractedProfile(
        source_name="source2.txt",
        source_confidence=0.85,
        full_name="Jane S. Doe",
        emails=["jane.doe@example.com", "alternative@example.com"],
        phones=["+14155552671"],
        location=LocationSchema(region="WA", country="US"),
        headline="Senior Systems Architect",
        years_experience=9.0,
        skills=["Python", "Docker"]
    )

    merged, conflicts = merge_profiles([p1, p2])
    
    # 1. Names conflict: pick source1 because 0.95 > 0.85
    assert merged.full_name == "Jane Doe"
    
    # 2. Years experience conflict: pick source1 because 0.95 > 0.85
    assert merged.years_experience == 8.5
    
    # 3. Location sub-fields: merged city from source1 and region from source2
    assert merged.location.city == "Seattle"
    assert merged.location.region == "WA"
    assert merged.location.country == "US"
    
    # 4. List fields: merged and deduplicated
    assert merged.emails == ["jane.doe@example.com", "alternative@example.com"]
    assert merged.skills == ["Python", "React", "Docker"]
    
    # 5. Headline: taken from source2 since source1 was empty (no conflict)
    assert merged.headline == "Senior Systems Architect"

def test_equal_confidence_conflict_resolution():
    # Two sources with equal confidence
    p1 = ExtractedProfile(
        source_name="src1.csv",
        source_confidence=0.90,
        full_name="ShortName",
        years_experience=5.0
    )
    p2 = ExtractedProfile(
        source_name="src2.csv",
        source_confidence=0.90,
        full_name="VeryLongCandidateName",
        years_experience=10.0
    )
    
    merged, conflicts = merge_profiles([p1, p2])
    # For names (strings), picks longest string
    assert merged.full_name == "VeryLongCandidateName"
    # For years_experience (numeric), picks maximum
    assert merged.years_experience == 10.0

def test_projection_custom_config():
    # Setup canonical profile
    p1 = ExtractedProfile(
        source_name="src.csv",
        source_confidence=0.95,
        full_name="John Doe",
        emails=["john.doe@example.com", "work@example.com"],
        phones=["+12065551212"],
        location=LocationSchema(city="Seattle", country="US"),
        skills=["Python"]
    )
    canonical, _ = merge_profiles([p1])
    canonical.overall_confidence = 0.92

    # Custom configuration
    config = RuntimeConfig(
        fields=[
            FieldConfig(path="id", from_field="candidate_id", type="string", required=True),
            FieldConfig(path="name", from_field="full_name", type="string", required=True),
            FieldConfig(path="primary_email", from_field="emails[0]", type="string"),
            FieldConfig(path="city", from_field="location.city", type="string"),
            FieldConfig(path="skills_list", from_field="skills", type="list")
        ],
        include_confidence=True,
        include_provenance=False,
        on_missing="null"
    )

    projected = project_profile(canonical, config)
    
    assert "id" in projected
    assert projected["name"] == "John Doe"
    assert projected["primary_email"] == "john.doe@example.com"
    assert projected["city"] == "Seattle"
    assert projected["skills_list"] == ["Python"]
    assert "overall_confidence" in projected
    assert projected["overall_confidence"] == 0.92
    assert "provenance" not in projected

def test_projection_missing_values_omit():
    p1 = ExtractedProfile(
        source_name="src.csv",
        source_confidence=0.95,
        full_name="John Doe",
        emails=[]
    )
    canonical, _ = merge_profiles([p1])
    
    config = RuntimeConfig(
        fields=[
            FieldConfig(path="name", from_field="full_name", type="string", required=True),
            FieldConfig(path="phone", from_field="phones[0]", type="string", required=False)
        ],
        include_confidence=False,
        include_provenance=False,
        on_missing="omit"
    )
    
    projected = project_profile(canonical, config)
    assert "name" in projected
    assert "phone" not in projected  # Omitted because on_missing is "omit"

def test_projection_missing_values_error():
    p1 = ExtractedProfile(
        source_name="src.csv",
        source_confidence=0.95,
        full_name="John Doe"
    )
    canonical, _ = merge_profiles([p1])
    
    config = RuntimeConfig(
        fields=[
            FieldConfig(path="phone", from_field="phones[0]", type="string", required=True)
        ],
        on_missing="error"
    )
    
    with pytest.raises(ValueError):
        project_profile(canonical, config)

def test_validation():
    # Valid default schema
    data = {
        "candidate_id": "cand_12345",
        "full_name": "Jane Doe",
        "emails": ["jane@example.com"],
        "phones": ["+14155552671"],
        "location": {"city": "Seattle", "region": "WA", "country": "US"},
        "links": [],
        "skills": [],
        "experience": [],
        "education": []
    }
    config = RuntimeConfig()  # Default
    assert validate_projected_json(data, config) is True
    
    # Missing required candidate_id
    invalid_data = data.copy()
    invalid_data.pop("candidate_id")
    with pytest.raises(ValueError):
        validate_projected_json(invalid_data, config)
        
    # Bad type for emails (expected list)
    invalid_type_data = data.copy()
    invalid_type_data["emails"] = "not-a-list"
    with pytest.raises(TypeError):
        validate_projected_json(invalid_type_data, config)
