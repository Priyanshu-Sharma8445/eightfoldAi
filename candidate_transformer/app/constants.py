# app/constants.py

# Configurable skill dictionary mapping variations to standard names (case-insensitive keys)
SKILL_DICTIONARY = {
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node js": "Node.js",
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "python": "Python",
    "python3": "Python",
    "py": "Python",
    "golang": "Go",
    "go lang": "Go",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
}

# Default source confidence levels
DEFAULT_SOURCE_CONFIDENCE = {
    "csv": 0.95,
    "resume": 0.85
}

# Country name mapping for ISO-3166 alpha-2
COUNTRY_MAPPING = {
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "india": "IN",
    "united kingdom": "GB",
    "uk": "GB",
    "great britain": "GB",
    "canada": "CA",
    "germany": "DE",
    "deutschland": "DE",
    "france": "FR",
    "australia": "AU",
    "singapore": "SG",
    "japan": "JP",
    "brazil": "BR",
}

# Domains to match for link categorization
LINK_CATEGORIES = {
    "github.com": "github",
    "linkedin.com": "linkedin",
}
