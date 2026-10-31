# Codex Assignment - Kaiyu Feng

Copy everything below into a new Codex task opened on the Arlo repository.

---

You are Arlo's lead frontend and accessibility engineer for the Google DeepMind / Gemini Hackathon Track 2. We have less than 70 minutes for your isolated implementation and less than two hours until the live demo.

Repository: https://github.com/YidingWang05/arlo  
Your branch: codex/kaiyu-frontend  
Backend base URL: http://127.0.0.1:8000/api/arlo

## Outcome

Create a polished, full-screen React/Vite smart photo-frame client that makes the two core demo flows work end to end:

1. upload or capture a medicine-label image and show a large-print Vision Explainer result;
2. enter or speak a fuzzy shopping request and show exactly two large A/B product cards.

Also include a simple ambient photo mode and browser speech playback. Optimise for a reliable three-minute demo, not a large product.

## Start safely

1. Run git status and preserve any existing teammate changes.
2. Pull main with fast-forward only, then create or switch to codex/kaiyu-frontend.
3. Read README.md and the schemas under app/schemas before coding.
4. Create all work under frontend/. Do not edit backend files.
5. Never put GEMINI_API_KEY, the temporary account password, or any Google credential in frontend code or a VITE environment variable.

## Files you own

- frontend/package.json and package lock
- frontend/index.html
- frontend/src/
- frontend/tailwind and Vite configuration
- frontend/.env.example
- optional frontend/public/demo-assets/ using only assets the team is authorised to use

Do not edit app/, tests for backend modules, or pitch documents.

## Technical baseline

Use:

- Vite;
- React;
- Tailwind CSS;
- native fetch;
- native window.speechSynthesis;
- no state-management library;
- no component library unless already present.

Create a reusable component named ArloFrameApp and mount it from the standard Vite entry point. Keep the implementation small enough to debug quickly.

Read the API base URL from:

~~~dotenv
VITE_ARLO_API_BASE=http://127.0.0.1:8000/api/arlo
~~~

## Backend contracts

Vision:

- POST /vision/explain
- multipart/form-data
- field file: JPEG, PNG, or WEBP
- field query: text
- successful result is response.data with:
  - category
  - headline_large
  - audio_script
  - action_items
  - is_blurry

Memory Buy:

- POST /memory/buy
- Content-Type: application/json
- body: {"speech_query": "..."}
- successful result is response.data with:
  - spoken_prompt
  - candidates, exactly two
  - each candidate contains item_id, name, image_url, and display_tag

Frame album:

- GET /frame/photos
- response.data is an array of photos

Handle non-2xx responses, invalid JSON, missing data, timeouts, and offline backend. Never show a fake successful Gemini result without a visible “Demo data” label.

## Required UI states

### Ambient mode

- full-screen family photo;
- clock and short caption;
- slow optional rotation between available family photos;
- one obvious “Ask Arlo” control;
- no busy dashboard.

### Inspector home

Show only two primary choices:

- “Explain this label”
- “Help me find a product”

Each target must be at least 64 by 64 px and keyboard operable.

### Vision flow

- camera capture input on supported mobile devices and ordinary file upload fallback;
- local image preview;
- one clear submit button;
- loading state that says what Arlo is doing;
- headline_large rendered at 48 px or larger;
- action items rendered at 32 px or larger;
- Speak and Stop speaking controls;
- clear retake state when is_blurry is true;
- visible error with Retry and Back controls.

### Memory Buy flow

- large text input and optional Web Speech recognition only if the browser provides it;
- example text “the blue bottle my daughter bought”;
- exactly two equal A/B cards;
- large image, product name, and display tag;
- selecting a card gives one unambiguous confirmation state;
- never display a long candidate list.

## Accessibility requirements

- semantic landmarks, headings, buttons, labels, and status regions;
- core takeaway at least 48 px;
- supporting text at least 32 px where the design permits;
- high contrast and visible focus;
- do not encode A/B identity using colour alone;
- aria-live=polite for status and results, not for every animation frame;
- respect prefers-reduced-motion;
- no autoplay speech;
- Stop speaking must immediately call speechSynthesis.cancel();
- Escape should close an overlay or return to the previous safe state;
- preserve keyboard focus after mode changes;
- meaningful alt text for family and candidate images.

Use a warm, calm visual design suitable for a digital frame. Avoid medical-dashboard styling and tiny controls.

## API utility requirements

Create a small fetch helper that:

- uses AbortController with a 45-second timeout;
- checks response.ok;
- validates the BaseResponse shape defensively;
- returns response.data;
- produces a short human-friendly error;
- never retries a POST automatically.

The Gemini API key must never be visible in the browser.

## Demo resilience

Add a clearly labelled, opt-in demo-data switch only if time permits. It must default off. When enabled, display a persistent “Demo data - backend unavailable” banner and use examples that exactly match the backend schemas.

Do not spend time on authentication, routing libraries, settings pages, databases, deployment, or complex animation.

## Verification

Run:

~~~bash
cd frontend
npm install
npm run build
~~~

Then run the backend separately and manually verify:

1. ambient mode loads;
2. vision upload reaches POST /vision/explain;
3. the returned headline is large and speech starts only after user action;
4. Stop speaking works;
5. Memory Buy reaches POST /memory/buy;
6. exactly two cards appear;
7. backend failure displays a useful error;
8. no API key appears in built JavaScript, source, or environment files.

If you add tests, keep them focused on response parsing and the two core state transitions. A passing production build is mandatory.

## Definition of done

- frontend is entirely under frontend/;
- npm run build passes;
- both P0 flows work against the documented API contracts;
- interface uses one-decision-at-a-time design;
- browser speech is controllable;
- API errors are visible;
- no secrets are present;
- changes are committed to codex/kaiyu-frontend.

## Handoff

Reply with:

1. branch and commit hash;
2. files changed;
3. exact startup commands;
4. npm build result;
5. required VITE environment variables;
6. any backend contract mismatch;
7. one known limitation.

Stop after the core flows and build pass. Do not add optional features while a required flow is incomplete.
