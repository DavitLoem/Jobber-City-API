from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Security Keys
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    
    # 3rd Party
    GOOGLE_CLIENT_ID: str
    
    # Security Policies (មានតម្លៃ Default ស្រាប់ ការពារក្រែងភ្លេចដាក់ក្នុង .env)
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15
    REQUIRE_ADMIN_OTP: bool = False

    # 🎯 នេះគឺជាទម្រង់ថ្មីរបស់ Pydantic V2 ក្នុងការហៅ .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # បើក្នុង .env មានអថេរផ្សេងទៀតដែលមិនបានប្រកាសក្នុងនេះ វានឹងរំលងអត់ Error ទេ
    )

# បង្កើត Instance មួយនេះដើម្បី Import យកទៅប្រើប្រាស់គ្រប់ទីកន្លែង
settings = Settings()