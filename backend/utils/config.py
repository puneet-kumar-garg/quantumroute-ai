from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str = "postgresql://puneetkumargarg@localhost:5432/quantumroute"
    SECRET_KEY: str = "quantum-route-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ENVIRONMENT: str = "development"
    INITIAL_ADMIN_EMAIL: str | None = None
    INITIAL_ADMIN_PASSWORD: str | None = None
    COOKIE_SECURE: bool = False
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    OSRM_TIMEOUT_SECONDS: float = 6.0

    @model_validator(mode="after")
    def validate_security(self):
        if self.ENVIRONMENT.lower() == "production":
            if len(self.SECRET_KEY) < 32 or "change-in-production" in self.SECRET_KEY:
                raise ValueError("Production SECRET_KEY must be a unique value of at least 32 characters")
            if not self.COOKIE_SECURE:
                raise ValueError("COOKIE_SECURE must be true in production")
        return self

settings = Settings()
