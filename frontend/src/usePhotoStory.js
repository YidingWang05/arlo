import { useCallback, useEffect, useRef, useState } from 'react';
import { API_BASE } from './api.js';

function socketUrl() {
  const url = new URL(`${API_BASE}/live/ws`, window.location.href);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return url.toString();
}

const canSpeak = () => 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;

export function usePhotoStory() {
  const run = useRef(null);
  const [status, setStatus] = useState('idle');
  const [caption, setCaption] = useState('');
  const [notice, setNotice] = useState('');
  const [source, setSource] = useState('');

  const dispose = useCallback((current) => {
    if (!current) return;
    clearTimeout(current.timer);
    current.accept = false;
    current.queue.length = 0;
    current.playing = false;
    if (canSpeak()) window.speechSynthesis.cancel();
    current.socket.onmessage = null;
    current.socket.onerror = null;
    current.socket.onclose = null;
    current.socket.close();
    if (run.current === current) run.current = null;
  }, []);

  const stop = useCallback(() => {
    const current = run.current;
    // Cancel before waiting for the network acknowledgement.
    if (canSpeak()) window.speechSynthesis.cancel();
    if (!current) return;
    current.busy = true;
    current.accept = false;
    current.queue.length = 0;
    current.playing = false;
    clearTimeout(current.timer);
    setStatus('stopping');
    setNotice('Stopping the story…');
    if (current.socket.readyState === 1 && current.sessionId) {
      try {
        current.socket.send(JSON.stringify({ type: 'INTERRUPT', session_id: current.sessionId }));
        current.timer = setTimeout(() => {
          if (run.current === current) { dispose(current); setStatus('idle'); setNotice('Story stopped.'); }
        }, 3000);
        return;
      } catch { /* close below if the connection failed */ }
    }
    dispose(current);
    setStatus('idle'); setNotice('Story stopped.');
  }, [dispose]);

  const start = useCallback((photo) => {
    if (!photo?.id || !photo?.caption || run.current?.busy) return;
    dispose(run.current);
    setCaption(''); setNotice('Connecting to the story…'); setSource(''); setStatus('connecting');
    if (canSpeak()) window.speechSynthesis.cancel();
    let socket;
    try { socket = new WebSocket(socketUrl()); }
    catch { setStatus('error'); setNotice('Could not connect to the story. Please try again.'); return; }
    const current = { socket, sessionId: '', storyId: '', queue: [], playing: false, accept: true, done: false, busy: true, nextSequence: 1, timer: null };
    run.current = current;

    const fail = (message) => {
      if (run.current !== current) return;
      dispose(current); setStatus('error'); setNotice(message);
    };
    const finishIfDone = () => {
      if (current.done && !current.playing && current.queue.length === 0 && current.accept) {
        current.busy = false;
        setStatus('complete'); setNotice(!canSpeak() || current.speechFailed ? 'Story complete. Voice playback is unavailable; you can read it below.' : 'Story complete.');
      }
    };
    const playNext = () => {
      if (run.current !== current || !current.accept || current.playing) return;
      if (!canSpeak()) { current.queue.length = 0; finishIfDone(); return; }
      const text = current.queue.shift();
      if (!text) { finishIfDone(); return; }
      const utterance = new window.SpeechSynthesisUtterance(text);
      utterance.lang = /[\u4e00-\u9fff]/.test(text) ? 'zh-CN' : 'en-GB';
      utterance.rate = 0.85;
      const playingStoryId = current.storyId;
      current.playing = true;
      utterance.onend = () => { if (run.current === current && current.accept && current.storyId === playingStoryId) { current.playing = false; playNext(); } };
      utterance.onerror = (event) => {
        if (run.current !== current || !current.accept || current.storyId !== playingStoryId) return;
        current.playing = false;
        if (!['canceled', 'interrupted'].includes(event.error)) {
          current.queue.length = 0; current.speechFailed = true;
          setNotice('Voice playback is unavailable. You can read the story below.');
          finishIfDone();
        } else playNext();
      };
      try { window.speechSynthesis.speak(utterance); }
      catch { current.playing = false; current.queue.length = 0; current.speechFailed = true; setNotice('Voice playback is unavailable. You can read the story below.'); finishIfDone(); }
    };
    current.sendText = (text) => {
      clearTimeout(current.timer);
      current.accept = true; current.done = false; current.busy = true;
      current.storyId = ''; current.nextSequence = 1; current.speechFailed = false;
      current.queue.length = 0; current.playing = false;
      setCaption(''); setSource(''); setStatus('loading'); setNotice('Preparing your reply…');
      try {
        socket.send(JSON.stringify({ type: 'USER_TEXT', text, session_id: current.sessionId }));
        current.timer = setTimeout(() => fail('The reply took too long. Please try again.'), 45000);
        return true;
      } catch { fail('Could not send your question. Please try again.'); return false; }
    };
    current.timer = setTimeout(() => fail('The story connection timed out. Please try again.'), 15000);
    socket.onerror = () => fail('Could not connect to the story. Please try again.');
    socket.onclose = () => {
      if (run.current !== current) return;
      if (!current.busy) { dispose(current); setNotice('Connection closed. Start a story to ask again.'); return; }
      if (!current.accept) { dispose(current); setStatus('idle'); setNotice('Story stopped.'); }
      else fail('The story connection closed. Please try again.');
    };
    socket.onmessage = (event) => {
      if (run.current !== current) return;
      let message;
      try { message = JSON.parse(event.data); } catch { fail('The story response could not be read. Please try again.'); return; }
      if (!message || typeof message !== 'object') { fail('The story response could not be read. Please try again.'); return; }
      if (message.type === 'SESSION_READY' && current.accept && !current.sessionId && typeof message.session_id === 'string' && message.session_id.trim()) {
        clearTimeout(current.timer);
        current.sessionId = message.session_id;
        try {
          socket.send(JSON.stringify({ type: 'START_STORY', photo_id: photo.id, caption: photo.caption, session_id: current.sessionId }));
          current.timer = setTimeout(() => fail('The story took too long. Please try again.'), 45000);
          setStatus('loading'); setNotice('Preparing your story…');
        } catch { fail('Could not start the story. Please try again.'); }
        return;
      }
      if (!current.sessionId || message.session_id !== current.sessionId) return;
      if (message.type === 'PLAYBACK_STOP' && !current.accept) {
        clearTimeout(current.timer);
        current.busy = false;
        setStatus('idle'); setNotice('Story stopped.'); return;
      }
      if (!current.accept) return;
      if (message.type === 'STORY_STARTED' && typeof message.story_id === 'string' && message.story_id && message.photo_id === photo.id && !current.storyId) {
        current.storyId = message.story_id;
      } else if (message.type === 'CAPTION_CHUNK' && current.storyId && message.story_id === current.storyId && !current.done) {
        if (!Number.isInteger(message.sequence) || message.sequence !== current.nextSequence || typeof message.text !== 'string' || !message.text.trim()) {
          fail('The story arrived out of order. Please try again.'); return;
        }
        current.nextSequence += 1;
        setCaption((previous) => previous ? `${previous} ${message.text.trim()}` : message.text.trim());
        setStatus('playing');
        if (message.source === 'demo') setSource('demo');
        if (!canSpeak() || current.speechFailed) setNotice('Voice playback is unavailable. You can read the story below.');
        else { setNotice(''); current.queue.push(message.text.trim()); playNext(); }
      } else if (message.type === 'STORY_COMPLETE' && current.storyId && message.story_id === current.storyId) {
        clearTimeout(current.timer);
        current.done = true;
        if (message.source === 'demo') setSource('demo');
        // The backend verifies the provider/model; stateless calls may have no ID.
        else if (message.source === 'argon' && message.model === 'gemini-4-argon'
          && (message.interaction_id == null || (typeof message.interaction_id === 'string' && message.interaction_id.trim()))) setSource('ai');
        else setSource('unverified');
        finishIfDone();
      } else if (message.type === 'ERROR' && (!message.story_id || message.story_id === current.storyId)) {
        fail('The story is unavailable. Please try again.');
      }
    };
  }, [dispose]);

  const sendText = useCallback((text) => {
    if (typeof text !== 'string' || !text.trim() || text.length > 1000) {
      setNotice('Please enter a question of up to 1000 characters.'); return false;
    }
    const current = run.current;
    if (!current?.sessionId || current.socket.readyState !== 1) {
      setNotice('Start a story before asking about this photo.'); return false;
    }
    if (current.busy) { setNotice('Please stop the story or wait until it finishes.'); return false; }
    return current.sendText(text.trim());
  }, []);

  useEffect(() => () => dispose(run.current), [dispose]);
  const clear = useCallback(() => {
    dispose(run.current); setCaption(''); setSource(''); setStatus('idle'); setNotice('');
  }, [dispose]);
  const canAsk = Boolean(run.current?.sessionId && !run.current.busy && run.current.socket.readyState === 1);
  return { start, stop, clear, sendText, canAsk, status, caption, notice, source, active: ['connecting', 'loading', 'playing', 'stopping'].includes(status) };
}
