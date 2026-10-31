# Three-minute Arlo demo

[Rehearsal draft. All unbracketed paragraphs below are spoken English; headings and bracketed cues are not spoken. June is a fictional persona. Target 360–400 spoken words at roughly 125–135 words per minute, including short interaction pauses.]

[Before presenting: configure an event key locally and restart the backend with the real shared provider. The current local demonstration server may use an explicitly injected deterministic story provider. Verify each live scene before claiming it is live. Keep the frontend's Use demo data switch OFF for the live journey; it disables Start a story when ON. Obtain an authorised medicine-label photo. No recording is supplied by this document.]

## 0:00–0:35 — One person

[Show the ambient photo frame.]

Imagine June, an older adult who wants to manage everyday tasks independently. The medicine label is too small. She remembers a household product by its blue bottle, not its name. And a family photo means more when someone shares its context. Arlo brings these moments into one familiar photo frame, with large text, spoken explanations, and one understandable decision at a time. June stays in control of what happens next.

## 0:35–1:25 — Explain this label

[Click Ask Arlo → Explain this label → Upload a photo. Select the authorised label, then click Explain this label. Point to the loading state. Wait for the response and check its source notice.]

First, June shows Arlo a medicine label. Gemini four Argon is our multimodal reasoning and structured-output engine. It reads the supplied image and returns a short explanation that our backend validates before displaying it. Here is the large-print takeaway, with the original image alongside it for comparison. June chooses when to hear it.

[Click Read aloud, allow a brief phrase, then click Stop speaking.]

And she can stop it immediately. This is help reading visible instructions, not medical advice. If the image is unclear, Arlo asks for another photo instead of filling in missing dosage information. The original label remains the reference.

## 1:25–2:05 — Find a familiar product

[Click Back, then Help me find a product. Say the next quoted phrase; use optional browser voice input only when supported, otherwise type the exact phrase. Click Find my product.]

Now June says, “the blue bottle my daughter bought.” She should not need to remember a brand or navigate a long catalogue. Argon can extract clues from that description, and our matcher ranks a small household catalogue. We show exactly two options, A and B. These illustrations and catalogue records are sample data; they are not proof of a real family purchase. June picks the familiar one. Nothing is ordered, and nothing is paid for. External actions remain under human control.

[Choose one card. Point to the confirmation and click Back to my frame.]

## 2:05–2:35 — A story under human control

[Click Start a story. Once captions appear and speech begins, click Stop.]

Finally, a family photo becomes an invitation to talk. This short story uses the supplied caption as context. Our application streams text over a WebSocket, and the browser reads it aloud. Watch what happens when June interrupts. Playback stops, queued speech is cleared, and the backend stops sending the remaining story. She can start again whenever she wants. The pace belongs to her.

## 2:35–3:00 — Why it matters

[Show the architecture slide briefly, then return attention to the frame.]

Argon provides reasoning; our backend validates results; the accessible interface makes them usable. Argon does not support the Live API. This prototype uses browser speech and application transport. We have tested software behaviour, but meaningful accessibility evaluation with older adults is our next step. Arlo should make independence feel a little easier, one everyday moment at a time.

## Replacement line for API failure — approximately ten seconds

[Replace the next live commentary with this line; do not append it to the timed script. Only switch label/product flows to Use demo data after the banner is visible. A story requires the explicit server-side demo provider; otherwise skip that scene.]

The live service is unavailable. I’ll show a clearly labelled demonstration of the interface; this result is not a live model response.

## Rehearsal and M3 handoff

[Practise with a stopwatch; model latency and browser speech vary. Never say a failed or demo scene is live. Do not claim voice-triggered interruption: this UI demonstrates the Stop control and Escape key.]

[M3 contract: START_STORY creates connection-local photo context. After STORY_COMPLETE, or after sending INTERRUPT and receiving PLAYBACK_STOP, a client may send USER_TEXT with text and the current session_id. It receives a fresh STORY_STARTED, ordered CAPTION_CHUNK events and STORY_COMPLETE. Before a photo, ERROR code is PHOTO_REQUIRED; during an active story it is STORY_BUSY. PING/PONG remains available. A null interaction_id is valid for stateless Argon output.]

[M3 UI handoff: the photo question form sends USER_TEXT on the retained connection after completion or PLAYBACK_STOP. A new story or photo clears the old context; navigation and unmount release it. Stop browser speech immediately and clear its queue before waiting for PLAYBACK_STOP. The complete question/reply path still needs a real-model rehearsal with an event key.]

[Known limitation: cancelling delivery does not terminate a synchronous Google SDK request already running in the shared core's worker thread; it can continue until its own transport timeout. M3 receives captions, not photo pixels, and does not retain a conversation transcript.]
