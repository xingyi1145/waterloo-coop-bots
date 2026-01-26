import os
import sys
import json
from typing import List, Optional
from pydantic import BaseModel, Field, BeforeValidator
from typing_extensions import Annotated
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
    # Use OpenRouter config if using that key
    base_url = "https://openrouter.ai/api/v1"
    
    client = OpenAI(
        api_key=openai_api_key,
        base_url=base_url
    )

    prompt_template = f"""
You are a Resume Parser. Convert the resume text below into the following JSON structure exactly. 
Do not change key names.

Expected JSON Structure:
{{
  "personalInfo": {{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "123-456-7890",
    "location": "City, Country",
    "linkedin": "url or empty",
    "github": "url or empty",
    "website": "url or empty"
  }},
  "summary": "Brief professional summary",
  "workExperience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "years": "YYYY - YYYY",
      "location": "City, Country",
      "description": ["bullet point 1", "bullet point 2"]
    }}
  ],
  "education": [
    {{
       "institution": "University Name",
       "degree": "Degree Name",
       "years": "YYYY - YYYY"
    }}
  ],
  "skills": ["skill1", "skill2", "skill3"]
}}

Rules:
- Use "" for missing text fields, [] for missing arrays.
- Format years as "YYYY - YYYY" or "YYYY - Present".
- Normalize dates: "Jan 2020" -> "2020".

Resume to parse:
{markdown_text}
"""

    response = client.chat.completions.create(
        model="tngtech/deepseek-r1t2-chimera:free", 
        messages=[
           # {"role": "system", "content": "You are a helpful assistant that extracts structured data from resumes."}, # DeepSeek R1 prefers simpler prompts sometimes
            {"role": "user", "content": prompt_template}
        ],
        extra_headers={
            "HTTP-Referer": "https://github.com/xingy/waterloo_coop_bot",
            "X-Title": "Waterloo Coop Bot",
        },
        # response_format={"type": "json_object"} # Removed for compatibility
    )

    content = response.choices[0].message.content
    
    # Simple cleanup for markdown json blocks
    if content.startswith("```"):
        import re
        content = re.sub(r"^```(?:json)?\n", "", content)
        content = re.sub(r"\n```$", "", content)
    
    # Load raw JSON
    try:
        raw_json = json.loads(content)
    except json.JSONDecodeError:
         # Fallback search
        import re
        match = re.search(r"(\{.*\})", content, re.DOTALL)
        if match:
             raw_json = json.loads(match.group(1))
        else:
            raise ValueError("Could not parse JSON from LLM response")
    
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
