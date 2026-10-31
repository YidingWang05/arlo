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
2. **Memory Buy** - say, “the blue bottle my daughter bought”; Arlo resolves fuzzy attributes against household memory and shows exactly two large A/B candidates.
3. **Live Companion** - open a family photo, hear a short story, and interrupt playback naturally.
4. **Family Hub** - a relative can push a photo and caption into the frame feed.

The first two flows are the required vertical slice. Live voice and family sync are supporting features and must not destabilise the core demo.

## Architecture

~~~mermaid
flowchart LR
    U[Older adult] --> F[Accessible frame web app]
    R[Family member] --> F
    F -->|HTTP / WebSocket| API[FastAPI gateway]
    API --> M1[M1 Vision Explainer]
    API --> M2[M2 Memory Buy]
    API --> M3[M3 Live Companion]
    API --> M4[M4 Family Hub]
    M1 --> CORE[Gemini core engine]
    M2 --> CORE
    M3 --> CORE
    CORE -->|Interactions API| ARGON[Gemini 4 Argon]
    M2 --> MEM[Household memory store]
    M4 --> ALBUM[Frame album]
~~~

### Gemini integration contract

All Gemini 4 Argon calls must go through <code>app/core/base_model.py</code>.

- Use the current Google GenAI SDK and the **Interactions API**: <code>client.interactions.create(...)</code>.
- Use the stable model ID <code>gemini-4-argon</code>.
- Use <code>generation_config={"thinking_level": "low" | "medium" | "high"}</code>.
- Use a top-level <code>response_format</code> with each Pydantic model's JSON schema.
- Send images as base64 multimodal input with the correct MIME type.
- Do not pass <code>temperature</code>, <code>top_p</code>, <code>top_k</code>, <code>thinking_budget</code>, or explicit cached content to Argon.
- Validate every response with Pydantic before returning it to the UI.
- Never silently claim that a mock response came from Gemini. Mock mode must be visible and explicitly enabled.

Argon supports text, image, audio, video, and PDF input, but **does not support the Gemini Live API**. Module 3 therefore uses the application's WebSocket for transport and browser speech for the MVP. A future true real-time voice implementation may use <code>gemini-3.8-live</code> as a companion model while Argon remains the reasoning engine.

Official references:

- [Gemini 4 Argon model](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon)
- [Interactions API](https://ai.google.dev/gemini-api/docs/interactions-overview)
- [Structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- [Image understanding](https://ai.google.dev/gemini-api/docs/image-understanding)

## Modules and ownership

| Owner | Module | Primary paths | Hackathon deliverable |
| --- | --- | --- | --- |
| **Xiyu Chen** | Foundation engine and M1 Vision Explainer | <code>app/core/base_model.py</code>, <code>app/core/config.py</code>, <code>app/modules/m1_vision_tool.py</code>, <code>app/schemas/m1_vision.py</code> | Real Argon Interactions API integration, structured multimodal output, blur/safety behaviour, M1 tests and live smoke test |
| **Yiding Wang** | M2 Memory Buy and API gateway | <code>app/modules/m2_memory_tool.py</code>, <code>app/schemas/m2_memory_buy.py</code>, <code>app/api/routes.py</code>, <code>app/main.py</code> | Household memory data, fuzzy matching, exactly two candidates, validated FastAPI contracts and endpoint tests |
| **Kaiyu Feng** | Accessible frame frontend | <code>frontend/</code> | Full-screen frame UI, camera/upload flow, A/B cards, browser speech, error/loading states and production build |
| **Weihang You** | M3 Live Companion and pitch | <code>app/modules/m3_live_tool.py</code>, <code>tests/test_m3_live.py</code>, <code>docs/pitch/</code> | Interruptible WebSocket story stream, three-minute script, six-slide outline and judge Q&A |

The paste-ready Codex assignments are in [docs/team-prompts/](docs/team-prompts/).

## Repository layout

~~~text
arlo/
├── app/
│   ├── api/routes.py
│   ├── core/
│   │   ├── base_model.py
│   │   └── config.py
│   ├── modules/
│   │   ├── m1_vision_tool.py
│   │   ├── m2_memory_tool.py
│   │   ├── m3_live_tool.py
│   │   └── m4_frame_hub.py
│   ├── schemas/
│   └── main.py
├── docs/
│   └── team-prompts/
├── frontend/                  # created by the frontend owner
├── tests/                     # created by module owners
├── .env.example
├── requirements.txt
└── README.md
~~~

## API contracts

Base URL: <code>http://127.0.0.1:8000/api/arlo</code>

| Method | Path | Purpose | Request |
| --- | --- | --- | --- |
| <code>POST</code> | <code>/vision/explain</code> | Explain a label, medicine box, bill, or notice | multipart <code>file</code> plus optional <code>query</code> |
| <code>POST</code> | <code>/memory/buy</code> | Resolve a fuzzy household-product query | JSON <code>{"speech_query": "..."}</code> |
| <code>WS</code> | <code>/live/ws</code> | Stream story captions and interruption events | JSON WebSocket messages |
| <code>POST</code> | <code>/frame/photo-push</code> | Add a family photo and caption | <code>FamilyPhotoPush</code> JSON |
| <code>GET</code> | <code>/frame/photos</code> | Read the frame album | none |

### Vision response

~~~json
{
  "code": 200,
  "message": "success",
  "data": {
    "category": "MEDICINE",
    "headline_large": "Take one tablet after breakfast",
    "audio_script": "The visible label says to take one tablet after breakfast.",
    "action_items": ["Take one tablet", "Take after breakfast"],
    "is_blurry": false
  }
}
~~~

### Memory Buy request

~~~json
{
  "speech_query": "Show me the blue bottle my daughter bought"
}
~~~

The response must contain exactly two <code>CandidateItem</code> objects so that the UI can render one A/B decision.

## Prerequisites

- Python 3.10 or newer
- Git
- A Gemini API key with <code>gemini-4-argon</code> access
- Node.js 20 or newer for the frontend

The event account is temporary. Export code and assets before the account is removed, and never commit its password or API key.

## Backend setup

~~~bash
git clone https://github.com/YidingWang05/arlo.git
cd arlo

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cp .env.example .env
~~~

Edit <code>.env</code>:

~~~dotenv
GEMINI_API_KEY=replace_with_the_event_api_key
GEMINI_MODEL_NAME=gemini-4-argon
GEMINI_THINKING_LEVEL=low
APP_PORT=8000
~~~

Do not put the key in frontend code. Do not commit <code>.env</code>.

Run the API:

~~~bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
~~~

Open:

- API status: <http://127.0.0.1:8000/>
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

## API examples

Vision:

~~~bash
curl -X POST http://127.0.0.1:8000/api/arlo/vision/explain +  -F "file=@samples/medicine.jpg" +  -F "query=Please explain only the instructions visible on this label"
~~~

Memory Buy:

~~~bash
curl -X POST http://127.0.0.1:8000/api/arlo/memory/buy +  -H "Content-Type: application/json" +  -d '{"speech_query":"the blue bottle my daughter bought"}'
~~~

Frame photos:

~~~bash
curl http://127.0.0.1:8000/api/arlo/frame/photos
~~~

## Frontend setup

The frontend owner creates the Vite/React app under <code>frontend/</code>. After it is merged:

~~~bash
cd frontend
npm install
cp .env.example .env
npm run dev
~~~

Expected frontend environment:

~~~dotenv
VITE_ARLO_API_BASE=http://127.0.0.1:8000/api/arlo
~~~

Open <http://127.0.0.1:5173>. The browser never receives <code>GEMINI_API_KEY</code>; it talks only to FastAPI.

## Tests and acceptance checks

Backend:

~~~bash
pytest -q
~~~

Frontend:

~~~bash
cd frontend
npm run build
~~~

Minimum acceptance criteria:

- the root endpoint and Swagger UI load;
- a real API-key smoke test returns a non-empty Argon interaction ID;
- M1 accepts JPEG/PNG, returns valid <code>VisionExplainResult</code>, and asks for a new photo when the image is unreadable;
- M1 never invents dosage or presents itself as medical advice;
- M2 always returns exactly two candidates from the household store;
- API errors are visible and never silently replaced by a fake “success” response;
- the frontend completes both core flows without exposing the API key;
- the browser speech can be stopped immediately;
- <code>pytest -q</code> and <code>npm run build</code> pass before the demo.

## Accessibility and safety

- Core takeaways use at least 48 px type; supporting captions use at least 32 px.
- Touch targets are at least 64 x 64 px and are operable by keyboard.
- No screen presents more than two primary decisions.
- Colour is never the only way information is communicated.
- Spoken output has visible captions and a stop control.
- If a medicine label is blurry, incomplete, or ambiguous, Arlo asks for a clearer image and recommends checking with a pharmacist or clinician.
- Arlo reports only text visible in the supplied image; it does not diagnose, recommend a different dose, or infer missing instructions.
- Images and household data remain in memory for the MVP and must not be logged as raw base64.

## Two-hour delivery plan

The scope is deliberately narrow. Do not add authentication, databases, deployment automation, or a new agent framework during the two-hour build.

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

## Demo fallback strategy

The live path is the primary demo. Keep a clearly labelled demo mode only for network or quota failure:

- preserve the same schemas and UI states;
- display a visible “Demo data - Gemini unavailable” banner;
- never claim mock output came from Argon;
- keep one short screen recording as a final fallback.

## Troubleshooting

### 401 or 403

Check that the event account's API key belongs to the imported paid project and has Argon access.

### 404 model not found

Confirm <code>GEMINI_MODEL_NAME=gemini-4-argon</code> and upgrade <code>google-genai</code>.

### 429 quota or spend cap

Check the AI Studio usage/spend page. Do not create unbounded retries. Use exponential backoff and a maximum attempt count.

### 503 model overloaded

Retry with jitter. For non-judged auxiliary work, <code>gemini-3.8-flash</code> may be used as a documented fallback; the main judged reasoning flow should remain Argon.

### Frontend cannot reach the API

Check the Vite API base URL, ensure FastAPI is listening on port 8000, and inspect the browser console and CORS settings.

## Current status

The repository began as a backend scaffold with Pydantic contracts and mock fallbacks. The hackathon implementation is complete only when the acceptance checks above pass with a real event API key. The README intentionally distinguishes planned behaviour from verified behaviour so the team does not confuse a mock response with a working Gemini integration.

## Licence and data

Hackathon prototype. Add an explicit licence before external reuse. Use only images and personal data that the team is authorised to process.
