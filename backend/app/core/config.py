from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = ".env"

    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    gemini_api_key: str
    gemini_model: str

    allowed_origins: str = "*"

    @property
    def cors_origins(self) -> list[str]:
        if not self.allowed_origins or self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()  # type: ignore
