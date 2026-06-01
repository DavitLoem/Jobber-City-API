import os
import aiosmtplib
from email.message import EmailMessage
from fastapi import HTTPException, status
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader # ហៅ Jinja2 មកប្រើ

load_dotenv()

MAIL_HOST = os.getenv("MAIL_HOST")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM_ADDRESS = os.getenv("MAIL_FROM_ADDRESS")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME")

# រៀបចំ Jinja2 ឱ្យស្គាល់ទីតាំង Folder ដែលយើងផ្ទុក Template
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "email")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

async def send_otp_email(recipient_email: str, otp_code: str):
    """
    មុខងារបញ្ជូន OTP តាមរយៈ SMTP Protocol ដោយប្រើប្រាស់ Jinja2 HTML Template
    """
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        raise ValueError("សូមពិនិត្យមើល SMTP credentials នៅក្នុង .env ឡើងវិញ")

    msg = EmailMessage()
    msg["Subject"] = "Your Jobber City Verification Code"
    msg["From"] = f"{MAIL_FROM_NAME} <{MAIL_FROM_ADDRESS}>"
    msg["To"] = recipient_email

    try:
        # ១. ទាញយក File HTML
        template = env.get_template("otp_email.html")
        
        # ២. បញ្ចូលទិន្នន័យ (otp_code) ទៅក្នុង Template
        html_content = template.render(otp_code=otp_code)

        # ៣. កំណត់ខ្លឹមសារសំបុត្រ
        msg.set_content(html_content, subtype="html") 

    except Exception as e:
        print(f"Template Rendering Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="មានបញ្ហាក្នុងការរៀបចំទម្រង់អ៊ីមែល"
        )

    # ៤. បញ្ជូនអ៊ីមែល
    try:
        await aiosmtplib.send(
            msg,
            hostname=MAIL_HOST,
            port=MAIL_PORT,
            username=MAIL_USERNAME,
            password=MAIL_PASSWORD,
            use_tls=True,    # 🎯 ត្រូវតែ True សម្រាប់ Port 465
            start_tls=False, # 🎯 ត្រូវតែ False សម្រាប់ Port 465
        )
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="មានបញ្ហាក្នុងការភ្ជាប់ទៅកាន់ប្រព័ន្ធផ្ញើអ៊ីមែល សូមសាកល្បងម្តងទៀតនៅពេលក្រោយ"
        )