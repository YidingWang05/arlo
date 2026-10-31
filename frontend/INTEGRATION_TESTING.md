# Frontend and backend integration check

The frontend reads `BaseResponse.meta` and distinguishes verified Gemini,
backend demo, keyword matching, local data, and unverified responses. A Gemini
label requires `source: "gemini"`, `is_mock: false`, and a non-empty
`interaction_id`. Results marked mock always display as demo data. The current
household catalogue is sample data regardless of the matching method.

Run from the repository root after installing Python dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd frontend
npm ci
npm run build
npm test
ARLO_TEST_PYTHON=../.venv/bin/python npm run test:integration
```

The integration test starts isolated local FastAPI servers, overrides the API
key to empty and explicitly enables demo mode for one server. It calls the
real album, vision and memory routes using the frontend API client, checks the
two served image URLs, and verifies that a no-key vision request returns an
error. It needs local loopback access and does not call Gemini or verify event
credentials. Run the separate live smoke test with the backend owner for that.
