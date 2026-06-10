from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Security Keys
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    
    # 3rd Party
    GOOGLE_CLIENT_ID: str
    
    # Security Policies
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15
    REQUIRE_ADMIN_OTP: bool = False

    # 🎯 Cloudinary Configurations
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" 
    )

settings = Settings()