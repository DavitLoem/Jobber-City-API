import os
import httpx # ប្រើ HTTPX ជំនួស aiosmtplib
from fastapi import HTTPException, status
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
MAIL_FROM_ADDRESS = os.getenv("MAIL_FROM_ADDRESS")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME")

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "email")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

async def send_otp_email(recipient_email: str, otp_code: str):
    if not BREVO_API_KEY:
        raise ValueError("សូមពិនិត្យមើល BREVO_API_KEY នៅក្នុង .env ឡើងវិញ")

    try:
        template = env.get_template("otp_email.html")
        html_content = template.render(otp_code=otp_code)
    except Exception as e:
        print(f"Template Rendering Error: {e}")
        raise HTTPException(status_code=500, detail="មានបញ្ហាក្នុងការរៀបចំទម្រង់អ៊ីមែល")

    # រៀបចំទិន្នន័យ (Payload) ដើម្បីបាញ់ទៅកាន់ Brevo API ផ្ទាល់
    payload = {
        "sender": {"name": MAIL_FROM_NAME, "email": MAIL_FROM_ADDRESS},
        "to": [{"email": recipient_email}],
        "subject": "Your Jobber City Verification Code",
        "htmlContent": html_content
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    # បាញ់ API ចេញទៅក្រៅ
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                json=payload,
                headers=headers,
                timeout=10.0 # កំណត់កុំឱ្យចាំយូរពេក
            )
            
            # ឆែកមើលថាតើ API ទទួលជោគជ័យដែរឬទេ
            if response.status_code in (200, 201):
                return True
            else:
                print(f"Brevo API Error: {response.text}")
                raise HTTPException(status_code=500, detail="ប្រព័ន្ធបដិសេធការផ្ញើអ៊ីមែល")

    except httpx.RequestError as e:
        print(f"HTTP Request Error: {e}")
        raise HTTPException(status_code=500, detail="មិនអាចភ្ជាប់ទៅកាន់ប្រព័ន្ធផ្ញើអ៊ីមែលបានទេ")