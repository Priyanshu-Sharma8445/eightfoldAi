# tests/test_normalizers.py

import pytest
from app.normalizers.email import normalize_email, normalize_emails
from app.normalizers.phone import normalize_phone, normalize_phones
from app.normalizers.date import normalize_date
from app.normalizers.skill import normalize_skill, normalize_skills
from app.normalizers.location import normalize_location
from app.normalizers.links import normalize_link, normalize_links
from app.schemas import LocationSchema

def test_email_normalization():
    assert normalize_email("  JANE.doe@EXAMPLE.com  ") == "jane.doe@example.com"
    assert normalize_email("") == ""
    assert normalize_email(None) == ""
    
    assert normalize_emails([" JANE.doe@EXAMPLE.com ", "jane.doe@example.com", "  work@example.com "]) == [
        "jane.doe@example.com",
        "work@example.com"
    ]

def test_phone_normalization():
    # US number format
    val, success = normalize_phone("+1 (415) 555-2671")
    assert val == "+14155552671"
    assert success is True

    # Bad format (fallback and return success=False)
    val, success = normalize_phone("12345-garbage")
    assert val == "12345-garbage"
    assert success is False
    
    # Empty
    assert normalize_phone(None) == ("", False)

    # Multi-phone normalization and deduplication
    vals, statuses = normalize_phones(["+1-415-555-2671", "12345-garbage", "+1 415 555 2671"])
    assert vals == ["+14155552671", "12345-garbage"]
    assert statuses == [True, False]

def test_date_normalization():
    assert normalize_date("2023-05-12") == "2023-05"
    assert normalize_date("May 2023") == "2023-05"
    assert normalize_date("05/2023") == "2023-05"
    assert normalize_date("2023/05") == "2023-05"
    assert normalize_date("2023") == "2023"
    assert normalize_date("June, 2021") == "2021-06"
    assert normalize_date("2021 June") == "2021-06"
    assert normalize_date("garbage-date") is None
    assert normalize_date("") is None
    assert normalize_date(None) is None

def test_skill_normalization():
    assert normalize_skill("NodeJS") == "Node.js"
    assert normalize_skill("node js") == "Node.js"
    assert normalize_skill("ReactJS") == "React"
    assert normalize_skill("golang") == "Go"
    assert normalize_skill("custom-skill-name") == "custom-skill-name"
    
    # Configurable skill dictionary override
    custom_dict = {"react": "React.js", "docker": "Docker Engine"}
    assert normalize_skill("react", custom_dict) == "React.js"
    assert normalize_skill("nodejs", custom_dict) == "nodejs"  # not in custom_dict
    
    assert normalize_skills(["NodeJS", "ReactJS", "NodeJS", "custom"]) == ["Node.js", "React", "custom"]

def test_location_normalization():
    # Comma-separated string with city, region, country
    loc = normalize_location("San Francisco, California, USA")
    assert loc.city == "San Francisco"
    assert loc.region == "California"
    assert loc.country == "US"

    # City, Country code
    loc2 = normalize_location("London, UK")
    assert loc2.city == "London"
    assert loc2.region is None
    assert loc2.country == "GB"

    # Dict input
    loc3 = normalize_location({"city": "Munich", "region": "Bavaria", "country": "Germany"})
    assert loc3.city == "Munich"
    assert loc3.region == "Bavaria"
    assert loc3.country == "DE"

    # Object input
    loc_schema = LocationSchema(city="Toronto", region="Ontario", country="Canada")
    loc4 = normalize_location(loc_schema)
    assert loc4.city == "Toronto"
    assert loc4.region == "Ontario"
    assert loc4.country == "CA"

def test_link_normalization():
    # GitHub link
    l1 = normalize_link("github.com/janedoe")
    assert l1.category == "github"
    assert l1.url == "github.com/janedoe"

    # LinkedIn link
    l2 = normalize_link("https://www.linkedin.com/in/janedoe")
    assert l2.category == "linkedin"
    
    # Portfolio link heuristics
    l3 = normalize_link("janedoe.github.io/blog")
    assert l3.category == "portfolio"

    l4 = normalize_link("http://janedoe.me")
    assert l4.category == "portfolio"
    
    # Other/Social
    l5 = normalize_link("https://twitter.com/janedoe")
    assert l5.category == "other"
    
    assert len(normalize_links(["github.com/janedoe", "github.com/janedoe"])) == 1
