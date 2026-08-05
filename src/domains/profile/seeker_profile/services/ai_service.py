import json
import asyncio
import logging
from google import genai
from google.genai import types
from fastapi import HTTPException, status
from src.core.config import settings

# 🎯 បង្កើត Client តាមស្តង់ដារ SDK ថ្មី
client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def analyze_cv_with_gemini(cv_text: str, max_retries: int = 3) -> dict:
    """
    បោះអត្ថបទ CV ទៅឱ្យ Gemini ដើម្បីវិភាគ និងទាញយកទិន្នន័យ (ភ្ជាប់ជាមួយប្រព័ន្ធការពារ Error 503)។
    """
    if not cv_text or len(cv_text.strip()) < 50:
        return {"is_cv": False, "reason": "The text is too short or unreadable. Please provide a valid CV."}

    # 🎯 Prompt រក្សាទុកដដែល
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
            "languages": [
                {
                    "name": "String (e.g., English, Khmer, French)",
                    "level": "String (e.g., Basic, Conversational, Fluent, Native) or null"
                }
            ],
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
    3. For dates: if only a year is mentioned (e.g., 2020), format as "2020-01-01". If it says "Present", "Current", or "Now", set end_date to null.
    4. Biography Handling: Treat any section labeled 'Objective', 'Summary', 'Profile', 'About Me', or similar, as the 'biography'.
    5. Language Handling: Extract languages. If proficiency level is unclear or presented visually, set 'level' to null or guess based on context.
    """

    for attempt in range(max_retries):
        try:
            # 🎯 ជួសជុល: ប្រើប្រាស់ client.aio សម្រាប់ Asynchronous call កុំឱ្យគាំង Server
            response = await client.aio.models.generate_content(
                model="gemini-3.6-flash", # 🎯 ជួសជុល: ប្តូរមកប្រើ 1.5-flash ដែលជា Model ត្រឹមត្រូវ
                contents=f"{prompt}\n\nHere is the document text:\n---\n{cv_text}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", 
                    temperature=0.1
                )
            )
            
            response_text = response.text.strip()
            parsed_data = json.loads(response_text)
            
            return parsed_data

        except json.JSONDecodeError as e:
            print(f"JSON Parse Error from AI: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The AI system could not extract data from this CV. Please try again."
            )
        except Exception as e:
            error_msg = str(e)
            
            # 🎯 ចាប់យក Error 503 ឬ High Demand ហើយធ្វើការ Retry
            if "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg.lower():
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt # រង់ចាំ 1s, 2s, 4s រួចសាកល្បងម្តងទៀត
                    logging.warning(f"Gemini API overloaded (503). Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue 
                else:
                    logging.error(f"Gemini API Error after {max_retries} attempts: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="The AI system is currently overloaded. Please try again later."
                    )
            else:
                # បើជា Error ផ្សេង (មិនមែន 503) គឺបោះចេញតែម្តង
                logging.error(f"Gemini API Error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="The AI system encountered an error. Please try again."
                )