import os
import json
import re
from openai import OpenAI

# --- CONFIGURATION ---
# OpenRouter API Key
API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "tngtech/deepseek-r1t2-chimera:free"
SITE_URL = "https://github.com/xingy/waterloo_coop_bot" 
SITE_NAME = "Waterloo Coop Bot"

# Initialize Sync Client
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL, 
)

EXTRACT_KEYWORDS_PROMPT = """
Extract job requirements as JSON. Output ONLY the JSON object.
Keys: "required_skills", "preferred_skills", "experience_requirements", "key_responsibilities".
Job description:
{job_description}
"""

MATCH_SCORE_PROMPT = """
You are an expert technical recruiter. Evaluate this candidate against the job requirements.

Job Requirements:
{job_keywords}

Candidate Resume:
{resume_json}

Output strictly valid JSON:
{{
  "match_score": <int 0-100>,
  "is_junior_friendly": <bool>,
  "missing_skills": [<list of strings>],
  "reasoning": "<short summary>"
}}
"""

def clean_json_response(response_text: str) -> dict:
    """
    Cleans the model response to ensure it parses as JSON.
    Removes markdown code blocks if present.
    """
    cleaned_text = response_text.strip()
    
    # Remove markdown code blocks (```json ... ```)
    if cleaned_text.startswith("```"):
        cleaned_text = re.sub(r"^```(?:json)?\n", "", cleaned_text)
        cleaned_text = re.sub(r"\n```$", "", cleaned_text)
    
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        # Fallback: try to find the first { and last }
        match = re.search(r"(\{.*\})", cleaned_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Return empty dictionary on failure rather than crashing
        print(f"Error: Failed to parse JSON from LLM response. Raw text: {response_text[:50]}...")
        return {}

def extract_job_keywords(job_text: str) -> dict:
    """
    Extracts structured requirements from a raw job description string using LLM.
    """
    prompt = EXTRACT_KEYWORDS_PROMPT.format(job_description=job_text)
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
            extra_headers={
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_NAME,
            },
        )
        content = response.choices[0].message.content
        return clean_json_response(content)
    except Exception as e:
        print(f"matcher.py: Error extracting keywords: {e}")
        return {}

def analyze_match(resume_json: dict, job_text: str) -> dict:
    """
    Evaluates a candidate against a job description.
    1. Extracts keywords from job description.
    2. Compares resume against extracted keywords.
    """
    # 1. Extract Keywords
    job_keywords = extract_job_keywords(job_text)
    if not job_keywords:
        return {
            "match_score": 0,
            "is_junior_friendly": False,
            "missing_skills": [],
            "reasoning": "Failed to extract job keywords."
        }
    
    # 2. Analyze Match
    # Convert dicts to strings for prompt insertion
    resume_str = json.dumps(resume_json)
    keywords_str = json.dumps(job_keywords)
    
    prompt = MATCH_SCORE_PROMPT.format(
        job_keywords=keywords_str,
        resume_json=resume_str
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
            extra_headers={
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_NAME,
            },
        )
        content = response.choices[0].message.content
        result = clean_json_response(content)
        
        # Ensure default keys exist if bad parsing
        if "match_score" not in result:
            result["match_score"] = 0
            result["reasoning"] = "JSON parsing complete but schema was invalid."
            
        return result
        
    except Exception as e:
        print(f"matcher.py: Error analyzing match: {e}")
        return {
            "match_score": 0,
            "is_junior_friendly": False,
            "missing_skills": [],
            "reasoning": f"Analysis failed: {str(e)}"
        }
