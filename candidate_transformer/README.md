Multi-Source Candidate Data Transformer

This is a Python project that collects candidate information from different sources like CSV files and text resumes. It combines the data, removes duplicates, fixes formatting, and creates one clean candidate profile.

Main Features
Reads data from both CSV files and text resumes.
Cleans and formats data (phone numbers, emails, dates, skills, and locations).
Combines information from multiple sources.
Chooses the most reliable value when there is a conflict.
Keeps track of where every piece of information came from.
Creates output in different formats using JSON configuration.
Can be used from the Command Line (CLI) or through a FastAPI web server.
Folder Structure
candidate_transformer/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── constants.py
│   ├── schemas.py
│   ├── validator.py
│   ├── confidence.py
│   ├── merger.py
│   ├── projection.py
│   ├── provenance.py
│   │
│   ├── normalizers/
│   │   ├── phone.py
│   │   ├── date.py
│   │   ├── skill.py
│   │   ├── email.py
│   │   ├── location.py
│   │   └── links.py
│   │
│   ├── extractors/
│   │   ├── csv_reader.py
│   │   └── resume_txt.py
│   │
│   ├── pipeline/
│   │   └── pipeline.py
│   │
│   ├── models/
│   └── utils/
│
├── configs/
├── sample_inputs/
├── sample_outputs/
├── tests/
├── README.md
└── requirements.txt
Installation

Make sure Python 3.9 or above is installed.

Go to the project folder.

cd candidate_transformer

Install all required libraries.

pip install -r requirements.txt
Running the CLI

Run the project using the default configuration.

$env:PYTHONPATH="."; python app/main.py --csv sample_inputs/sample.csv --resume sample_inputs/resume.txt --config configs/default.json

For Linux/macOS:

PYTHONPATH=. python app/main.py --csv sample_inputs/sample.csv --resume sample_inputs/resume.txt --config configs/default.json

To use a custom configuration:

$env:PYTHONPATH="."; python app/main.py --csv sample_inputs/sample.csv --resume sample_inputs/resume.txt --config configs/custom.json
Running the FastAPI Server

Start the server.

$env:PYTHONPATH="."; python app/main.py --server --host 127.0.0.1 --port 8000

python -m uvicorn app.main:app --reload

Open Swagger UI in your browser.

http://127.0.0.1:8000/docs

Send files using curl.

curl -X POST "http://127.0.0.1:8000/transform" \
-F "csv=@sample_inputs/sample.csv" \
-F "resume=@sample_inputs/resume.txt" \
-F "config_json={\"fields\":[{\"path\":\"name\",\"from\":\"full_name\"}]}"
Running Tests

Run all test files.

$env:PYTHONPATH="."; pytest tests/
How the Project Works

The project follows these simple steps:

Read the input files.
Extract candidate information.
Clean and format the data.
Merge information from different sources.
Calculate a confidence score.
Create the required output.
Check if the final output is valid.
Data Cleaning

The project automatically:

Converts phone numbers into one standard format.
Converts emails to lowercase.
Formats dates properly.
Standardizes skill names.
Converts country names into standard country codes.
Removes duplicate emails and skills.
Handling Conflicts

Sometimes the CSV and resume contain different information.

The project solves this by:

Giving higher priority to CSV data (confidence = 0.95).
Giving second priority to Resume data (confidence = 0.85).
If both have the same confidence:
For numbers, it keeps the larger value.
For text, it keeps the longer value.
If one source has an empty field and the other has a value, it keeps the available value.
Confidence Score

The project gives every candidate profile a confidence score between 0 and 1.

The score depends on:

Quality of the data source.
How much information is available.
Whether phone numbers and dates were successfully formatted.
Number of conflicts while merging.

Higher score means the profile is more reliable.

Future Improvements

Some ideas for improving the project are:

Use AI models like OpenAI or Gemini to extract resume information more accurately.
Add support for PDF resumes and LinkedIn profiles.
Improve skill matching using AI or machine learning.
Store candidate data in a database to avoid duplicate profiles.
Summary

This project helps create one clean and complete candidate profile by collecting information from multiple sources. It automatically cleans the data, resolves conflicts, tracks where the information came from, calculates a confidence score, and generates the final output in the required format. It can be used from both the command line and a FastAPI web application.