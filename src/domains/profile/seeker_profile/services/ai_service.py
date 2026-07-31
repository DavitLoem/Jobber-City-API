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

    # 🎯 កែសម្រួល Prompt ឱ្យទាញយកទិន្នន័យបានកាន់តែលម្អិត និងស៊ីគ្នាជាមួយ Database
    prompt = """
    You are an expert HR Technical Recruiter. Your task is to analyze the following extracted text from a document and determine if it is a Resume/CV.
    If it is a CV, extract the core information to auto-fill a candidate's profile.

    Output ONLY a valid JSON object matching this exact structure:
    {
        "is_cv": true,
        "confidence_score": 0-100,
        "reason": "Brief explanation in Khmer",
        "extracted_data": {
            "personal_info": {
                "first_name": "String or null",
                "last_name": "String or null",
                "email": "String or null",
                "phone_number": "String or null",
                "biography": "String (Short summary of the candidate) or null"
            },
            "skills": ["Skill 1", "Skill 2"],
            "experiences": [
                {
                    "job_title": "String",
                    "company_name": "String",
                    "start_date": "YYYY-MM-DD or null",
                    "end_date": "YYYY-MM-DD or null",
                    "description": "String (Summary of responsibilities) or null"
                }
            ],
            "educations": [
                {
                    "school_name": "String",
                    "degree": "String",
                    "field_of_study": "String or null",
                    "start_date": "YYYY-MM-DD or null",
                    "end_date": "YYYY-MM-DD or null",
                    "description": "String or null"
                }
            ]
        }
    }

    Rules:
    1. Output MUST be valid JSON only without any markdown formatting.
    2. If is_cv is false, set "is_cv": false, provide the "reason" in Khmer, and "extracted_data" must be empty.
    3. For dates: if only a year is mentioned (e.g., 2020), format as "2020-01-01". If it says "Present" or "Current", set end_date to null.
    4. Ensure names and text formatting are clean and professional.
    """

    try:
        # ហៅទៅកាន់ Gemini API
        response = client.models.generate_content(
            model="gemini-3.5-flash", # ប្រើប្រាស់ Model ដែលអ្នកបានកំណត់
            contents=f"{prompt}\n\nHere is the document text:\n---\n{cv_text}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json", 
                temperature=0.1 # 🎯 បន្ថែម Temperature ទាបដើម្បីឱ្យចម្លើយមានភាពជាក់លាក់ (Fact-based) មិនរវើរវាយ
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
            detail="The AI system encountered an error. Please try again."
        )