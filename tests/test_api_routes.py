import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api import routes
from app.modules import m2_memory_tool as m2
from app.modules.m4_frame_hub import FRAME_ALBUM


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
    assert set(body) == {"code", "message", "data"}
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
