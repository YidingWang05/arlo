export const API_BASE = (import.meta.env.VITE_ARLO_API_BASE || 'http://127.0.0.1:8000/api/arlo').replace(/\/+$/, '');
export const TIMEOUT_MS = 45_000;
export const PROVENANCE = Symbol('response-provenance');

export class ArloApiError extends Error {
  constructor(message, kind = 'response') {
    super(message);
    this.name = 'ArloApiError';
    this.kind = kind;
  }
}

const object = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const text = (value) => typeof value === 'string' && value.trim().length > 0;

export function safeImageUrl(value) {
  if (!text(value)) return '';
  try {
    const url = new URL(value, 'http://localhost');
    return ['http:', 'https:'].includes(url.protocol) ? value : '';
  } catch { return ''; }
}

export function validateVision(value) {
  return object(value) && text(value.category) && text(value.headline_large)
    && text(value.audio_script) && typeof value.is_blurry === 'boolean'
    && Array.isArray(value.action_items) && value.action_items.every(text);
}

export function validateMemory(value) {
  return object(value) && text(value.spoken_prompt) && Array.isArray(value.candidates)
    && value.candidates.length === 2
    && value.candidates.every((item) => object(item) && text(item.item_id) && text(item.name)
      && Boolean(safeImageUrl(item.image_url)) && text(item.display_tag))
    && value.candidates[0].item_id !== value.candidates[1].item_id;
}

export function validatePhotos(value) {
  return Array.isArray(value) && value.every((photo) => object(photo) && text(photo.id)
    && Boolean(safeImageUrl(photo.image_url)) && text(photo.caption) && text(photo.timestamp));
}

export function parseEnvelope(body, validate) {
  if (!object(body) || !Number.isInteger(body.code) || typeof body.message !== 'string') {
    throw new ArloApiError('Arlo received an incomplete response. Please try again.');
  }
  if (body.code < 200 || body.code >= 300) {
    throw new ArloApiError('The service could not complete this request. Please try again.');
  }
  if (!Object.hasOwn(body, 'data') || !validate(body.data)) {
    throw new ArloApiError('Arlo could not read the result. Please try again.');
  }
  // The scaffold silently substitutes mock results. Unmarked results must stay visibly unverified.
  // Optional future metadata is additive; the existing BaseResponse contract still works.
  const meta = body.meta;
  const source = object(meta) && meta.source === 'gemini' && text(meta.interaction_id)
    && meta.is_mock !== true ? 'gemini' : 'unverified';
  Object.defineProperty(body.data, PROVENANCE, { value: source, configurable: true });
  return body.data;
}

export async function requestData(path, { validate, signal, timeoutMs = TIMEOUT_MS, ...options } = {}) {
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener('abort', abort, { once: true });
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...options, signal: controller.signal });
    if (!response.ok) {
      const message = response.status === 413 ? 'This photo is too large. Please choose a smaller one.'
        : response.status === 429 ? 'Arlo is busy right now. Wait a moment, then try again.'
          : response.status >= 500 ? 'The Arlo service is unavailable. Please try again shortly.'
            : `This request could not be completed (HTTP ${response.status}). Please try again.`;
      throw new ArloApiError(message, 'http');
    }
    let body;
    try { body = await response.json(); }
    catch (error) {
      if (controller.signal.aborted) throw error;
      throw new ArloApiError('The service returned an unreadable response. Please try again.');
    }
    return parseEnvelope(body, validate);
  } catch (error) {
    if (timedOut) throw new ArloApiError('This is taking too long. Please try again when you are ready.', 'timeout');
    if (signal?.aborted) throw new DOMException('Request cancelled', 'AbortError');
    if (error instanceof ArloApiError) throw error;
    throw new ArloApiError('Cannot reach Arlo. Check your connection and that the backend is running.', 'offline');
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', abort);
  }
}

export const getPhotos = (signal) => requestData('/frame/photos', { validate: validatePhotos, signal });

export function explainLabel(file, signal) {
  const body = new FormData();
  body.append('file', file);
  body.append('query', 'Explain only the instructions visible on this label. Do not infer missing dosage. If the image is unreadable, ask for a clearer photo.');
  return requestData('/vision/explain', { method: 'POST', body, validate: validateVision, signal });
}

export function findProducts(query, signal) {
  return requestData('/memory/buy', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ speech_query: query.trim() }), validate: validateMemory, signal,
  });
}
