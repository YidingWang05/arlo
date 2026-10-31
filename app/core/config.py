"""Environment settings shared by the Arlo backend."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    GEMINI_API_KEY: SecretStr = SecretStr("")
    GEMINI_MODEL_NAME: str = "gemini-4-argon"
    GEMINI_THINKING_LEVEL: Literal["low", "medium", "high"] = "low"
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(default=32768, ge=256, le=65536)
    GEMINI_TIMEOUT_SECONDS: float = Field(default=45, gt=0, le=120)
    ARLO_ENABLE_MOCKS: bool = False
    APP_PORT: int = 8000

    @field_validator("GEMINI_THINKING_LEVEL", mode="before")
    @classmethod
    def normalize_thinking(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @property
    def has_api_key(self) -> bool:
        value = self.GEMINI_API_KEY.get_secret_value().strip()
        return bool(value) and value not in {
            "your_gemini_api_key_here", "replace_with_the_event_api_key",
            "YOUR_API_KEY",
        }


settings = Settings()
