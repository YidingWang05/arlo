# Builder guide review

Reviewed the supplied seven-page Gemini 4 Argon hackathon builder guide against
the Yiding M2/API branch. This is a comparison with the supplied event document,
not independent verification of model availability or SDK releases.

## M2/API alignment

- M2 calls only the shared engine with a structured attribute schema.
- Deterministic selection grounds both cards in the household catalogue.
- Selection requires human confirmation; no purchase or payment is executed.
- Fallback is explicitly described as keyword matching in the spoken prompt.
- Offline tests mock Gemini. A fuzzy-language regression test proves that model
  attributes can select a product without a literal brand or category clue.
- Low thinking is appropriate for targeted extraction according to page 4.
  The shared engine, not the M2 prompt, must actually configure this value.

## Foundation integration requirements (Xiyu)

The existing core on this branch has not yet been replaced by Xiyu's work.
Before claiming a live Argon demo:

1. Replace the current `client.models.generate_content` call with the guide's
   recommended `client.interactions.create` integration (pages 3-4).
2. Use `generation_config` with lowercase `thinking_level="low"` for extraction.
   The existing default is uppercase `LOW` in the old configuration structure.
3. Remove `temperature`; the guide says custom sampling parameters are ignored
   with deprecation warnings (page 5).
4. Check the dependency floor: the guide specifies SDK version 2.3.0 or later
   (page 3), while this branch's requirements allow `google-genai>=0.1.1`.
5. Preserve the `generate_structured(prompt, image_bytes, response_schema)`
   interface or coordinate a compatibility change. Preserve validated output.
6. Avoid silent mock success. The current core still returns mock vision results
   on errors; M2 labels its own empty/failed extraction fallback separately.
7. Verify PNG/WEBP handling: the gateway accepts these formats, but the existing
   core marks all image bytes as JPEG. Coordinate MIME support with the M1 owner.

The assignment explicitly reserves `app/core/` and M1 for Xiyu, so this review
does not edit that implementation or merge other branches.

## Demo acceptance still pending

Run a real-input smoke test with the event account after foundation integration;
offline tests do not establish live Argon availability. Rehearse the complete
workflow within the guide's three-minute limit, using a specific person's task.
The catalogue illustrations are labelled demo assets, not product photographs.

Merge order remains Xiyu, Yiding, Weihang, Kaiyu, followed by the full backend
suite and frontend integration checks. No merge is performed by this review.
