"""Validated Interactions API access shared by M1, M2 and M3.

Public contract: await generate_structured(prompt, image_bytes, response_schema).
Failures raise GeminiError subclasses with safe messages and an http_status for
the gateway owner to map. No raw SDK exception text or image data is logged.
"""

import asyncio
import base64
import contextvars
import io
import json
import logging
import random
import time
import warnings
from dataclasses import dataclass
from typing import Any, TypeVar

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, settings

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000


class GeminiError(RuntimeError):
    """Safe service error; the gateway may expose this message to a client."""

    http_status = 502


class GeminiConfigurationError(GeminiError):
    http_status = 503


class GeminiAuthenticationError(GeminiError):
    http_status = 503


class GeminiModelAccessError(GeminiError):
    http_status = 503


class GeminiInvalidOutputError(GeminiError):
    pass


class GeminiRetryExhaustedError(GeminiError):
    http_status = 503


class GeminiInputError(GeminiError):
    http_status = 400


@dataclass(frozen=True)
class GenerationMetadata:
    source: str
    model: str
    interaction_id: str | None
    latency_seconds: float


def detect_image_mime(image_bytes: bytes) -> str:
    """Decode and verify an image, rejecting empty, truncated and unsafe files."""
    if not isinstance(image_bytes, bytes) or not image_bytes:
        raise GeminiInputError("Please upload a non-empty image.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise GeminiInputError("Please upload an image smaller than 10 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(image_bytes)) as image:
                mime = {"JPEG": "image/jpeg", "PNG": "image/png",
                        "WEBP": "image/webp"}.get(image.format)
                if mime is None:
                    raise GeminiInputError("Please upload a JPEG, PNG or WEBP image.")
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise GeminiInputError("Please resize the image below 20 megapixels.")
                image.verify()
            with Image.open(io.BytesIO(image_bytes)) as image:
                image.load()
        return mime
    except GeminiInputError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
            Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise GeminiInputError("The image cannot be read. Please take another photo.") from None


class GeminiCoreEngine:
    """Lazy SDK initialization; per-task metadata prevents cross-request leakage."""

    def __init__(self, config: Settings | None = None, *, client: Any = None):
        self.config = config if config is not None else settings
        self.model_name = self.config.GEMINI_MODEL_NAME
        self.client = client
        self._metadata = contextvars.ContextVar(
            f"arlo_generation_{id(self)}", default=None
        )

    @property
    def last_metadata(self) -> GenerationMetadata | None:
        """Read in the same async task after awaiting generation."""
        return self._metadata.get()

    def _get_client(self):
        if self.client is not None:
            return self.client
        if not self.config.has_api_key:
            raise GeminiConfigurationError("GEMINI_API_KEY is not configured.")
        try:
            from google import genai

            self.client = genai.Client(
                api_key=self.config.GEMINI_API_KEY.get_secret_value(),
                http_options={
                    "timeout": int(self.config.GEMINI_TIMEOUT_SECONDS * 1000),
                    "retry_options": {"attempts": 0},
                },
            )
        except Exception:
            raise GeminiConfigurationError("Could not initialize the Google GenAI SDK.") from None
        return self.client

    async def generate_structured(
        self, prompt: str, image_bytes: bytes | None, response_schema: type[T],
        *, system_instruction: str | None = None, store: bool = False,
    ) -> T:
        """Generate and validate JSON; storage stays opt-in for private inputs."""
        self._metadata.set(None)
        if not isinstance(prompt, str) or not prompt.strip():
            raise GeminiInputError("A non-empty prompt is required.")
        mime = None
        if image_bytes is not None:
            mime = await asyncio.to_thread(detect_image_mime, image_bytes)
        if self.config.ARLO_ENABLE_MOCKS:
            result = self._demo_result(response_schema)
            self._metadata.set(GenerationMetadata("demo", self.model_name, None, 0))
            return result
        content = [{"type": "text", "text": prompt}]
        if image_bytes is not None:
            content.append({
                "type": "image",
                "data": base64.b64encode(image_bytes).decode("ascii"),
                "mime_type": mime,
            })
        request = {
            "model": self.model_name,
            "input": content,
            "store": store,
            "generation_config": {
                "thinking_level": self.config.GEMINI_THINKING_LEVEL,
                "max_output_tokens": self.config.GEMINI_MAX_OUTPUT_TOKENS,
            },
            "response_format": {
                "type": "text", "mime_type": "application/json",
                "schema": response_schema.model_json_schema(),
            },
        }
        if system_instruction:
            request["system_instruction"] = system_instruction
        start = time.monotonic()
        interaction = await self._request(request)
        try:
            if getattr(interaction, "status", "completed") != "completed":
                raise ValueError("Interaction did not complete")
            # The live API currently omits id for stateless store=False calls.
            # An ID is required only when the caller opts into server storage.
            raw_interaction_id = getattr(interaction, "id", None)
            if store and (
                not isinstance(raw_interaction_id, str) or not raw_interaction_id
            ):
                raise ValueError("Missing stored interaction ID")
            if raw_interaction_id in (None, ""):
                interaction_id = None
            elif isinstance(raw_interaction_id, str):
                interaction_id = raw_interaction_id
            else:
                raise ValueError("Invalid interaction ID")
            output_text = getattr(interaction, "output_text", None)
            if not isinstance(output_text, str):
                raise ValueError("Missing text output")
            # Provenance is controlled by the server, not by generated JSON.
            from app.schemas.m1_vision import VisionExplainResult
            if response_schema is VisionExplainResult:
                payload = json.loads(output_text)
                if not isinstance(payload, dict):
                    raise ValueError("Expected an object")
                payload["source"] = "gemini"
                result = response_schema.model_validate(payload)
            else:
                result = response_schema.model_validate_json(output_text)
        except (ValidationError, ValueError, TypeError, AttributeError):
            raise GeminiInvalidOutputError(
                "Gemini returned an incomplete or invalid response. Please try again."
            ) from None
        self._metadata.set(GenerationMetadata(
            "gemini", self.model_name, interaction_id, time.monotonic() - start
        ))
        logger.info("Gemini generation completed model=%s interaction_id=%s",
                    self.model_name, interaction_id or "not-stored")
        return result

    async def _request(self, request: dict):
        client = self._get_client()
        # Disable SDK retries: exactly three application attempts at most.
        interactions = client.interactions
        # SDK 2.34's HttpRetryOptions(attempts=0) is normalized to 1 and
        # interpreted as one retry by Interactions. Disable its generated
        # transport retry configuration explicitly; tested at the HTTP boundary.
        if hasattr(interactions, "sdk_configuration"):
            interactions.sdk_configuration.retry_config = None
        for attempt in range(3):
            try:
                return await asyncio.to_thread(
                    interactions.create, **request,
                    timeout=self.config.GEMINI_TIMEOUT_SECONDS,
                    automatic_continuation=False,
                )
            except Exception as exc:
                status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
                if status in (429, 503):
                    if attempt == 2:
                        raise GeminiRetryExhaustedError(
                            "Gemini is busy or quota is exhausted. Please try again later."
                        ) from None
                    await asyncio.sleep(2 ** attempt + random.uniform(0, 0.25))
                    continue
                if status == 401:
                    raise GeminiAuthenticationError("The Gemini API key was rejected.") from None
                if status in (403, 404):
                    raise GeminiModelAccessError(
                        "The configured Gemini model or project is unavailable to this key."
                    ) from None
                raise GeminiError(
                    "Gemini request failed. Check connectivity and model configuration."
                ) from None

    def _demo_result(self, schema: type[T]) -> T:
        """Explicit demo mode has visible text labels; never infer medical doses."""
        from app.schemas.m1_vision import VisionExplainResult

        if schema is VisionExplainResult:
            result = schema(
                category="OTHER",
                headline_large="Demo data: Please take a clearer photo",
                audio_script="Demo data. Please take a clearer photo. No label was analysed.",
                action_items=["Demo data: retake photo"],
                is_blurry=True,
                source="demo",
            )
            return result
        # Arbitrary schemas cannot be safely populated with invented data.
        raise GeminiConfigurationError(
            "Demo data is only available for VisionExplainResult. Disable mock mode for other schemas."
        )

    async def generate_text(self, prompt: str, *, system_instruction: str | None = None) -> str:
        """M3 helper using the same validated, text-only Interactions path."""
        class TextResult(BaseModel):
            text: str

        result = await self.generate_structured(
            prompt, None, TextResult, system_instruction=system_instruction,
        )
        if not result.text.strip():
            raise GeminiInvalidOutputError("Gemini returned empty story text.")
        return result.text


gemini_engine = GeminiCoreEngine()
