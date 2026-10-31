# Arlo

> A multimodal, human-centred everyday living assistant for older adults.
>
> Google DeepMind / Gemini Hackathon - Track 2: Multimodal & Human-Centric AI
>
> Foundation reasoning model: Gemini 4 Argon (<code>gemini-4-argon</code>)

Arlo turns a familiar digital photo frame into a calm, accessible assistant. An older adult can show Arlo a medicine label or household bill, describe a product they cannot remember, browse family photos, and hear a clear spoken response without navigating a conventional smartphone interface.

The hackathon MVP combines camera understanding, structured Gemini output, family context, large-print interaction, and human confirmation. It is an assistive prototype, not a medical device.

## The problem

Many older adults encounter four related barriers:

- medicine labels, bills, and notices use small type and complex language;
- household products are often remembered by colour, shape, or who bought them rather than by exact brand;
- important family context is spread across messaging apps and photo libraries;
- mainstream interfaces present too many controls, small targets, and unclear states.

Arlo is designed around one principle: **one understandable decision at a time**.

## What the MVP demonstrates

The three-minute demo should show one continuous story:

1. **Vision Explainer** - upload or capture a medicine label; Arlo extracts only visible instructions and presents a short large-print takeaway plus a warm spoken explanation.
2. **Memory Buy** - type or, when browser speech recognition is available, say “the blue bottle my daughter bought”; Arlo matches clues against a ten-item sample household catalogue and shows exactly two large A/B candidates.
3. **Live Companion** - start a short caption-based photo story, stop it with the Stop control or Escape, and ask a text question after playback finishes or stopping is acknowledged. Captions and browser speech accompany the reply.
4. **Family Hub** - push a photo URL, sender name and caption through the backend API, then refresh the frame to load the updated album. There is currently no family photo-upload screen.

The first two flows are the required vertical slice. The implemented story flow is application-level text streaming with browser speech, and the family album is an in-memory prototype. Neither the product catalogue nor the album is a production family-memory service.

## Architecture

~~~mermaid
flowchart LR
    U[Older adult] --> F[Accessible frame web app]
    R[Family member] -->|Photo-push API| API
    F -->|HTTP / WebSocket| API[FastAPI gateway]
    API --> M1[M1 Vision Explainer]
    API --> M2[M2 Memory Buy]
    API --> M3[M3 Live Companion]
    API --> M4[M4 Family Hub]
    M1 --> CORE[Gemini core engine]
    M2 --> CORE
    M3 --> CORE
    CORE -->|Interactions API| ARGON[Gemini 4 Argon]
    M2 --> MEM[Sample household catalogue]
    M4 --> ALBUM[In-memory frame album]
~~~

### Gemini integration contract

All Gemini 4 Argon calls must go through <code>app/core/base_model.py</code>.

- Use <code>google-genai&gt;=2.34.0,&lt;3</code> and the **Interactions API**: <code>client.interactions.create(...)</code>. The shared engine runs synchronous SDK requests in a worker thread.
- Use the stable model ID <code>gemini-4-argon</code>.
- Use <code>generation_config={"thinking_level": "low" | "medium" | "high"}</code>.
- Use a top-level <code>response_format</code> with each Pydantic model's JSON schema.
- Send images as base64 multimodal input with the correct MIME type.
- Do not pass <code>temperature</code>, <code>top_p</code>, <code>top_k</code>, <code>thinking_budget</code>, or explicit cached content to Argon.
- Validate every response with Pydantic before returning it to the UI.
- Never silently claim that a mock response came from Gemini. Mock mode must be visible and explicitly enabled.
- Normal application calls use <code>store=false</code>. A successful stateless response may omit its interaction ID; do not treat a null ID alone as a failed or mock result.
- M3 uses the shared <code>generate_text()</code> helper and requires the configured Argon model with <code>low</code> thinking. It receives caption text and the current question, not photo pixels or an accumulated conversation transcript.

Argon supports text, image, audio, video, and PDF input, but **does not support the Gemini Live API**. Module 3 therefore uses the application's WebSocket for transport and browser speech for the MVP. Stop and Escape are implemented; microphone-triggered voice interruption is not. A future true real-time voice implementation may use <code>gemini-3.8-live</code> as a companion model while Argon remains the reasoning engine.

Official references:

- [Gemini 4 Argon model](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon)
- [Interactions API](https://ai.google.dev/gemini-api/docs/interactions)
- [Structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- [Image understanding](https://ai.google.dev/gemini-api/docs/image-understanding)

## Modules and ownership

| Owner | Module | Primary paths | Hackathon deliverable |
| --- | --- | --- | --- |
| **Xiyu Chen** | Foundation engine and M1 Vision Explainer | <code>app/core/base_model.py</code>, <code>app/core/config.py</code>, <code>app/modules/m1_vision_tool.py</code>, <code>app/schemas/m1_vision.py</code> | Real Argon Interactions API integration, structured multimodal output, blur/safety behaviour, M1 tests and live smoke test |
| **Yiding Wang** | M2 Memory Buy and API gateway | <code>app/modules/m2_memory_tool.py</code>, <code>app/schemas/m2_memory_buy.py</code>, <code>app/api/routes.py</code>, <code>app/main.py</code> | Household memory data, fuzzy matching, exactly two candidates, validated FastAPI contracts and endpoint tests |
| **Kaiyu Feng** | Accessible frame frontend | <code>frontend/</code> | Full-screen frame UI, camera/upload flow, A/B cards, browser speech, error/loading states and production build |
| **Weihang You** | M3 Live Companion and pitch | <code>app/modules/m3_live_tool.py</code>, <code>tests/test_m3_live.py</code>, <code>docs/pitch/</code> | Interruptible story stream, caption-based text follow-ups, frontend protocol integration, three-minute script, six-slide outline and judge Q&A |

The paste-ready Codex assignments are in [docs/team-prompts/](docs/team-prompts/).

## Repository layout

~~~text
arlo/
├── app/
│   ├── api/routes.py
│   ├── core/
│   │   ├── base_model.py
│   │   └── config.py
│   ├── data/household_memory.py # ten sample products and generated illustrations
│   ├── modules/
│   │   ├── m1_vision_tool.py
│   │   ├── m2_memory_tool.py
│   │   ├── m3_live_tool.py
│   │   └── m4_frame_hub.py
│   ├── schemas/
│   └── main.py
├── docs/
│   ├── team-prompts/
│   └── pitch/                 # demo script, slide outline and judge Q&A
├── frontend/                  # implemented Vite/React client
├── scripts/smoke_test_gemini.py
├── tests/                     # offline backend contract tests
├── .env                       # create locally; ignored by Git
├── requirements.txt
└── README.md
~~~

## API contracts

Base URL: <code>http://127.0.0.1:8000/api/arlo</code>

| Method | Path | Purpose | Request |
| --- | --- | --- | --- |
| <code>POST</code> | <code>/vision/explain</code> | Explain a label, medicine box, bill, or notice | multipart <code>file</code> plus optional <code>query</code> |
| <code>POST</code> | <code>/memory/buy</code> | Resolve a fuzzy household-product query | JSON <code>{"speech_query": "..."}</code> |
| <code>GET</code> | <code>/memory/images/{item_id}</code> | Serve a sample product's SVG illustration | known catalogue item ID |
| <code>WS</code> | <code>/live/ws</code> | Stream story captions and interruption events | JSON WebSocket messages |
| <code>POST</code> | <code>/frame/photo-push</code> | Add a family photo and caption | <code>FamilyPhotoPush</code> JSON |
| <code>GET</code> | <code>/frame/photos</code> | Read the frame album | none |

### Vision response

Illustrative successful response; actual label text and safety wording depend on the supplied image. The shared response envelope includes server-provided provenance:

~~~json
{
  "code": 200,
  "message": "success",
  "data": {
    "category": "MEDICINE",
    "headline_large": "Take one tablet after breakfast",
    "audio_script": "The visible label says to take one tablet after breakfast.",
    "action_items": ["Take one tablet", "Take after breakfast"],
    "is_blurry": false,
    "source": "gemini"
  },
  "meta": {
    "source": "gemini",
    "model": "gemini-4-argon",
    "interaction_id": null,
    "is_mock": false
  }
}
~~~

### Memory Buy request

~~~json
{
  "speech_query": "Show me the blue bottle my daughter bought"
}
~~~

The response contains exactly two distinct <code>CandidateItem</code> objects so the UI can render one A/B decision. Candidate images are served by the backend's <code>/memory/images/{item_id}</code> endpoint.

The ten catalogue entries are developer-seeded rows in <code>app/data/household_memory.py</code>. They are not uploaded by users or retrieved from an online shop. Each row manually supplies an item ID/brand, name, category, colour, shape, example purchaser and purchase date. Code derives <code>brand_hint</code>, <code>display_tag</code> and a labelled SVG illustration. These are sample records, not verified purchase history. There is no product-upload, automatic product-image tagging or catalogue-editing API in this MVP.

Argon extracts structured clues from <code>speech_query</code>. Explicit catalogue terms in the input override the corresponding inferred attributes. The matcher scores brand, category, colour, shape, purchaser and keywords, then breaks ties by the sample purchase date and item ID. If extraction fails or returns no clues, it falls back to keyword matching and labels the response accordingly. To change the demo inventory, edit the catalogue rows and restart the backend; changing a search description alone does not add or modify products.

**Live Companion message flow:** connect to <code>ws://127.0.0.1:8000/api/arlo/live/ws</code> and retain the <code>session_id</code> from <code>SESSION_READY</code>.

| Client message | Fields / behaviour |
| --- | --- |
| <code>START_STORY</code> | <code>photo_id</code>, <code>caption</code>, optional <code>user_prompt</code>, and the current <code>session_id</code>; establishes photo context |
| <code>USER_TEXT</code> | <code>text</code> and <code>session_id</code>; asks about that caption after completion or stop acknowledgement |
| <code>INTERRUPT</code> | <code>session_id</code>; cancels delivery and returns <code>PLAYBACK_STOP</code> |
| <code>PING</code> | returns <code>PONG</code> |

Each response turn emits <code>STORY_STARTED</code>, ordered <code>CAPTION_CHUNK</code> messages with sequence numbers starting at 1, then <code>STORY_COMPLETE</code>. Turns have distinct <code>story_id</code> values. Completion identifies <code>source</code> as <code>argon</code> or <code>demo</code>; Argon completion also supplies <code>model</code> and an optional/null <code>interaction_id</code>. HTTP provenance uses <code>meta.source="gemini"</code>, while the story protocol uses <code>source="argon"</code>. Errors use <code>ERROR</code> with safe text and, for story operations, codes such as <code>PHOTO_REQUIRED</code>, <code>STORY_BUSY</code>, <code>STORY_TIMEOUT</code> and <code>STORY_UNAVAILABLE</code>.

The client retains its connection for follow-ups and clears the context when changing photos, leaving the frame or unmounting. Stop immediately cancels browser speech and clears queued utterances before waiting for the backend acknowledgement. Stories are fewer than 90 words; the question mode requests a concise direct answer. The server rejects messages above 16 KiB and bounds captions/questions. Cancelling delivery cannot terminate a synchronous Google SDK request already running in its worker thread.

All successful HTTP envelopes include <code>meta</code>; possible sources are <code>gemini</code>, <code>demo</code>, <code>keyword</code>, <code>local</code> and <code>unverified</code>. M2's Gemini source describes clue extraction; its catalogue remains sample data. Shared service errors are mapped to HTTP 400 for invalid input, 502 for invalid output, or 503 for configuration, authentication, model-access and exhausted-retry failures. See [API provenance](docs/api-provenance.md) for details.

## Prerequisites

- Python 3.10 or newer
- Git
- A Gemini API key with <code>gemini-4-argon</code> access
- Node.js 22.12 or newer for the frontend, as required by <code>frontend/package.json</code>

The event account is temporary. Export code and assets before the account is removed, and never commit its password or API key.

## Backend setup

~~~bash
git clone https://github.com/YidingWang05/arlo.git
cd arlo

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

touch .env
~~~

On Windows PowerShell, use the following instead (no activation is required):

~~~powershell
git clone https://github.com/YidingWang05/arlo.git
cd arlo
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { New-Item -ItemType File -Path .env | Out-Null }
~~~

Create/edit the repository-root <code>.env</code> locally. The former backend <code>.env.example</code> has been removed; it is not needed to configure the application:

~~~dotenv
GEMINI_API_KEY=replace_with_the_event_api_key
GEMINI_MODEL_NAME=gemini-4-argon
GEMINI_THINKING_LEVEL=low
ARLO_ENABLE_MOCKS=false
APP_PORT=8000
~~~

Do not put the key in frontend code or any <code>VITE_*</code> variable. Do not commit <code>.env</code>. Git does not distribute teammates' ignored environment files. Restart the backend after changing its environment; all modules use the shared key.

Run the API:

~~~bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
~~~

On Windows, run <code>.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload</code>. These explicit CLI options select the host/port; changing <code>APP_PORT</code> alone does not alter this command.

Open:

- API status: <http://127.0.0.1:8000/>
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

## API examples

Vision:

~~~bash
curl -X POST http://127.0.0.1:8000/api/arlo/vision/explain \
  -F "file=@/path/to/your-authorised-label.jpg" \
  -F "query=Please explain only the instructions visible on this label"
~~~

Memory Buy:

~~~bash
curl -X POST http://127.0.0.1:8000/api/arlo/memory/buy \
  -H "Content-Type: application/json" \
  -d '{"speech_query":"the blue bottle my daughter bought"}'
~~~

Frame photos:

~~~bash
curl http://127.0.0.1:8000/api/arlo/frame/photos
~~~

The examples above use Bash syntax. On Windows, Swagger UI is a convenient way to supply a local image or try <code>/frame/photo-push</code>; the push endpoint accepts an existing image URL, sender name and caption, not a binary image upload. New photos are visible after refreshing the frame, and the in-memory album resets when the server restarts.

## Frontend setup

The Vite/React app is implemented under <code>frontend/</code>. In a second terminal:

~~~bash
cd frontend
npm ci
cp .env.example .env
npm run dev
~~~

The frontend copy command uses <code>frontend/.env.example</code>, which still exists. Its environment file is optional when using the default local API address. Expected frontend environment:

~~~dotenv
VITE_ARLO_API_BASE=http://127.0.0.1:8000/api/arlo
~~~

Open <http://127.0.0.1:5173>. The browser never receives <code>GEMINI_API_KEY</code>; it talks only to FastAPI. The photo frame includes Start a story, Stop and Ask about this photo. You can draft a question while a story plays, but send it only after completion or stop acknowledgement. The Ask Arlo control opens label explanation and product search.

## Tests and acceptance checks

Backend:

~~~bash
python -m pytest -q
python -m compileall -q app tests scripts
~~~

Frontend:

~~~bash
cd frontend
npm test
npm run build
~~~

Run the separate local HTTP/WebSocket integration checks from <code>frontend/</code>:

~~~bash
ARLO_TEST_PYTHON=../.venv/bin/python npm run test:integration
~~~

On Windows PowerShell:

~~~powershell
$env:ARLO_TEST_PYTHON = "../.venv/Scripts/python.exe"
npm run test:integration
~~~

These integration checks start isolated servers with explicit test providers and no API key. Normal <code>npm test</code> skips them; running <code>test:integration</code> executes them separately. See [integration instructions](frontend/INTEGRATION_TESTING.md). Offline tests do not prove real-model accuracy or live credentials.

For one intentional live connection check, run <code>python scripts/smoke_test_gemini.py</code> from the activated backend environment, or <code>.\.venv\Scripts\python.exe scripts/smoke_test_gemini.py</code> on Windows. It refuses to run without a key. Its fixed, non-sensitive readiness probe opts into storage to verify an interaction ID; normal application image/story calls remain stateless. An optional <code>--image /path/to/image.png</code> probe tests a real image using <code>store=false</code>.

Minimum acceptance criteria:

- the root endpoint and Swagger UI load;
- the explicit readiness smoke test passes with the real event key; successful stateless application calls may have a null interaction ID;
- M1 accepts JPEG/PNG/WEBP up to 10 MB, returns valid <code>VisionExplainResult</code>, and asks for a new photo when the image is unreadable;
- M1's live output is checked against the visible label for unsupported dosage or advice; automated safeguards are not clinical validation;
- M2 always returns exactly two candidates from the household store;
- API errors are visible and never silently replaced by a fake “success” response;
- the frontend completes both core flows without exposing the API key;
- the browser speech can be stopped immediately;
- M3 starts a caption-based story, stops remaining captions, restarts, and accepts a question after completion/stop without reusing stale speech;
- <code>python -m pytest -q</code>, <code>npm test</code>, <code>npm run test:integration</code> and <code>npm run build</code> pass before the demo.

## Accessibility and safety

- Core takeaways use at least 48 px type; supporting captions use at least 32 px.
- Touch targets are at least 64 x 64 px and are operable by keyboard.
- The core task chooser and product result use a two-choice design; story controls and the follow-up form have separate start/stop/send states.
- Colour is never the only way information is communicated.
- Spoken output has visible captions and a stop control.
- If a medicine label is blurry, incomplete, or ambiguous, Arlo asks for a clearer image and recommends checking with a pharmacist or clinician.
- Arlo reports only text visible in the supplied image; it does not diagnose, recommend a different dose, or infer missing instructions.
- Uploaded images are handled transiently by the application, photo-album state is in memory, and the sample product catalogue is stored in code. Relevant input is sent to Google for real model calls; do not claim processing is entirely on-device. Normal calls use <code>store=false</code>, and raw prompts/images must not be logged.
- Accessibility settings and automated UI tests are implemented; a formal accessibility audit and evaluation with older adults are still pending. M3 uses only the supplied caption, so it cannot independently identify people, objects or weather in the photo.

## Two-hour delivery plan

This is the original hackathon delivery plan, retained for team coordination. The current implementation status is recorded below. The scope remains deliberately narrow: authentication, databases, deployment automation and a new agent framework are outside this MVP.

| Time | Activity |
| --- | --- |
| 0:00-0:10 | Everyone pulls <code>main</code>, creates an owned branch, reads schemas, and freezes endpoint contracts |
| 0:10-1:05 | Four parallel implementations; each owner tests only their bounded module |
| 1:05-1:20 | Merge Xiyu's foundation engine first, then Yiding's API, Weihang's WebSocket/docs, and Kaiyu's frontend |
| 1:20-1:40 | End-to-end integration using one medicine image and one fuzzy shopping query |
| 1:40-1:55 | Fix only demo blockers; run backend tests and frontend production build |
| 1:55-2:00 | Freeze code, export assets, and start the rehearsed three-minute demo |

### Branches

~~~text
codex/xiyu-m1
codex/yiding-m2-api
codex/kaiyu-frontend
codex/weihang-m3-pitch
~~~

Each owner should commit only owned paths and report:

- branch and commit hash;
- files changed;
- commands run and their results;
- any API/schema change needed by another owner;
- one known limitation.

Push work to a feature branch and open a pull request for review. The repository owner/team performs merges; an assistant must not merge into <code>main</code> without a new explicit instruction.

## Demo fallback strategy

The live path is the primary demo. The current implementation has distinct, explicit demonstration paths:

- preserve the same schemas and UI states;
- the frontend's opt-in <code>Use demo data</code> switch displays “Demo data - backend unavailable” and returns fixed label/product examples without analysing the uploaded image;
- that frontend switch disables stories; it does not enable a fake live story. An explicitly injected server-side <code>demo_story_provider</code> can exercise M3 transport and is labelled “Demo story — not a live AI result”;
- <code>ARLO_ENABLE_MOCKS=true</code> enables the core's labelled M1 demo response; arbitrary story schemas are not supported by that fallback. M2 can separately return a visibly labelled keyword match;
- never claim mock output came from Argon;
- prepare an authorised, clearly identified screen recording before the event if a final fallback is needed; no recording is supplied by this repository.

## Troubleshooting

### 401 or 403

Check that the event account's API key belongs to the imported project and has Argon access. The shared engine exposes authentication/model-access failures to the UI as safe 503 errors; the underlying Google response may be 401 or 403.

### 404 model not found

Confirm <code>GEMINI_MODEL_NAME=gemini-4-argon</code>, project access and the SDK dependency in <code>requirements.txt</code>. A provider 404 is mapped to a safe model-access error.

### 429 quota or spend cap

Check the AI Studio usage/spend page. The shared engine retries provider 429 and 503 failures at most three times, with backoff and jitter; exhausted retries produce a safe service error.

### 503 model overloaded

The shared engine already applies bounded retries for provider 503 responses. M3 also has a 20-second delivery timeout. Model failures are not silently replaced by successful Gemini output, and there is no automatic model switch; M3 currently requires Argon with low thinking.

### Frontend cannot reach the API

Check the Vite API base URL, ensure FastAPI is listening on port 8000, and inspect the browser console and CORS settings.

## Current status

The repository now contains the shared Interactions engine, M1 label explanation, M2 sample-catalogue matching and served illustrations, M3 interruptible stories/text follow-ups, the in-memory M4 photo API, and the implemented frame frontend. Pitch drafts are in <code>docs/pitch/</code>; the timed script contains 363 main spoken words.

Development verification at the M3 question-mode checkpoint passed 135 backend tests, 54 frontend unit/UI tests, six separate local integration tests, and the frontend production build. A real configured-key M3 check verified generation, interruption and follow-up delivery; additional live questions confirmed direct caption-grounded answers. This is not a measured accuracy benchmark or proof that every presentation scene is ready. M1/M2 live end-to-end acceptance and the final timed rehearsal should be confirmed by their owners/presenter on the demonstration machine.

Known limits: no product-upload flow or online shopping search; catalogue purchasers/dates and illustrations are sample data; no persistent or authenticated family account; no frontend photo-push form or real-time album subscription; no microphone-triggered M3 interruption; and no photo-pixel understanding or accumulated conversation memory in M3. Keep the response-source labels visible, configure the ignored local <code>.env</code>, and run the acceptance checks for the revision being presented.

## Licence and data

Hackathon prototype. Add an explicit licence before external reuse. Use only images and personal data that the team is authorised to process.
