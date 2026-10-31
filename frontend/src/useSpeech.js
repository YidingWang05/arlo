import { useCallback, useEffect, useState } from 'react';

export function useSpeech() {
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
  const [speaking, setSpeaking] = useState(false);
  const [message, setMessage] = useState('');
  const stop = useCallback(() => {
    if (supported) window.speechSynthesis.cancel();
    setSpeaking(false);
    setMessage('');
  }, [supported]);
  const speak = useCallback((text) => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.lang = /[\u4e00-\u9fff]/.test(text) ? 'zh-CN' : 'en-GB';
    utterance.rate = 0.85;
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => { setSpeaking(false); setMessage('Finished reading.'); };
    utterance.onerror = (event) => {
      setSpeaking(false);
      if (!['canceled', 'interrupted'].includes(event.error)) setMessage('Voice playback is unavailable. You can read the text on screen.');
    };
    setMessage('');
    setSpeaking(true);
    try { window.speechSynthesis.speak(utterance); }
    catch { setSpeaking(false); setMessage('Voice playback is unavailable. You can read the text on screen.'); }
  }, [supported]);
  useEffect(() => () => { if (supported) window.speechSynthesis.cancel(); }, [supported]);
  return { supported, speaking, message, speak, stop };
}
