import { act, renderHook } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { usePhotoStory } from './usePhotoStory.js';

let sockets;
class FakeSocket {
  constructor(url) { this.url = url; this.readyState = 1; this.sent = []; sockets.push(this); }
  send(value) { this.sent.push(JSON.parse(value)); }
  close() { this.readyState = 3; }
  receive(data) { this.onmessage?.({ data: typeof data === 'string' ? data : JSON.stringify(data) }); }
}
const photo = { id: 'photo-1', caption: 'A day by the sea' };
const event = (type, fields = {}) => ({ type, session_id: 'session-1', ...fields });
function begin(result) {
  act(() => result.current.start(photo));
  const socket = sockets.at(-1);
  act(() => socket.receive(event('SESSION_READY')));
  act(() => socket.receive(event('STORY_STARTED', { story_id: 'story-1', photo_id: photo.id })));
  return socket;
}
beforeEach(() => { sockets = []; vi.stubGlobal('WebSocket', FakeSocket); });

it('sends the photo and session, displays chunks, and speaks them in order until completion', () => {
  const { result } = renderHook(() => usePhotoStory());
  const socket = begin(result);
  expect(socket.url).toBe('ws://127.0.0.1:8000/api/arlo/live/ws');
  expect(socket.sent).toEqual([{ type: 'START_STORY', photo_id: photo.id, caption: photo.caption, session_id: 'session-1' }]);
  act(() => socket.receive(event('CAPTION_CHUNK', { story_id: 'story-1', sequence: 1, text: 'First sentence.', source: 'argon' })));
  act(() => socket.receive(event('CAPTION_CHUNK', { story_id: 'story-1', sequence: 2, text: 'Second sentence.', source: 'argon' })));
  expect(result.current.caption).toBe('First sentence. Second sentence.');
  expect(window.speechSynthesis.speak).toHaveBeenCalledTimes(1);
  const first = window.speechSynthesis.speak.mock.calls[0][0];
  expect(first.text).toBe('First sentence.');
  act(() => socket.receive(event('STORY_COMPLETE', { story_id: 'story-1', source: 'argon', model: 'gemini-4-argon', interaction_id: 'interaction-1' })));
  expect(result.current.active).toBe(true);
  act(() => first.onend());
  expect(window.speechSynthesis.speak.mock.calls[1][0].text).toBe('Second sentence.');
  act(() => window.speechSynthesis.speak.mock.calls[1][0].onend());
  expect(result.current.status).toBe('complete');
  expect(result.current.source).toBe('ai');
  expect(socket.readyState).toBe(3);
});

it.each([null, undefined, 'interaction-1'])('accepts verified Argon completion with optional interaction ID: %s', (interactionId) => {
  const { result } = renderHook(() => usePhotoStory());
  const socket = begin(result);
  act(() => socket.receive(event('CAPTION_CHUNK', { story_id: 'story-1', sequence: 1, text: 'A garden.', source: 'argon' })));
  act(() => socket.receive(event('STORY_COMPLETE', {
    story_id: 'story-1', source: 'argon', model: 'gemini-4-argon', interaction_id: interactionId,
  })));
  expect(result.current.source).toBe('ai');
  expect(result.current.caption).toBe('A garden.');
  act(() => window.speechSynthesis.speak.mock.calls[0][0].onend());
  expect(result.current.status).toBe('complete');
});

it.each([
  { source: 'argon', interaction_id: 'interaction-1' },
  { source: 'argon', model: 'other-model', interaction_id: null },
  { source: 'argon', model: 'gemini-4-argon', interaction_id: 123 },
  { source: 'argon', model: 'gemini-4-argon', interaction_id: '' },
  { source: 'argon', model: 'gemini-4-argon', interaction_id: '   ' },
  { source: 'unverified', model: 'gemini-4-argon', interaction_id: 'interaction-1' },
])('keeps invalid or unverified completion metadata unverified: %j', (metadata) => {
  const { result } = renderHook(() => usePhotoStory());
  const socket = begin(result);
  act(() => socket.receive(event('STORY_COMPLETE', { story_id: 'story-1', ...metadata })));
  expect(result.current.source).toBe('unverified');
  expect(result.current.status).toBe('complete');
});

it('cancels immediately, clears queued speech and ignores late chunks until stop acknowledgement', () => {
  const { result } = renderHook(() => usePhotoStory());
  const socket = begin(result);
  act(() => socket.receive(event('CAPTION_CHUNK', { story_id: 'story-1', sequence: 1, text: 'Speaking now.' })));
  act(() => socket.receive(event('CAPTION_CHUNK', { story_id: 'story-1', sequence: 2, text: 'Queued.' })));
  const first = window.speechSynthesis.speak.mock.calls[0][0];
  window.speechSynthesis.cancel.mockClear();
  act(() => result.current.stop());
  expect(window.speechSynthesis.cancel).toHaveBeenCalled();
  expect(socket.sent.at(-1)).toEqual({ type: 'INTERRUPT', session_id: 'session-1' });
  act(() => { first.onend(); socket.receive(event('CAPTION_CHUNK', { story_id: 'story-1', sequence: 3, text: 'Too late.' })); });
  expect(window.speechSynthesis.speak).toHaveBeenCalledTimes(1);
  expect(result.current.caption).not.toContain('Too late.');
  act(() => socket.receive(event('PLAYBACK_STOP', { story_id: 'story-1' })));
  expect(result.current.status).toBe('idle');
  expect(socket.readyState).toBe(3);
});

it('stops even before SESSION_READY and does not send a story afterward', () => {
  const { result } = renderHook(() => usePhotoStory());
  act(() => result.current.start(photo));
  const socket = sockets[0];
  act(() => result.current.stop());
  act(() => socket.receive(event('SESSION_READY')));
  expect(socket.sent).toEqual([]);
  expect(result.current.status).toBe('idle');
});

it('reports backend errors and rejects out-of-order messages', () => {
  const { result } = renderHook(() => usePhotoStory());
  const socket = begin(result);
  act(() => socket.receive(event('ERROR', { story_id: 'story-1', code: 'STORY_UNAVAILABLE' })));
  expect(result.current.status).toBe('error');
  expect(result.current.notice).toMatch(/unavailable/i);
  act(() => result.current.start(photo));
  const next = sockets.at(-1);
  act(() => { next.receive(event('SESSION_READY')); next.receive(event('STORY_STARTED', { story_id: 's2', photo_id: photo.id })); next.receive(event('CAPTION_CHUNK', { story_id: 's2', sequence: 2, text: 'Missing first chunk' })); });
  expect(result.current.status).toBe('error');
  expect(result.current.notice).toMatch(/out of order/i);
});

it('labels demo stories and cleans up playback on unmount', () => {
  const { result, unmount } = renderHook(() => usePhotoStory());
  const socket = begin(result);
  act(() => socket.receive(event('CAPTION_CHUNK', { story_id: 'story-1', sequence: 1, text: 'Example.', source: 'demo' })));
  expect(result.current.source).toBe('demo');
  window.speechSynthesis.cancel.mockClear();
  unmount();
  expect(window.speechSynthesis.cancel).toHaveBeenCalled();
  expect(socket.readyState).toBe(3);
});
