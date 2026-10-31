# API provenance and household images

Successful responses retain `code`, `message`, and `data`, and now include `meta`:

```json
{"source":"gemini","interaction_id":null,"model":"gemini-4-argon","is_mock":false}
```

`source` is `gemini` only when the shared engine supplies generation metadata.
Privacy-preserving `store=false` calls may omit the provider interaction ID;
the server-controlled model name still establishes provenance. The text-only
smoke probe opts into storage so it can return a provider interaction ID.
Other values are `keyword` for M2 deterministic fallback, `demo` for explicit
core demo mode, `local` for the family album, and `unverified` when provenance
is unavailable. Non-Gemini responses do not fabricate an interaction ID.
M2 Gemini provenance describes attribute extraction; its candidate catalogue
and labelled illustrations remain local demo data.

M2 candidate `image_url` values are absolute HTTP(S) URLs on the backend origin.
`GET /api/arlo/memory/images/{item_id}` serves the catalogue's SVG illustration;
unknown IDs return 404. The existing frontend HTTP(S) URL filter accepts them.
Behind a reverse proxy, configure trusted forwarded host/scheme handling so
generated URLs use the externally reachable backend origin.

Shared core errors exposed by the gateway use `{"detail":"safe message"}`:
invalid input 400, invalid model output 502, configuration/auth/model-access or
exhausted retry errors 503. M2 extraction failures retain its specified local
keyword fallback, returning 200 with `meta.source="keyword"` and visible wording.

Frontend owners can use these fields to distinguish local, fallback, and demo
states. The frontend recognizes server-controlled Gemini metadata with either a
nonempty interaction ID or model name and `is_mock=false`; unmarked responses
remain visibly unverified.
