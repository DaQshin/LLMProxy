from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    openai_api_key: str
    gemini_api_key: str
    database_url: str
    qdrant_host: str
    qdrant_port: int
    
    class Config:
        env_file = ".env"


settings = Settings()

print(settings.database_url)