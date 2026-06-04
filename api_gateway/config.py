from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = Field("development", env="APP_ENV")
    database_url: str = Field("sqlite:///./travelsouls.db", env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    openai_api_key: str | None = Field(None, env="OPENAI_API_KEY")
    tavily_api_key: str | None = Field(None, env="TAVILY_API_KEY")
    openweather_api_key: str | None = Field(None, env="OPENWEATHER_API_KEY")
    pinecone_api_key: str | None = Field(None, env="PINECONE_API_KEY")
    pinecone_environment: str | None = Field(None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str | None = Field(None, env="PINECONE_INDEX_NAME")
    sentry_dsn: str | None = Field(None, env="SENTRY_DSN")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
