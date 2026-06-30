# tests/test_extractors.py

import pytest
from app.extractors.csv_reader import extract_csv
from app.extractors.resume_txt import extract_resume_txt

def test_csv_extractor_valid():
    csv_content = """full_name,email,phone,city,state,country,linkedin,github,headline,years_experience,skills
Jane Doe,jane.doe@example.com,+14155552671,Seattle,WA,USA,linkedin.com/in/jane,github.com/jane,Software Architect,10,Python;AWS;React
"""
    profile = extract_csv(csv_content, "test.csv")
    assert profile.source_name == "test.csv"
    assert profile.source_confidence == 0.95
    assert profile.full_name == "Jane Doe"
    assert profile.emails == ["jane.doe@example.com"]
    assert profile.phones == ["+14155552671"]
    assert profile.location.city == "Seattle"
    assert profile.location.region == "WA"
    assert profile.location.country == "USA"
    assert profile.years_experience == 10.0
    assert profile.skills == ["Python", "AWS", "React"]

def test_csv_extractor_malformed():
    # Empty headers, empty columns, garbage text
    profile1 = extract_csv("", "empty.csv")
    assert profile1.full_name is None
    assert len(profile1.emails) == 0

    profile2 = extract_csv("garbage,headers,only\n", "garbage.csv")
    assert profile2.full_name is None

def test_resume_txt_extractor():
    resume_content = """John Smith
Lead Backend Developer
Email: john.smith@work.com
Phone: (206) 555-0199
GitHub: www.github.com/jsmith
Location: Austin, Texas

Summary:
Experienced engineer with 7+ years of experience in system design.

Skills:
Go, Python, Kubernetes, SQL

Experience:
Senior Engineer at Austin Tech
Jan 2019 - Present
Worked on microservices.
    """
    profile = extract_resume_txt(resume_content, "john_resume.txt")
    assert profile.source_name == "john_resume.txt"
    assert profile.source_confidence == 0.85
    assert profile.full_name == "John Smith"
    assert profile.emails == ["john.smith@work.com"]
    assert profile.phones == ["(206) 555-0199"]
    assert profile.location.city == "Austin"
    assert profile.location.region == "Texas"
    assert profile.headline == "Lead Backend Developer"
    assert profile.years_experience == 7.0
    assert "Go" in profile.skills
    assert "Python" in profile.skills
    assert len(profile.experience) == 1
    assert profile.experience[0].job_title == "Senior Engineer"
    assert profile.experience[0].company == "Austin Tech"
    assert profile.experience[0].start_date == "Jan 2019"
    assert profile.experience[0].end_date == "Present"

def test_resume_txt_extractor_garbage():
    profile = extract_resume_txt("just some random text with no keywords", "garbage.txt")
    assert profile.source_name == "garbage.txt"
    assert profile.full_name is not None  # Heuristic fallback is first line
    assert len(profile.emails) == 0
    assert len(profile.phones) == 0
    assert len(profile.experience) == 0
