import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api import routes
from app.modules import m2_memory_tool as m2
from app.modules.m4_frame_hub import FRAME_ALBUM
from app.core.base_model import GeminiInputError, GeminiConfigurationError, GeminiInvalidOutputError
from app.core.base_model import GenerationMetadata
from app.data.household_memory import HOUSEHOLD_ITEMS
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


def test_http_candidate_images(client):
    body = client.post("/api/arlo/memory/buy", json={"speech_query": "blue daughter"}).json()
    for candidate in body["data"]["candidates"]:
        assert urlparse(candidate["image_url"]).scheme in {"http", "https"}
        assert client.get(candidate["image_url"]).status_code == 200
    for item in HOUSEHOLD_ITEMS:
        response = client.get("/api/arlo/memory/images/" + item["item_id"])
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/svg+xml")
        ET.fromstring(response.text)
    assert client.get("/api/arlo/memory/images/unknown").status_code == 404


def test_memory_provenance_and_fallback(client, monkeypatch):
    async def extract(*args):
        m2.gemini_engine._metadata.set(GenerationMetadata("gemini", "gemini-4-argon", "test-interaction", 0.1))
        return m2.MemoryAttributes(colours=["blue"])
    monkeypatch.setattr(m2.gemini_engine, "generate_structured", extract)
    body = client.post("/api/arlo/memory/buy", json={"speech_query": "blue"}).json()
    assert body["meta"] == {"source": "gemini", "interaction_id": "test-interaction", "model": "gemini-4-argon", "is_mock": False}
    async def fail(*args):
        raise GeminiConfigurationError("Key unavailable")
    monkeypatch.setattr(m2.gemini_engine, "generate_structured", fail)
    body = client.post("/api/arlo/memory/buy", json={"speech_query": "blue"}).json()
    assert body["meta"]["source"] == "keyword"
    assert body["meta"]["interaction_id"] is None


@pytest.mark.parametrize("source,interaction", [("gemini", "test-id"), ("demo", None)])
def test_vision_provenance(client, monkeypatch, source, interaction):
    async def vision(*args):
        m2.gemini_engine._metadata.set(GenerationMetadata(source, "gemini-4-argon", interaction, 0))
        return dict(category="OTHER", headline_large="Test", audio_script="Test", action_items=[], is_blurry=False)
    monkeypatch.setattr(routes, "run_vision_explain", vision)
    body = client.post("/api/arlo/vision/explain", files={"file": ("test.png", b"fixture", "image/png")}).json()
    assert body["meta"]["source"] == source
    assert body["meta"]["interaction_id"] == interaction
    assert body["meta"]["is_mock"] == (source == "demo")


@pytest.mark.parametrize("error,status", [(GeminiInputError, 400), (GeminiConfigurationError, 503), (GeminiInvalidOutputError, 502)])
@pytest.mark.parametrize("endpoint", ["vision", "memory"])
def test_core_error_contract(client, monkeypatch, error, status, endpoint):
    async def fail(*args):
        raise error("Safe service message")
    if endpoint == "vision":
        monkeypatch.setattr(routes, "run_vision_explain", fail)
        response = client.post("/api/arlo/vision/explain", files={"file": ("test.png", b"fixture", "image/png")})
    else:
        monkeypatch.setattr(routes, "run_memory_buy", fail)
        response = client.post("/api/arlo/memory/buy", json={"speech_query": "blue"})
    assert response.status_code == status
    assert response.json() == {"detail": "Safe service message"}


@pytest.fixture
def client(monkeypatch):
    async def extract(*args):
        return m2.MemoryAttributes()
    monkeypatch.setattr(m2.gemini_engine, "generate_structured", extract)
    with TestClient(app) as client:
        yield client


def test_memory_contract(client):
    response = client.post("/api/arlo/memory/buy", json={"speech_query": " blue bottle my daughter bought "})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"code", "message", "data", "meta"}
    assert body["meta"]["source"] == "keyword"
    assert body["code"] == 200 and body["message"] == "success"
    assert set(body["data"]) == {"spoken_prompt", "candidates"}
    assert len(body["data"]["candidates"]) == 2
    assert set(body["data"]["candidates"][0]) == {"item_id", "name", "image_url", "display_tag"}


@pytest.mark.parametrize("query", ["", "   ", "x" * 1001])
def test_invalid_query(client, query):
    assert client.post("/api/arlo/memory/buy", json={"speech_query": query}).status_code == 422


@pytest.mark.parametrize("mime,data,status", [("text/plain", b"x", 400), ("image/png", b"", 400), ("image/jpeg", b"x" * (10 * 1024 * 1024 + 1), 413)])
def test_bad_upload(client, mime, data, status):
    assert client.post("/api/arlo/vision/explain", files={"file": ("upload", data, mime)}).status_code == status


@pytest.mark.parametrize("mime", ["image/jpeg", "image/png", "image/webp"])
def test_supported_upload(client, monkeypatch, mime):
    async def vision(image, query):
        return dict(category="OTHER", headline_large="Test", audio_script="Test", action_items=[], is_blurry=False)
    monkeypatch.setattr(routes, "run_vision_explain", vision)
    assert client.post("/api/arlo/vision/explain", files={"file": ("upload", b"fixture", mime)}).status_code == 200


@pytest.mark.parametrize("error,status", [(TimeoutError, 504), (ConnectionError, 503), (RuntimeError, 500)])
def test_service_errors(client, monkeypatch, error, status):
    async def fail(query):
        raise error("private details")
    monkeypatch.setattr(routes, "run_memory_buy", fail)
    response = client.post("/api/arlo/memory/buy", json={"speech_query": "blue"})
    assert response.status_code == status
    assert "private details" not in response.text


def test_root_openapi_and_cors(client):
    assert client.get("/").json()["foundation_model"]
    assert client.get("/openapi.json").status_code == 200
    for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        response = client.options("/api/arlo/memory/buy", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
        assert response.headers["access-control-allow-origin"] == origin


def test_frame(client):
    original = FRAME_ALBUM[:]
    try:
        response = client.post("/api/arlo/frame/photo-push", json={"image_url": "https://example.com/photo.jpg", "sender_name": "Daughter", "caption": "Hello"})
        assert response.json()["data"] is True
        assert client.get("/api/arlo/frame/photos").json()["data"][0]["caption"] == "Daughter: Hello"
    finally:
        FRAME_ALBUM[:] = original
