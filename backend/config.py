from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Ziyonet"
    API_PREFIX: str = "/api"
    APP_ENV: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    DATABASE_URL: str = "sqlite:///./ziyonet.db"

    OLLAMA_URL: str = "http://localhost:11434/api/chat"
    OLLAMA_MODEL: str = "qwen3.5:4b"
    OLLAMA_NUM_THREADS: int = 4

    CACHE_TTL_FAST: int = 3600
    CACHE_TTL_DEEP: int = 21600
    CACHE_MAX_SIZE: int = 1000

    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    MAX_BOOKS_PER_PAGE: int = 20
    SEARCH_DEBOUNCE_MS: int = 300
    API_RATE_LIMIT: int = 100

    FAST_MODE_TOKENS: int = 300
    DEEP_MODE_TOKENS: int = 800
    FAST_MODE_TIMEOUT: int = 30
    DEEP_MODE_TIMEOUT: int = 90

    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    @model_validator(mode="after")
    def validate_security_defaults(self):
        if self.APP_ENV.lower() != "development":
            if self.SECRET_KEY == "change-me":
                raise ValueError("SECRET_KEY must be changed outside development")
            if self.DEFAULT_ADMIN_PASSWORD == "admin123":
                raise ValueError("DEFAULT_ADMIN_PASSWORD must be changed outside development")
        return self

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
