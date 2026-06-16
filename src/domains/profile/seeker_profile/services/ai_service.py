import json
from google import genai
from google.genai import types
from fastapi import HTTPException, status
from src.core.config import settings

# 🎯 បង្កើត Client តាមស្តង់ដារ SDK ថ្មី
client = genai.Client(api_key=settings.GEMINI_API_KEY)
async def analyze_cv_with_gemini(cv_text: str) -> dict:
    """
    បោះអត្ថបទ CV ទៅឱ្យ Gemini ដើម្បីវិភាគ និងទាញយកទិន្នន័យ។
    """
    if not cv_text or len(cv_text.strip()) < 50:
        return {"is_cv": False, "reason": "The text is too short or unreadable. Please provide a valid CV."}

    # 🎯 Prompt ដែលកំណត់ទម្រង់យ៉ាងច្បាស់
    prompt = """
    You are an expert HR Technical Recruiter. Your task is to analyze the following extracted text from a document and determine if it is a Resume/CV.
    If it is a CV, extract the core information to auto-fill a candidate's profile.

    Output ONLY a valid JSON object matching this exact structure:
    {
        "is_cv": true/false,
        "confidence_score": 0-100,
        "reason": "Brief explanation in Khmer",
        "extracted_data": {
            "skills": ["Skill 1"],
            "experiences": [
                {
                    "job_title": "String",
                    "company_name": "String",
                    "start_date": "YYYY-MM-DD or null",
                    "end_date": "YYYY-MM-DD or null"
                }
            ],
            "educations": [
                {
                    "school_name": "String",
                    "degree": "String",
                    "field_of_study": "String or null",
                    "start_date": "YYYY-MM-DD or null",
                    "end_date": "YYYY-MM-DD or null"
                }
            ]
        }
    }

    Rules:
    1. Output MUST be valid JSON only.
    2. If is_cv is false, "extracted_data" can be empty lists.
    3. For dates, if only a year is mentioned (e.g., 2020), format as "2020-01-01". If present to current, end_date is null.
    """

    try:
        # ហៅទៅកាន់ Gemini API ដោយប្រើ Method ថ្មី
        response = client.models.generate_content(
            model="gemini-3.5-flash", # ប្រើប្រាស់ Model ជំនាន់ថ្មីដែលអ្នកបានឃើញ
            contents=f"{prompt}\n\nHere is the document text:\n---\n{cv_text}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json", # 🎯 បង្ខំឱ្យ Gemini ឆ្លើយតបជា JSON សុទ្ធ
            )
        )
        
        response_text = response.text.strip()
        parsed_data = json.loads(response_text)
        
        return parsed_data

    except json.JSONDecodeError as e:
        print(f"JSON Parse Error from AI: {e}\nResponse was: {response.text}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The AI system could not extract data from this CV. Please try again."
        )
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The AI system could not extract data from this CV. Please try again."
        )