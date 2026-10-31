# Judge Q&A

Use these as short spoken answers. Identify the mode actually running before the demo; code support, offline test results and a successful live call are different evidence. Do not claim a clinical result, a user study, a latency target, an accessibility audit or production deployment.

## 1. Why is this an agent rather than a chatbot?

Arlo is a bounded task assistant: it combines image explanation, household-catalogue lookup and controllable photo storytelling through separate tools. The user selects the task and confirms the result. We have not implemented general autonomous planning, purchases or unattended external actions.

## 2. Why does it need Gemini 4 Argon?

Argon provides a shared multimodal reasoning and structured-output interface. It can explain an image and extract clues from an imprecise description without separate hand-written rules for every phrasing. We have not established that it outperforms smaller models or OCR baselines; that needs comparative evaluation.

## 3. What is real versus mocked?

The repository contains a real Google Interactions API integration, actual FastAPI routes and a working browser client. The household catalogue and product illustrations are sample data. Tests use offline providers. A local M3 demo provider returns deterministic stories and is labelled demo; do not describe it as Argon output. A live run must be verified with the configured event key. Stateless live responses may legitimately have no interaction ID.

## 4. How do you prevent dangerous medicine advice?

M1 is instructed to explain visible label information, avoid invented doses and request a clearer image when needed. Its schema constrains the result and substitutes a retake message for blurry input. The interface keeps the original image available and recommends checking unclear instructions with a pharmacist. These safeguards have software tests; they are not proof of clinical safety or a substitute for professional advice.

## 5. Does Argon support the Live API?

No. Argon generates short text through the shared Interactions engine. Our own WebSocket transports captions, and the browser synthesises speech. The UI's Stop button and Escape key demonstrate interruption; they do not demonstrate microphone-triggered voice barge-in. A separate live voice model is only a future option.

## 6. What happens when the model or network fails?

Errors are visible. The shared core retries only selected transient failures with a bounded attempt count. M3 has a generation timeout and returns an error without silently substituting demo output. M2 can explicitly fall back to keyword matching. Frontend demo data is opt-in. For a presentation failure, use the exact fallback line and identify the demonstration mode or skip the scene.

## 7. How is family data protected?

Keys stay on the backend. M3 holds bounded caption context per connection, does not log caption or prompt contents and uses the shared core's store=false path. Stopping delivery does not guarantee that an already-sent Google request is terminated. The family album is in-memory sample state; authentication, household isolation, production consent and retention controls have not been implemented. We cannot claim data never leaves the device when using Google generation.

## 8. How was accessibility tested?

The frontend has tests for core flows, controllable speech, failure states and keyboard-related behaviour. Its implementation uses large text, clear controls and reduced-motion handling. We have not completed a formal WCAG audit, screen-reader certification or an older-adult usability study. Co-design and task-based evaluation with intended users are next steps.

## 9. Why exactly two shopping candidates?

Two candidates create one clear A/B decision. They come from a bounded sample catalogue rather than model-invented product URLs. This is a design hypothesis, not a proven optimal number. We need to measure whether the intended item appears in the top two and whether people can make the choice comfortably.

## 10. What would production deployment require?

Authenticated family accounts and household boundaries, consent and retention policies, durable storage, secure credential management, request limits, monitoring and evaluated failure behaviour. We would also need authorised content, better catalogue coverage and meaningful user/accessibility studies. The current prototype runs locally and is not a medical device or a production family-data service.

## 11. How do you evaluate accuracy?

Current automated tests verify contracts and controlled scenarios, not real-world accuracy. At the USER_TEXT checkpoint, 132 backend tests passed, including 59 M3 tests; earlier frontend checks passed 45 unit tests and six local integration tests. Proposed evaluation measures visible-label faithfulness, safe abstention on unreadable images, product top-two recall, story grounding, stop behaviour and user task completion. No numerical accuracy or clinical-performance claim is available yet.

## 12. Why not use OCR plus rules?

OCR plus rules is a useful baseline and may be sufficient for constrained labels. Arlo also needs to turn visible text into plain language and handle fuzzy product descriptions and photo-caption questions. A shared multimodal engine offers that flexibility, while deterministic validation remains useful. We should compare cost, latency and error rates instead of assuming a language model is always necessary.

## Technical follow-up: current M3 boundary

- START_STORY establishes photo context for the connection. USER_TEXT replaces the prompt for a new short response grounded in that caption; it does not append a growing transcript.
- Send USER_TEXT after completion, or after INTERRUPT and PLAYBACK_STOP. PHOTO_REQUIRED means no photo context; STORY_BUSY means the current task must be stopped or allowed to finish.
- Responses use the same STORY_STARTED, ordered CAPTION_CHUNK and STORY_COMPLETE events. The source/model are server-established; interaction_id may be null. Text is escaped JSON data under a separate system instruction.
- The current frontend has start/stop story controls but no follow-up input, and closes its socket after completion or stopping. Exposing follow-ups requires a frontend integration change. This limitation must remain explicit.
- Offline cancellation tests cover generation, chunking, restart, disconnect and session isolation. They do not establish real-network latency or cancellation of the provider's worker-thread request.

## References for technical questions

- Repository implementation: app/core/base_model.py, app/modules/m3_live_tool.py, frontend/src/usePhotoStory.js.
- Google model capabilities: https://ai.google.dev/gemini-api/docs/models/gemini-4-argon
- Google Interactions API: https://ai.google.dev/gemini-api/docs/interactions
- Rehearsal script and UI handoff: DEMO_SCRIPT.md.
