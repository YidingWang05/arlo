import asyncio
import pytest
from pydantic import ValidationError
from app.modules import m2_memory_tool as m2
from app.schemas.m2_memory_buy import MemoryBuyResult


@pytest.fixture(autouse=True)
def engine(monkeypatch):
    async def extract(*args):
        return m2.MemoryAttributes(colours=["blue"], purchased_by="daughter")
    monkeypatch.setattr(m2.gemini_engine, "generate_structured", extract)


def run(query):
    return asyncio.run(m2.run_memory_buy(query))


def test_blue_daughter():
    result = run("the blue bottle my daughter bought")
    assert len(result.candidates) == 2
    assert result.candidates[0].item_id == "flash"
    assert len({c.item_id for c in result.candidates}) == 2
    assert all(c.item_id in {i["item_id"] for i in m2.HOUSEHOLD_ITEMS} for c in result.candidates)


def test_brand_wins():
    assert run("blue Persil bottle").candidates[0].item_id == "persil"


@pytest.mark.parametrize("raw", [{"colours": 5}, {"invented": "product"}, {}])
def test_invalid_or_empty_extraction(monkeypatch, raw):
    async def extract(*args):
        return raw
    monkeypatch.setattr(m2.gemini_engine, "generate_structured", extract)
    result = run("blue bottle my daughter bought")
    assert result.candidates[0].item_id == "flash"
    assert "keyword matching" in result.spoken_prompt
    unknown = run("something from outer space")
    assert "closest matches" in unknown.spoken_prompt
    assert len(unknown.candidates) == 2


def test_schema_disallows_duplicates_and_wrong_count():
    candidate = run("blue").candidates[0]
    for candidates in ([candidate], [candidate, candidate], [candidate] * 3):
        with pytest.raises(ValidationError):
            MemoryBuyResult(spoken_prompt="A or B?", candidates=candidates)


def test_synonyms_and_repeatability():
    assert run("NAVY bottle daughter") == run("navy bottle daughter")


def test_engine_failure(monkeypatch):
    async def fail(*args):
        raise ConnectionError("offline")
    monkeypatch.setattr(m2.gemini_engine, "generate_structured", fail)
    assert "keyword matching" in run("blue daughter").spoken_prompt
