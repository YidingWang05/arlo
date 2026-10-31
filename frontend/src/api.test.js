import { describe, expect, it, vi } from 'vitest';
import { parseEnvelope, validateMemory, validateVision, requestData, PROVENANCE, TIMEOUT_MS } from './api.js';
import { demoMemory, demoVision } from './demo.js';

const envelope = (data) => ({ code: 200, message: 'success', data: structuredClone(data) });

describe('defensive API contract', () => {
  it('unwraps valid results and keeps unmarked responses visibly unverified', () => {
    expect(parseEnvelope(envelope(demoVision), validateVision)[PROVENANCE]).toBe('unverified');
    expect(parseEnvelope(envelope(demoMemory), validateMemory).candidates).toHaveLength(2);
  });
  it.each([null, {}, { code: 200, message: 'ok' }, { code: 200, message: 'ok', data: null }, { code: 500, message: 'fail', data: demoVision }])('rejects incomplete/error envelopes: %j', (value) => {
    expect(() => parseEnvelope(value, validateVision)).toThrow();
  });
  it('requires two distinct, usable candidates and a complete vision result', () => {
    const memory = structuredClone(demoMemory);
    expect(validateMemory({ ...memory, candidates: memory.candidates.slice(0, 1) })).toBe(false);
    expect(validateMemory({ ...memory, candidates: [...memory.candidates, memory.candidates[0]] })).toBe(false);
    expect(validateMemory({ ...memory, candidates: [memory.candidates[0], memory.candidates[0]] })).toBe(false);
    memory.candidates[0].image_url = 'javascript:alert(1)';
    expect(validateMemory(memory)).toBe(false);
    expect(validateVision({ ...demoVision, is_blurry: 'false' })).toBe(false);
  });
  it.each([
    [() => Promise.resolve({ ok: false, status: 503 }), /unavailable/],
    [() => Promise.resolve({ ok: true, json: () => Promise.reject(new SyntaxError()) }), /unreadable/],
    [() => Promise.reject(new TypeError('Failed to fetch')), /Cannot reach Arlo/],
  ])('reports failures without automatically retrying a POST', async (response, message) => {
    const fetchMock = vi.fn(response); vi.stubGlobal('fetch', fetchMock);
    await expect(requestData('/memory/buy', { method: 'POST', validate: validateMemory })).rejects.toThrow(message);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
  it('aborts after 45 seconds and distinguishes explicit cancellation', async () => {
    vi.useFakeTimers();
    vi.stubGlobal('fetch', vi.fn((_url, { signal }) => new Promise((_resolve, reject) => {
      signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
    })));
    const timed = expect(requestData('/vision/explain', { method: 'POST', validate: validateVision })).rejects.toMatchObject({ kind: 'timeout' });
    await vi.advanceTimersByTimeAsync(TIMEOUT_MS); await timed;
    const controller = new AbortController();
    const cancelled = expect(requestData('/vision/explain', { signal: controller.signal, validate: validateVision })).rejects.toMatchObject({ name: 'AbortError' });
    controller.abort(); await cancelled;
  });
});
