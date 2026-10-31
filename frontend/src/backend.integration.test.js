// @vitest-environment node
// Starts the real FastAPI app with explicit demo/no-key settings; never calls Gemini.
import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';

const integration = process.env.ARLO_INTEGRATION === '1' ? describe : describe.skip;
const root = resolve(process.cwd(), '..');
const python = process.env.ARLO_TEST_PYTHON
  ? resolve(process.cwd(), process.env.ARLO_TEST_PYTHON)
  : process.platform === 'win32' ? 'python' : 'python3';
const appScript = `import os, socket, uvicorn
if os.environ.get('ARLO_STORY_TEST_PROVIDER') == '1':
    import app.modules.m3_live_tool as m3
    m3.argon_story_provider = m3.demo_story_provider
sock = socket.socket()
sock.bind(('127.0.0.1', 0))
sock.listen(128)
print('PORT=' + str(sock.getsockname()[1]), flush=True)
server = uvicorn.Server(uvicorn.Config('app.main:app', log_level='warning'))
server.run(sockets=[sock])`;

async function startBackend(demo) {
  const child = spawn(python, ['-u', '-c', appScript], {
    cwd: root,
    env: { ...process.env, GEMINI_API_KEY: '', ARLO_ENABLE_MOCKS: demo ? 'true' : 'false', ARLO_STORY_TEST_PROVIDER: demo ? '1' : '0' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let diagnostics = '';
  child.stderr.on('data', (chunk) => { diagnostics += chunk; });
  const port = await new Promise((resolvePort, reject) => {
    let output = '';
    const timer = setTimeout(() => { child.kill(); reject(new Error(`Backend did not start: ${diagnostics}`)); }, 10_000);
    child.on('error', (error) => { clearTimeout(timer); reject(error); });
    child.on('exit', (code) => { clearTimeout(timer); reject(new Error(`Backend exited (${code}): ${diagnostics}`)); });
    child.stdout.on('data', (chunk) => {
      output += chunk;
      const match = output.match(/PORT=(\d+)/);
      if (match) { clearTimeout(timer); resolvePort(Number(match[1])); }
    });
  });
  const base = `http://127.0.0.1:${port}`;
  for (let attempt = 0; attempt < 100; attempt++) {
    try { if ((await fetch(`${base}/`)).ok) return { child, base }; } catch { /* server starting */ }
    await new Promise((done) => setTimeout(done, 50));
  }
  child.kill();
  throw new Error(`Backend readiness failed: ${diagnostics}`);
}

integration('actual FastAPI responses through the frontend client', () => {
  let demoBackend;
  let noKeyBackend;
  let api;

  beforeAll(async () => {
    demoBackend = await startBackend(true);
    noKeyBackend = await startBackend(false);
    vi.stubEnv('VITE_ARLO_API_BASE', `${demoBackend.base}/api/arlo`);
    vi.resetModules();
    api = await import('./api.js');
  }, 30_000);

  afterAll(() => { demoBackend?.child.kill(); noKeyBackend?.child.kill(); vi.unstubAllEnvs(); });

  it('loads the actual album with local provenance', async () => {
    const photos = await api.getPhotos();
    expect(Array.isArray(photos)).toBe(true);
    expect(photos[api.PROVENANCE]).toBe('local');
  });

  it('posts an image to actual vision endpoint and identifies explicit demo data', async () => {
    // A valid 2x2 PNG. Demo mode deliberately reports it as needing a retake.
    const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAE0lEQVR4nGP8//8/AwMDEwMYAAAkBgMBXaJOiAAAAABJRU5ErkJggg==', 'base64');
    const file = new File([png], 'label.png', { type: 'image/png' });
    const result = await api.explainLabel(file);
    expect(result[api.PROVENANCE]).toBe('demo');
    expect(result.is_blurry).toBe(true);
    expect(result.headline_large).toMatch(/demo data/i);
  });

  it('posts to actual memory endpoint, marks keyword fallback and loads both real image URLs', async () => {
    const result = await api.findProducts('the blue bottle my daughter bought');
    expect(result[api.PROVENANCE]).toBe('keyword');
    expect(result.candidates).toHaveLength(2);
    for (const candidate of result.candidates) {
      const image = await fetch(candidate.image_url);
      expect(image.status).toBe(200);
      expect(image.headers.get('content-type')).toContain('image/svg+xml');
    }
  });

  it('surfaces a real missing-key HTTP error without presenting it as a successful result', async () => {
    const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAE0lEQVR4nGP8//8/AwMDEwMYAAAkBgMBXaJOiAAAAABJRU5ErkJggg==', 'base64');
    const form = new FormData(); form.append('file', new File([png], 'label.png', { type: 'image/png' })); form.append('query', 'Read this label');
    const response = await fetch(`${noKeyBackend.base}/api/arlo/vision/explain`, { method: 'POST', body: form });
    expect(response.status).toBe(503);
    expect((await response.json()).detail).toMatch(/not configured/i);
    vi.stubEnv('VITE_ARLO_API_BASE', `${noKeyBackend.base}/api/arlo`);
    vi.resetModules();
    const noKeyApi = await import('./api.js');
    await expect(noKeyApi.explainLabel(new File([png], 'label.png', { type: 'image/png' }))).rejects.toMatchObject({ kind: 'http' });
  });

  it('exchanges real story WebSocket session, error and interruption messages without a key', async () => {
    const socket = new WebSocket(`${noKeyBackend.base.replace('http:', 'ws:')}/api/arlo/live/ws`);
    const pending = [];
    const waiters = [];
    socket.addEventListener('message', (event) => {
      const message = JSON.parse(event.data);
      if (waiters.length) waiters.shift()(message); else pending.push(message);
    });
    const next = () => pending.length ? Promise.resolve(pending.shift()) : new Promise((resolve) => waiters.push(resolve));
    try {
      const ready = await next();
      expect(ready.type).toBe('SESSION_READY');
      expect(ready.session_id).toBeTruthy();
      socket.send(JSON.stringify({ type: 'START_STORY', session_id: ready.session_id, photo_id: 'photo-1', caption: 'A day by the sea' }));
      const started = await next();
      expect(started.type).toBe('STORY_STARTED');
      const error = await next();
      expect(error.type).toBe('ERROR');
      expect(error.story_id).toBe(started.story_id);
      socket.send(JSON.stringify({ type: 'INTERRUPT', session_id: ready.session_id }));
      const stopped = await next();
      expect(stopped.type).toBe('PLAYBACK_STOP');
      expect(stopped.session_id).toBe(ready.session_id);
    } finally { socket.close(); }
  }, 10_000);

  it('streams a labelled test story from the real WebSocket backend and acknowledges interruption', async () => {
    const socket = new WebSocket(`${demoBackend.base.replace('http:', 'ws:')}/api/arlo/live/ws`);
    const pending = [];
    const waiters = [];
    socket.addEventListener('message', (event) => {
      const message = JSON.parse(event.data);
      if (waiters.length) waiters.shift()(message); else pending.push(message);
    });
    const next = () => pending.length ? Promise.resolve(pending.shift()) : new Promise((resolve) => waiters.push(resolve));
    try {
      const ready = await next();
      expect(ready.type).toBe('SESSION_READY');
      const start = () => socket.send(JSON.stringify({ type: 'START_STORY', session_id: ready.session_id, photo_id: 'p1', caption: 'A day by the sea' }));
      start();
      const started = await next();
      expect(started.type).toBe('STORY_STARTED');
      const first = await next();
      expect(first).toMatchObject({ type: 'CAPTION_CHUNK', story_id: started.story_id, sequence: 1, source: 'demo' });
      socket.send(JSON.stringify({ type: 'INTERRUPT', session_id: ready.session_id }));
      let response;
      do { response = await next(); } while (response.type === 'CAPTION_CHUNK');
      expect(response).toMatchObject({ type: 'PLAYBACK_STOP', story_id: started.story_id });
      start();
      const second = await next();
      expect(second.type).toBe('STORY_STARTED');
      let sequence = 0;
      do {
        response = await next();
        if (response.type === 'CAPTION_CHUNK') expect(response.sequence).toBe(++sequence);
      } while (response.type === 'CAPTION_CHUNK');
      expect(sequence).toBeGreaterThan(0);
      expect(response).toMatchObject({ type: 'STORY_COMPLETE', story_id: second.story_id, source: 'demo' });
      socket.send(JSON.stringify({ type: 'USER_TEXT', session_id: ready.session_id, text: 'What is in this photo?' }));
      const followup = await next();
      expect(followup.type).toBe('STORY_STARTED');
      expect(followup.photo_id).toBe('p1');
      expect(followup.story_id).not.toBe(second.story_id);
      sequence = 0;
      do {
        response = await next();
        if (response.type === 'CAPTION_CHUNK') expect(response.sequence).toBe(++sequence);
      } while (response.type === 'CAPTION_CHUNK');
      expect(sequence).toBeGreaterThan(0);
      expect(response).toMatchObject({ type: 'STORY_COMPLETE', story_id: followup.story_id, source: 'demo' });
    } finally { socket.close(); }
  }, 10_000);
});
