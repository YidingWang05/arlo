# Codex Assignment - Weihang You

Copy everything below into a new Codex task opened on the Arlo repository.

---

You are Arlo's product lead, M3 Live Companion engineer, and three-minute demo presenter for the Google DeepMind / Gemini Hackathon Track 2. We have less than 70 minutes for your implementation and less than two hours until code freeze.

Repository: https://github.com/YidingWang05/arlo  
Your branch: codex/weihang-m3-pitch  
Foundation reasoning model: Gemini 4 Argon, model ID gemini-4-argon

## Outcome

Deliver:

1. a reliable, interruptible WebSocket story stream for the Live Companion scene;
2. backend WebSocket tests;
3. a word-for-word three-minute pitch and live-demo script;
4. a six-slide deck outline;
5. concise answers to difficult judge questions.

The demo must be emotionally clear but technically honest.

## Critical model fact

Gemini 4 Argon does not support the Gemini Live API. Do not claim that it does and do not attempt to open an Argon Live session.

For this MVP:

- the application WebSocket provides full-duplex client/server transport;
- Argon may generate or refine short story text through the shared core engine;
- the frontend uses browser speech synthesis for audible playback;
- interruption cancels playback and stops further chunks;
- a future version may use gemini-3.8-live as a companion voice model while Argon remains the reasoning engine.

This distinction should be stated confidently if judges ask.

## Start safely

1. Run git status and preserve any existing teammate changes.
2. Pull main with fast-forward only, then create or switch to codex/weihang-m3-pitch.
3. Read README.md, app/modules/m3_live_tool.py, app/api/routes.py, app/core/base_model.py, and the frontend API contract.
4. Do not edit Xiyu, Yiding, or Kaiyu's owned files.
5. Never print or commit any API key.

## Files you own

- app/modules/m3_live_tool.py
- tests/test_m3_live.py
- docs/pitch/DEMO_SCRIPT.md
- docs/pitch/SLIDE_OUTLINE.md
- docs/pitch/JUDGE_QA.md

Do not edit app/core/, app/api/routes.py, M1, M2, or frontend/.

## WebSocket message contract

Use small JSON messages with a session ID. Support at least:

Client to server:

- START_STORY with photo_id, caption, and optional user_prompt;
- USER_TEXT with text;
- INTERRUPT;
- PING.

Server to client:

- SESSION_READY;
- STORY_STARTED;
- CAPTION_CHUNK with sequence number, text, and barge_in_ready=true;
- STORY_COMPLETE;
- PLAYBACK_STOP;
- PONG;
- ERROR with a safe user-facing message.

Requirements:

- accept the socket exactly once;
- validate JSON and message types;
- reject oversized messages;
- maintain per-connection session state only;
- split story text into short natural chunks;
- add a small asynchronous delay between chunks without blocking the event loop;
- when INTERRUPT arrives, stop the active generation/chunking task immediately, send PLAYBACK_STOP, and return to listening state;
- support a new story after interruption;
- handle disconnects without attempting to close an already-disconnected socket;
- never swallow all exceptions silently;
- never log family-photo content or raw personal data.

If the shared core exposes generate_text, use it with gemini-4-argon and low thinking for one short story. If the method is not yet available, design the handler around an injectable async story provider and provide a clearly labelled deterministic demo provider for tests. Do not create a second direct Gemini client.

Keep the story under 90 words. It may reflect the supplied caption but must not invent sensitive family facts, dates, names, or relationships.

## WebSocket tests

Use FastAPI TestClient or a minimal test app. Cover:

- connection produces SESSION_READY;
- START_STORY produces ordered CAPTION_CHUNK events and STORY_COMPLETE;
- PING produces PONG;
- INTERRUPT produces PLAYBACK_STOP and prevents remaining chunks;
- invalid JSON produces ERROR without killing the server;
- unknown message type produces ERROR;
- a second story can start after interruption;
- disconnect exits cleanly.

Tests must not call the network or spend Gemini credits.

Run:

~~~bash
python -m compileall app tests
pytest -q tests/test_m3_live.py
~~~

## Three-minute script

Write docs/pitch/DEMO_SCRIPT.md as exact spoken English, including stage directions and fallback lines. Target 360-400 spoken words, not counting stage directions.

Timing:

- 0:00-0:35 - introduce a specific older adult and the problem: tiny medicine labels, forgotten product names, and disconnection from family context;
- 0:35-1:25 - live medicine-label upload, visible Argon analysis, large plain-English takeaway, and controlled speech;
- 1:25-2:05 - say “the blue bottle my daughter bought,” then show exactly two A/B candidates;
- 2:05-2:35 - family-photo story begins and the presenter interrupts it;
- 2:35-3:00 - explain architecture, human control, safety, and human-centred impact.

The script must:

- never say Arlo diagnoses or gives medical advice;
- never claim Argon has a Live API;
- identify Argon as the multimodal reasoning and structured-output engine;
- mention that external actions remain under human control;
- include a 10-second fallback line for API failure;
- include exact click/speak cues in brackets;
- finish with one memorable sentence, not a feature list.

## Six-slide deck

Write docs/pitch/SLIDE_OUTLINE.md:

1. One person, one problem;
2. Arlo's one-decision interface;
3. Live three-scene product journey;
4. Architecture and why Gemini 4 Argon;
5. Safety, accessibility, and verification;
6. Impact, next step, and ask.

For each slide provide:

- title;
- one-sentence message;
- maximum three visible bullets;
- recommended visual;
- speaker note;
- transition to the next slide.

Slides support the demo and must not replace it.

## Judge Q&A

Write docs/pitch/JUDGE_QA.md with concise answers for:

- Why is this an agent rather than a chatbot?
- Why does it need Gemini 4 Argon?
- What is real versus mocked?
- How do you prevent dangerous medicine advice?
- Does Argon support Live API?
- What happens when the model or network fails?
- How is family data protected?
- How was accessibility tested?
- Why exactly two shopping candidates?
- What would production deployment require?
- How do you evaluate accuracy?
- Why not use OCR plus rules?

Answers must match the actual repository. Do not claim tests, metrics, privacy controls, deployment, or features that are not implemented.

## Definition of done

- WebSocket protocol is explicit and tested;
- interruption actually cancels remaining chunks;
- no false Argon Live claim exists;
- exact three-minute script is ready to rehearse;
- six-slide outline and judge Q&A are complete;
- tests pass;
- changes are committed to codex/weihang-m3-pitch.

## Handoff

Reply with:

1. branch and commit hash;
2. files changed;
3. WebSocket message contract;
4. test result;
5. final script word count and estimated duration;
6. one integration request for Kaiyu;
7. one known limitation.

Stop adding functionality once the WebSocket test and pitch documents are complete. Rehearse instead.
