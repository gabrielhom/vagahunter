from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    database_url: str = "sqlite:///./data/sql_app.db"
    scraper_timeout: int = 10
    scraper_detail_timeout: int = 5
    scraper_max_results: int = 5
    scraper_sleep_seconds: float = 0.5
    api_title: str = "VagaHunter API"
    api_description: str = "API REST para monitoramento de vagas remotas."
    api_version: str = "1.0.0"

    class Config:
        env_file = ".env"

settings = Settings()
