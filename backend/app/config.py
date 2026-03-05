from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "OCRAgent"
    
    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # LLM Configuration
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_API_KEY: str = "ollama" # Can be overridden by .env
    LLM_MODEL: str = "qwen2.5-vision"
    
    # Extraction Scheduling
    EXTRACTION_POLL_INTERVAL_SECONDS: int = 180
    TRIGGER_EXTRACTION_IMMEDIATELY: bool = False

    # Security & Paths
    DATA_DIR: str = "data"
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ["../.env", ".env"]
        extra = "ignore"

settings = Settings()
