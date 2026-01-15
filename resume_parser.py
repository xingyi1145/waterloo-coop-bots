import os
import sys
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from markitdown import MarkItDown

# --- 1. Pydantic Schema ---

class PersonalInfo(BaseModel):
    name: str
    email: str
    phone: str
    location: str
    linkedin: Optional[str]
    github: Optional[str]
    website: Optional[str]

class Experience(BaseModel):
    title: str
    company: str
    years: str
    location: Optional[str]
    description: List[str]

class Education(BaseModel):
    institution: str
    degree: str
    years: str

class ResumeData(BaseModel):
    personalInfo: PersonalInfo
    summary: str
    workExperience: List[Experience]
    education: List[Education]
    skills: List[str]

# --- 2. Functions ---

def convert_to_markdown(file_path: str) -> str:
    """
    Ingests a file (PDF/DOCX) and returns markdown text content.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    md = MarkItDown()
    result = md.convert(file_path)
    
    # Return the text content from the Document object
    return result.text_content

def parse_resume_to_json(markdown_text: str, openai_api_key: str) -> dict:
    """
    Uses OpenAI to parse markdown resume text into a structured JSON dictionary.
    """
    client = OpenAI(api_key=openai_api_key)

    prompt_template = f"""
Parse this resume into JSON. Output ONLY the JSON object, no other text.
Map content to standard sections.
Rules:
- Use "" for missing text fields, [] for missing arrays.
- Format years as "YYYY - YYYY" or "YYYY - Present".
- Normalize dates: "Jan 2020" -> "2020".

Resume to parse:
{markdown_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o",  # Using a capable model for JSON extraction
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts structured data from resumes."},
            {"role": "user", "content": prompt_template}
        ],
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content
    
    # Load raw JSON
    raw_json = json.loads(content)
    
    # Validate with Pydantic
    resume_data = ResumeData.model_validate(raw_json)
    
    # Return dict
    return resume_data.model_dump()

# --- 3. Main Block ---

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resume_parser.py <path_to_resume_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    try:
        print(f"Reading file: {file_path}...")
        markdown_text = convert_to_markdown(file_path)
        
        print("Parsing with LLM...")
        parsed_data = parse_resume_to_json(markdown_text, api_key)
        
        # Print result nicely
        print(json.dumps(parsed_data, indent=2))
        
    except Exception as e:
        print(f"An error occurred: {e}")
