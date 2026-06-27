from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    openai_api_key: str
    gemini_api_key: str
    database_url: str
    langcache_api: str
    langcache_id: str
    langfuse_secret_key: str
    langfuse_public_key: str
    langfuse_host: str
    
    class Config:
        env_file = ".env"


settings = Settings()

print(settings.database_url)