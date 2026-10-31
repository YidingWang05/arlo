# Codex Assignment - Xiyu Chen

Copy everything below into a new Codex task opened on the Arlo repository.

---

You are the senior AI engineer for Arlo, a Google DeepMind / Gemini Hackathon Track 2 project. We have less than 70 minutes for your isolated implementation and less than two hours for the full team integration.

Repository: https://github.com/YidingWang05/arlo  
Your branch: codex/xiyu-m1  
Foundation model: Gemini 4 Argon, model ID gemini-4-argon

## Outcome

Deliver a real, testable Gemini 4 Argon foundation engine and a safe M1 Vision Explainer. The current repository is only a scaffold: it calls the legacy models.generate_content API, uses an obsolete SDK minimum, passes deprecated sampling parameters, and silently returns mocks after API failures. Replace that behaviour with the current Interactions API and prove the real connection with a smoke test.

## Start safely

1. Run git status and preserve any existing teammate changes.
2. Pull main with fast-forward only, then create or switch to codex/xiyu-m1.
3. Read README.md, all schemas, app/core/base_model.py, app/core/config.py, app/modules/m1_vision_tool.py, and app/api/routes.py before editing.
4. Do not print, commit, or paste GEMINI_API_KEY.
5. If the Gemini API development skill is available, use it. Otherwise use only the current official documentation linked from README.md.

## Files you own

- app/core/base_model.py
- app/core/config.py
- app/modules/m1_vision_tool.py
- app/schemas/m1_vision.py, only when a schema constraint is necessary
- tests/test_core_gemini.py
- tests/test_m1_vision.py
- scripts/smoke_test_gemini.py
- requirements.txt and .env.example only for Gemini/test dependencies

Do not edit frontend/, M2, M3, frame hub, or pitch documents. If you need a route signature change, report it to Yiding instead of editing his file.

## Current Gemini API contract

Use google-genai 2.30.1 or newer and the Interactions API. The essential shape is:

~~~python
interaction = client.interactions.create(
    model="gemini-4-argon",
    input=[
        {"type": "text", "text": prompt},
        {
            "type": "image",
            "data": base64_image,
            "mime_type": mime_type,
        },
    ],
    generation_config={
        "thinking_level": "low",
        "max_output_tokens": 32768,
    },
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": ResponseModel.model_json_schema(),
    },
)
result = ResponseModel.model_validate_json(interaction.output_text)
~~~

Requirements:

- Use client.interactions.create, not client.models.generate_content.
- Use lower-case low, medium, or high for thinking_level.
- Do not send temperature, top_p, top_k, thinking_budget, or explicit cache parameters to Argon.
- Base64-encode inline images and detect JPEG, PNG, or WEBP MIME type from the bytes. Reject unsupported or empty files.
- Run the synchronous SDK call using asyncio.to_thread so the FastAPI event loop is not blocked.
- Use the top-level response_format shown above.
- Validate interaction.output_text with the supplied Pydantic model.
- Return or log the interaction ID and model name in safe metadata, but never log prompts containing personal data or raw base64.
- Provide bounded retry with exponential backoff and jitter for 429 and 503 only, maximum three attempts.
- Raise a clear typed exception on authentication, model access, invalid output, or exhausted retries.

## Mock policy

Mocks are allowed only when an explicit ARLO_ENABLE_MOCKS=true environment setting is present. If mocks are disabled and the key is missing or the API call fails, return a clear error; do not silently return a fake success. Add a source field or safe metadata if needed so the UI can label demo output. Preserve existing schemas unless coordination makes a change unavoidable.

## M1 Vision Explainer behaviour

Implement run_vision_explain with a strong system instruction and structured output:

- classify MEDICINE, BILL, NOTICE, or OTHER;
- extract only text and instructions visibly supported by the image;
- never infer a dose, condition, drug interaction, or diagnosis;
- when the label is blurry, incomplete, reflective, cropped, or ambiguous, set is_blurry=true, ask for a clearer image, and avoid dosage claims;
- headline_large must contain no more than 15 plain-English words;
- audio_script must be warm, short, and suitable for browser speech;
- action_items must contain at most three concrete items;
- for medicine, state that the user should check the original label or a pharmacist if uncertain;
- do not call this “clinical reasoning” in the user-facing response.

The response must validate as VisionExplainResult.

## Tests

Create deterministic tests that do not spend API credits:

- successful structured response parsing with a mocked Interactions client;
- JPEG and PNG MIME detection;
- malformed JSON raises the correct error;
- missing API key fails when mocks are off;
- mock mode is explicit and labelled;
- blurry response contains no invented dose;
- headline is at most 15 words;
- run_vision_explain returns VisionExplainResult.

Use pytest and pytest-asyncio. Do not make normal test runs depend on the network.

Create scripts/smoke_test_gemini.py for one intentional live call. It must:

- refuse to run without GEMINI_API_KEY;
- call gemini-4-argon using client.interactions.create;
- request a tiny structured response;
- print PASS, the interaction ID, model ID, and latency;
- never print the key;
- exit non-zero on failure.

Run it once only if a key is already configured locally. Never invent or request the key in chat.

## Commands to verify

~~~bash
python -m compileall app tests scripts
pytest -q tests/test_core_gemini.py tests/test_m1_vision.py
python scripts/smoke_test_gemini.py
~~~

The final live command is conditional on a configured event key. Report it as not run if no key is present.

## Definition of done

- real API path uses gemini-4-argon through Interactions API;
- no deprecated Argon parameters remain;
- structured output validates through Pydantic;
- API failures are not disguised as successful Gemini output;
- M1 safety and blur behaviour are tested;
- offline tests pass;
- live smoke test passes with the event key, or is clearly reported as pending;
- changes are committed to codex/xiyu-m1.

## Handoff

Reply with:

1. branch and commit hash;
2. exact files changed;
3. test commands and results;
4. live smoke-test result and interaction ID, without secrets;
5. the public method signature Yiding and Weihang should call;
6. one known limitation.

Do not continue adding features after the definition of done is satisfied.
