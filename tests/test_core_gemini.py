"""Offline contract tests, including actual SDK serialization via MockTransport."""

import asyncio
import base64
import io
import json
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from google import genai
from PIL import Image
from pydantic import BaseModel

from app.core.base_model import (
    GeminiCoreEngine, GeminiError, GeminiConfigurationError,
    GeminiAuthenticationError, GeminiModelAccessError, GeminiInputError,
    GeminiInvalidOutputError, GeminiRetryExhaustedError, detect_image_mime,
)
from app.core.config import Settings
from app.schemas.m1_vision import VisionExplainResult


class Answer(BaseModel):
    answer: str


def config(**kwargs):
    return Settings(_env_file=None, GEMINI_API_KEY="", ARLO_ENABLE_MOCKS=False, **kwargs)


def response(text='{"answer":"ok"}', **kwargs):
    values = dict(id="interaction-test-1", status="completed", output_text=text)
    values.update(kwargs)
    return SimpleNamespace(**values)


def engine_with(create):
    return GeminiCoreEngine(config(), client=SimpleNamespace(interactions=SimpleNamespace(create=create)))


def image_bytes(fmt="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.mark.parametrize("fmt,mime", [
    ("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp"),
])
def test_detect_mime(fmt, mime):
    assert detect_image_mime(image_bytes(fmt)) == mime


@pytest.mark.parametrize("payload", [b"", b"not an image", b"\xff\xd8\xff", image_bytes("GIF")])
def test_reject_invalid_images(payload):
    with pytest.raises(GeminiInputError):
        detect_image_mime(payload)


@pytest.mark.asyncio
async def test_structured_request_and_metadata(caplog):
    create = Mock(return_value=response())
    engine = engine_with(create)
    payload = image_bytes()
    with caplog.at_level("INFO"):
        result = await engine.generate_structured("private-user-text", payload, Answer)
    request = create.call_args.kwargs
    assert result.answer == "ok"
    assert request["model"] == "gemini-4-argon"
    assert request["generation_config"] == {"thinking_level": "low", "max_output_tokens": 32768}
    assert request["input"][1]["data"] == base64.b64encode(payload).decode("ascii")
    assert request["input"][1]["mime_type"] == "image/png"
    assert request["response_format"]["schema"] == Answer.model_json_schema()
    assert request["store"] is False
    assert engine.last_metadata.interaction_id == "interaction-test-1"
    assert engine.last_metadata.source == "gemini"
    assert "private-user-text" not in caplog.text
    assert request["input"][1]["data"] not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_id", [None, ""])
async def test_stateless_response_without_id_is_valid(missing_id):
    create = Mock(return_value=response(id=missing_id))
    engine = engine_with(create)
    result = await engine.generate_structured("question", None, Answer)
    assert result.answer == "ok"
    assert create.call_args.kwargs["store"] is False
    assert engine.last_metadata.source == "gemini"
    assert engine.last_metadata.interaction_id is None


@pytest.mark.asyncio
async def test_stored_probe_requires_and_preserves_id():
    create = Mock(return_value=response())
    engine = engine_with(create)
    await engine.generate_structured("question", None, Answer, store=True)
    assert create.call_args.kwargs["store"] is True
    assert engine.last_metadata.interaction_id == "interaction-test-1"

    missing = engine_with(Mock(return_value=response(id=None)))
    with pytest.raises(GeminiInvalidOutputError):
        await missing.generate_structured("question", None, Answer, store=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["not-json", '{"wrong":"field"}', "null", ""])
async def test_invalid_output_is_error(value):
    engine = engine_with(Mock(return_value=response(value)))
    with pytest.raises(GeminiInvalidOutputError):
        await engine.generate_structured("question", None, Answer)
    assert engine.last_metadata is None


@pytest.mark.asyncio
async def test_missing_key_is_not_mock():
    engine = GeminiCoreEngine(config())
    with pytest.raises(GeminiConfigurationError):
        await engine.generate_structured("question", None, Answer)


@pytest.mark.asyncio
async def test_explicit_demo_label():
    cfg = config().model_copy(update={"ARLO_ENABLE_MOCKS": True})
    create = Mock(side_effect=AssertionError("No network in demo mode"))
    engine = GeminiCoreEngine(cfg, client=SimpleNamespace(interactions=SimpleNamespace(create=create)))
    result = await engine.generate_structured("label", image_bytes(), VisionExplainResult)
    assert result.headline_large.startswith("Demo data:")
    assert result.audio_script.startswith("Demo data.")
    assert engine.last_metadata.source == "demo"
    assert engine.last_metadata.interaction_id is None
    create.assert_not_called()
    with pytest.raises(GeminiConfigurationError):
        await engine.generate_structured("question", None, Answer)


@pytest.mark.asyncio
@pytest.mark.parametrize("status,error", [
    (401, GeminiAuthenticationError), (403, GeminiModelAccessError),
    (404, GeminiModelAccessError), (400, GeminiError), (500, GeminiError),
])
async def test_nonretryable_errors_are_sanitized(status, error):
    exc = RuntimeError("secret-key-and-private-image")
    exc.status_code = status
    create = Mock(side_effect=exc)
    engine = engine_with(create)
    with pytest.raises(error) as caught:
        await engine.generate_structured("question", None, Answer)
    assert "secret" not in str(caught.value)
    assert create.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [429, 503])
async def test_retry_exhaustion_and_backoff(status, monkeypatch):
    sleep = AsyncMock()
    monkeypatch.setattr("app.core.base_model.asyncio.sleep", sleep)
    exc = RuntimeError("sensitive")
    exc.code = status
    create = Mock(side_effect=exc)
    with pytest.raises(GeminiRetryExhaustedError):
        await engine_with(create).generate_structured("question", None, Answer)
    assert create.call_count == 3
    assert sleep.await_count == 2
    assert 1 <= sleep.await_args_list[0].args[0] <= 1.25
    assert 2 <= sleep.await_args_list[1].args[0] <= 2.25


@pytest.mark.asyncio
async def test_transient_failure_recovers(monkeypatch):
    monkeypatch.setattr("app.core.base_model.asyncio.sleep", AsyncMock())
    exc = RuntimeError("busy")
    exc.code = 503
    create = Mock(side_effect=[exc, response()])
    assert (await engine_with(create).generate_structured("q", None, Answer)).answer == "ok"
    assert create.call_count == 2


@pytest.mark.asyncio
async def test_sdk_runs_off_event_loop():
    caller = threading.get_ident()
    threads = []
    def create(**kwargs):
        threads.append(threading.get_ident())
        return response()
    await engine_with(create).generate_structured("question", None, Answer)
    assert threads[0] != caller


@pytest.mark.asyncio
async def test_metadata_is_per_task():
    def create(**kwargs):
        text = kwargs["input"][0]["text"]
        result = response()
        result.id = text
        return result
    engine = engine_with(create)
    async def generate(text):
        await engine.generate_structured(text, None, Answer)
        await asyncio.sleep(0)
        return engine.last_metadata.interaction_id
    assert await asyncio.gather(generate("one"), generate("two")) == ["one", "two"]
    assert engine.last_metadata is None


def sdk_client(transport):
    return genai.Client(
        api_key="test-placeholder",
        http_options={
            "httpx_client": httpx.Client(transport=transport),
            "retry_options": {"attempts": 0},
        },
    )


@pytest.mark.asyncio
async def test_real_sdk_serialization():
    requests = []
    def serve(request):
        requests.append(json.loads(request.content))
        assert request.url.path.endswith("/interactions")
        return httpx.Response(200, json={
            "id": "sdk-interaction-1", "status": "completed",
            "model": "gemini-4-argon",
            "steps": [{"type": "model_output", "content": [
                {"type": "text", "text": '{"answer":"sdk-ok"}'}
            ]}],
        })
    client = sdk_client(httpx.MockTransport(serve))
    try:
        engine = GeminiCoreEngine(config(), client=client)
        result = await engine.generate_structured("question", image_bytes(), Answer)
        assert result.answer == "sdk-ok"
        assert engine.last_metadata.interaction_id == "sdk-interaction-1"
        assert len(requests) == 1
        assert requests[0]["response_format"]["schema"]["properties"]["answer"]["type"] == "string"
        assert requests[0]["input"][0]["content"][1]["mime_type"] == "image/png"
    finally:
        client.close()


@pytest.mark.asyncio
async def test_real_sdk_does_not_multiply_retries(monkeypatch):
    monkeypatch.setattr("app.core.base_model.asyncio.sleep", AsyncMock())
    requests = []
    def serve(request):
        requests.append(request)
        return httpx.Response(503, json={"error": {"code": 503, "message": "private-text", "status": "UNAVAILABLE"}})
    client = sdk_client(httpx.MockTransport(serve))
    try:
        with pytest.raises(GeminiRetryExhaustedError):
            await GeminiCoreEngine(config(), client=client).generate_structured("q", None, Answer)
        assert len(requests) == 3
    finally:
        client.close()


def test_settings_mask_key_and_normalize_level():
    cfg = Settings(_env_file=None, GEMINI_API_KEY="test-secret", GEMINI_THINKING_LEVEL="MEDIUM")
    assert "test-secret" not in repr(cfg)
    assert cfg.GEMINI_THINKING_LEVEL == "medium"
