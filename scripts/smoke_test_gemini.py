"""One explicit live probe; never falls back to mocks.

Run from any directory: python scripts/smoke_test_gemini.py
Optional image probe: python scripts/smoke_test_gemini.py --image sample.png
The text-only probe is stored so it returns a verifiable interaction ID. Image
probes remain stateless and print no image or label content.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import BaseModel

from app.core.base_model import GeminiCoreEngine, GeminiError
from app.core.config import Settings
from app.modules.m1_vision_tool import SYSTEM_PROMPT
from app.schemas.m1_vision import VisionExplainResult


class ProbeResult(BaseModel):
    status: Literal["ready"]


async def probe(image_path: str | None = None) -> int:
    config = Settings()
    if not config.has_api_key:
        print("FAIL: GEMINI_API_KEY is not configured; no request sent.")
        return 2
    config = config.model_copy(update={
        "ARLO_ENABLE_MOCKS": False, "GEMINI_MODEL_NAME": "gemini-4-argon",
    })
    engine = GeminiCoreEngine(config)
    try:
        if image_path:
            await engine.generate_structured(
                "Explain only the visible label.", Path(image_path).read_bytes(),
                VisionExplainResult, system_instruction=SYSTEM_PROMPT,
            )
        else:
            await engine.generate_structured(
                'Return JSON with status exactly "ready".', None, ProbeResult,
                store=True,
            )
        metadata = engine.last_metadata
        if metadata is None or metadata.source != "gemini":
            print("FAIL: no verified Gemini interaction metadata.")
            return 1
        if not image_path and not metadata.interaction_id:
            print("FAIL: stored probe returned no interaction ID.")
            return 1
        interaction_id = metadata.interaction_id or "not-stored"
        print(f"PASS model={metadata.model} interaction_id={interaction_id} "
              f"latency_seconds={metadata.latency_seconds:.3f}")
        return 0
    except GeminiError as exc:
        print(f"FAIL {type(exc).__name__}: {exc}")
        return 1
    except Exception:
        print("FAIL: could not complete the probe; check SDK, configuration and image path.")
        return 1
    finally:
        if engine.client is not None:
            engine.client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", help="Optional JPEG, PNG or WEBP label image")
    args = parser.parse_args()
    try:
        sys.exit(asyncio.run(probe(args.image)))
    except Exception:
        print("FAIL: invalid configuration; no credentials displayed.")
        sys.exit(1)
