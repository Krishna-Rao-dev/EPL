"""
Configuration — reads from environment / .env
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017/"
    MONGO_DB: str = "compliance_db"

    # JWT
    SECRET_KEY: str = "pramanik-super-secret-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Ollama / LLM
    OLLAMA_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_MODEL: str = "llama3.2:3b"

    GROQ_API_KEY :str= "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"

  

    # Sandbox PAN API  (real key you provided — swap here)
    SANDBOX_PAN_API_KEY: str = os.getenv("SANDBOX_PAN_API_KEY", "your-sandbox-key-here")
    SANDBOX_PAN_URL: str = "https://api.sandbox.co.in/kyc/pan/status"
    SANDBOX_AUTH_URL: str = "https://api.sandbox.co.in/authenticate"

    # Tesseract
    TESSERACT_CMD: str = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # Poppler (Linux default)
    POPPLER_PATH: str = r"C:\poppler\poppler-25.12.0\Library\bin"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
