"""Stable M1 response fields with enforceable display and safety constraints."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CLARIFICATION = (
    "Please take a clearer photo showing the whole label. "
    "Check the original label or ask a pharmacist if you are unsure."
)
MEDICINE_REMINDER = "Check the original label or ask a pharmacist if you are unsure."


class VisionExplainResult(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category: Literal["MEDICINE", "BILL", "NOTICE", "OTHER"]
    headline_large: str = Field(min_length=1, max_length=180, description="At most 15 plain-English words")
    audio_script: str = Field(min_length=1, max_length=1200, description="Short, warm spoken explanation")
    action_items: list[str] = Field(default_factory=list, max_length=3)
    is_blurry: bool = Field(description="True for unclear, incomplete or ambiguous label instructions")
    source: Literal["gemini", "demo"] = Field(
        default="gemini", description="Server-controlled output provenance",
    )

    @field_validator("headline_large")
    @classmethod
    def limit_headline(cls, value: str) -> str:
        if len(value.split()) > 15:
            raise ValueError("headline_large must contain at most 15 words")
        return value

    @field_validator("action_items")
    @classmethod
    def validate_actions(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or len(value) > 180 for value in values):
            raise ValueError("Action items must be short and non-empty")
        return [value.strip() for value in values]

    @model_validator(mode="after")
    def protect_uncertain_labels(self) -> Self:
        # Once uncertain, never pass generated dose/payment instructions downstream.
        if self.is_blurry:
            self.headline_large = "Please take a clearer photo of the whole label"
            self.audio_script = CLARIFICATION
            self.action_items = ["Retake a clear photo of the whole label"]
        elif self.category == "MEDICINE":
            if MEDICINE_REMINDER not in self.audio_script:
                self.audio_script = self.audio_script[:1050].rstrip() + " " + MEDICINE_REMINDER
        if self.source == "demo":
            if not self.headline_large.startswith("Demo data:"):
                self.headline_large = "Demo data: " + self.headline_large
            if not self.audio_script.startswith("Demo data."):
                self.audio_script = "Demo data. " + self.audio_script
        return self
