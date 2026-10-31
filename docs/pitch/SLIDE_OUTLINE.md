# Arlo: six-slide outline

Use the slides as brief support for the live frame journey. They are an outline, not an exported slide deck. Keep visible text large, retain contrast and avoid showing credentials or private family content. Persona and catalogue examples are fictional/sample data. Do not present intended behaviour as verified live performance.

## 1. One person, one problem

**Message:** June wants everyday independence without another complicated interface.

**Visible bullets:**
- Small print creates friction.
- Familiar products are hard to name.
- Family photos need context.

**Visual:** A fictional persona beside a medicine label, blue household bottle and authorised family-photo placeholder.

**Speaker note:** Introduce June as an illustrative persona, not a participant in a user study. Describe the tasks rather than a diagnosis or a claim about all older adults.

**Transition:** “What if these moments could start from a familiar photo frame?”

## 2. One understandable decision

**Message:** Arlo reduces navigation to a clear next action with controllable speech.

**Visible bullets:**
- Large takeaway and simple controls.
- Two product candidates: A or B.
- Speech starts and stops on request.

**Visual:** Current frame screenshots: Ask Arlo choices, a large-print result and two equal product cards.

**Speaker note:** Point to the actual implementation. The interface uses large text and keyboard-operable controls; formal accessibility and older-adult evaluation are still pending. Browser voice support varies.

**Transition:** “Let’s follow June through three everyday moments.”

## 3. See the three-scene journey

**Message:** The live demo connects a visible label, a fuzzy description and a caption-based photo story.

**Visible bullets:**
- Show a label; compare the explanation.
- Describe a product; choose A or B.
- Start a photo story; interrupt it.

**Visual:** Three static scene thumbnails with the product UI taking most of the presentation time.

**Speaker note:** Use an authorised medicine image. Keep catalogue illustrations labelled as sample data. The story uses caption text, not independent analysis of the displayed photo. Demonstrate interruption with Stop; do not claim microphone-triggered barge-in. If a model call fails, use the exact fallback line in DEMO_SCRIPT.md and identify any demonstration provider.

**Transition:** “The simple interface sits on a deliberately small architecture.”

## 4. Why Gemini 4 Argon?

**Message:** A shared reasoning engine supplies validated outputs, while the application controls transport and playback.

**Visible bullets:**
- Argon: multimodal reasoning and structured output.
- FastAPI: validated module contracts.
- WebSocket captions + browser speech.

**Visual:** A compact architecture figure: frame client → FastAPI gateway → bounded modules → shared Argon Interactions engine, with browser speech beside the client.

**Speaker note:** All production Gemini calls go through app/core/base_model.py. M1 supplies an image; M2 supplies product clues; M3 supplies caption and optional user text. State clearly that Argon has no Live API. A missing interaction ID is valid with store=false. Do not claim this architecture proves superiority over simpler baselines.

**Transition:** “Control and verification matter as much as generation.”

## 5. Human control and verification

**Message:** Explicit source labels and tested cancellation help users understand and control the prototype.

**Visible bullets:**
- Source and fallback states stay visible.
- Stop clears speech and remaining captions.
- Offline tests cover protocol and failure paths.

**Visual:** Actual Stop control, a labelled demonstration notice and a small test-result excerpt with the command and commit used.

**Speaker note:** At the USER_TEXT feature checkpoint, the local backend suite passed 132 tests, including 59 M3 tests; this is a development result, not a performance metric. Earlier frontend validation passed 45 unit tests and 6 local integration tests. Re-run relevant checks before presenting a later revision. No clinical validation, formal accessibility audit or user study has been completed here. API keys stay server-side; authenticated family accounts, durable storage and production data governance are not implemented.

**Transition:** “The next step is to learn whether this actually helps people.”

## 6. More independence, fewer steps

**Message:** The goal is measurable everyday usefulness with the older adult in control.

**Visible bullets:**
- Co-design and test with older adults.
- Measure task success, errors and stop latency.
- Seek pilot and accessibility partners.

**Visual:** Return to the calm frame screen with one closing sentence: “One everyday moment at a time.”

**Speaker note:** Describe a future evaluation, not invented results: label faithfulness and unreadable-image handling; product top-two recall on authorised catalogue cases; story grounding; cancellation and latency; task completion with users. Deployment would require authentication, consent, retention controls and operational monitoring. The photo question form sends USER_TEXT on a retained session after completion or stop acknowledgement; real-model rehearsal remains pending.

**Transition:** “Arlo should make independence feel a little easier, one everyday moment at a time.”
