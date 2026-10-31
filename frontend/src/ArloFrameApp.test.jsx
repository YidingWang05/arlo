import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import ArloFrameApp from './ArloFrameApp.jsx';
import { demoMemory, demoVision } from './demo.js';

function mockApi({ vision = demoVision, failMemory = false, meta = undefined } = {}) {
  const fetchMock = vi.fn(async (url) => {
    if (url.endsWith('/memory/buy') && failMemory) throw new TypeError('offline');
    const data = url.endsWith('/frame/photos') ? [] : url.endsWith('/vision/explain') ? vision : demoMemory;
    return { ok: true, json: async () => ({ code: 200, message: 'success', data: structuredClone(data), meta }) };
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}
async function openFlow(user, label) {
  render(<ArloFrameApp />);
  await user.click(screen.getByRole('button', { name: /Ask Arlo/ }));
  await user.click(screen.getByRole('button', { name: label }));
}
async function uploadLabel(user) {
  const file = new File(['label'], 'label.png', { type: 'image/png' });
  await user.upload(screen.getByLabelText('Upload a photo'), file);
  await user.click(screen.getByRole('button', { name: /Explain this label/ }));
  return file;
}

it('uploads a label, displays the result, and speaks only on request with immediate stop', async () => {
  const fetchMock = mockApi(); const user = userEvent.setup();
  await openFlow(user, /Explain this label/);
  const file = await uploadLabel(user);
  expect(await screen.findByRole('heading', { name: demoVision.headline_large })).toBeVisible();
  const [, options] = fetchMock.mock.calls.find(([url]) => url.endsWith('/vision/explain'));
  expect(options.method).toBe('POST');
  expect(options.body.get('file')).toBe(file);
  expect(options.body.get('query')).toContain('Do not infer missing dosage');
  expect(screen.getByText('Result source unverified')).toBeVisible();
  expect(window.speechSynthesis.speak).not.toHaveBeenCalled();
  expect(screen.getByRole('heading', { level: 1 })).toHaveFocus();
  await user.click(screen.getByRole('button', { name: 'Read aloud' }));
  expect(window.speechSynthesis.speak.mock.calls[0][0].text).toBe(demoVision.audio_script);
  window.speechSynthesis.cancel.mockClear();
  await user.click(screen.getByRole('button', { name: 'Stop speaking' }));
  expect(window.speechSynthesis.cancel).toHaveBeenCalledTimes(1);
});

it.each([
  [{ source: 'keyword', is_mock: false }, 'Keyword matching'],
  [{ source: 'local', is_mock: false }, 'Local result'],
  [{ source: 'gemini', is_mock: false, interaction_id: 'id-123' }, 'AI response'],
  [{ source: 'demo', is_mock: true }, 'Demo data — not a live AI result'],
  [{ source: 'gemini', is_mock: false, interaction_id: null }, 'Result source unverified'],
])('shows the correct visible source for backend metadata %j', async (meta, notice) => {
  mockApi({ meta }); const user = userEvent.setup();
  await openFlow(user, /Help me find a product/);
  await user.type(screen.getByLabelText('What do you remember?'), 'blue bottle');
  await user.click(screen.getByRole('button', { name: /Find my product/ }));
  expect(await screen.findByText(notice)).toBeVisible();
  if (['keyword', 'local', 'gemini'].includes(meta.source) && notice !== 'Result source unverified') {
    expect(screen.getByText(/sample household catalogue; not verified purchase history/i)).toBeVisible();
  }
});

it('offers retake and hides potentially unsafe instructions for a blurry image', async () => {
  mockApi({ vision: { ...demoVision, is_blurry: true, headline_large: 'UNREADABLE DOSAGE' } });
  const user = userEvent.setup(); await openFlow(user, /Explain this label/); await uploadLabel(user);
  expect(await screen.findByRole('button', { name: /Retake photo/ })).toBeVisible();
  expect(screen.queryByText('UNREADABLE DOSAGE')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: /Retake photo/ }));
  expect(screen.getByRole('button', { name: /Explain this label/ })).toBeDisabled();
});

it('posts the fuzzy query, offers exactly two cards, and confirms one choice without a purchase', async () => {
  const fetchMock = mockApi(); const user = userEvent.setup();
  await openFlow(user, /Help me find a product/);
  await user.type(screen.getByLabelText('What do you remember?'), 'the blue bottle my daughter bought');
  await user.click(screen.getByRole('button', { name: /Find my product/ }));
  const cards = await screen.findAllByRole('button', { name: /Choose [AB]/ });
  expect(cards).toHaveLength(2);
  const [, options] = fetchMock.mock.calls.find(([url]) => url.endsWith('/memory/buy'));
  expect(JSON.parse(options.body)).toEqual({ speech_query: 'the blue bottle my daughter bought' });
  await user.click(cards[1]);
  expect(screen.getByText('YOU SELECTED OPTION B')).toBeVisible();
  expect(screen.getByText('Nothing has been ordered or paid for.')).toBeVisible();
  fireEvent.keyDown(window, { key: 'Escape' });
  expect(screen.getAllByRole('button', { name: /Choose [AB]/ })).toHaveLength(2);
  expect(screen.getByRole('heading', { level: 1 })).toHaveFocus();
});

it('shows backend failure, waits for manual retry, and keeps demo mode opt-in', async () => {
  const fetchMock = mockApi({ failMemory: true }); const user = userEvent.setup();
  await openFlow(user, /Help me find a product/);
  expect(screen.getByRole('checkbox', { name: 'Use demo data' })).not.toBeChecked();
  await user.type(screen.getByLabelText('What do you remember?'), 'blue bottle');
  await user.click(screen.getByRole('button', { name: /Find my product/ }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach Arlo');
  expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/memory/buy'))).toHaveLength(1);
  await user.click(screen.getByRole('button', { name: 'Retry' }));
  await waitFor(() => expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/memory/buy'))).toHaveLength(2));
  expect(await screen.findByRole('alert')).toBeVisible();
  await user.click(screen.getByRole('checkbox', { name: 'Use demo data' }));
  expect(screen.getByText('Demo data - backend unavailable')).toBeVisible();
});
