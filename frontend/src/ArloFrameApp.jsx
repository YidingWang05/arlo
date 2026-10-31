import { useCallback, useEffect, useRef, useState } from 'react';
import { explainLabel, findProducts, getPhotos, PROVENANCE, safeImageUrl } from './api.js';
import { demoMemory, demoPhotos, demoVision } from './demo.js';
import { useSpeech } from './useSpeech.js';

function Icon({ name, size = 28 }) {
  const paths = {
    arrow: <><path d="m9 5 7 7-7 7" /><path d="M4 12h12" /></>,
    back: <><path d="m12 5-7 7 7 7" /><path d="M5 12h15" /></>,
    camera: <><path d="m8 5 1-2h6l1 2h4v15H4V5Z" /><circle cx="12" cy="12" r="4" /></>,
    photo: <><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="9" cy="9" r="2" /><path d="m3 18 6-5 4 3 4-5 4 4" /></>,
    bag: <><path d="M5 7h14l1 14H4L5 7Z" /><path d="M8 8V6a4 4 0 0 1 8 0v2" /></>,
    sound: <><path d="m11 4-6 5H2v6h3l6 5Z" /><path d="M15 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14" /></>,
    stop: <rect x="5" y="5" width="14" height="14" rx="2" />,
    mic: <><rect x="9" y="2" width="6" height="13" rx="3" /><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3m-4 0h8" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    leaf: <><path d="M20 3C9 1 1 9 5 16c7 7 16 0 15-13Z" /><path d="M4 21 15 9" /></>,
    pause: <><path d="M8 5v14M16 5v14" /></>,
    play: <path d="m8 4 12 8-12 8Z" />,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.leaf}</svg>;
}

function Image({ src, alt, className = '' }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);
  return failed || !safeImageUrl(src)
    ? <div className={`image-placeholder ${className}`} role="img" aria-label={`${alt}. Image unavailable.`}><Icon name="photo" size={48} /><span>Image unavailable</span></div>
    : <img className={className} src={src} alt={alt} onError={() => setFailed(true)} referrerPolicy="no-referrer" />;
}

function SpeechControls({ text, speech }) {
  return <div className="speech-area">
    {speech.supported ? <div className="button-row">
      <button className="button secondary" onClick={() => speech.speak(text)} disabled={speech.speaking}><Icon name="sound" />Read aloud</button>
      <button className="button quiet" onClick={speech.stop}><Icon name="stop" />Stop speaking</button>
    </div> : <p className="small-note">Your browser does not offer voice playback. All information is shown here.</p>}
    <span role="status" className="small-note">{speech.speaking ? 'Reading aloud…' : speech.message}</span>
  </div>;
}

function ResultNotice({ result, demo }) {
  if (demo) return null;
  return result[PROVENANCE] === 'gemini'
    ? <p className="source-label"><span className="status-dot" />AI response · Check against the original</p>
    : <div className="data-notice"><strong>Demo data — backend source unverified</strong><span>The service has not identified this as a real AI result. Treat it as a demonstration only.</span></div>;
}

function ErrorPanel({ error, retry, back }) {
  return <div className="error-panel">
    <div role="alert"><h2>Let’s try that again.</h2><p>{error}</p></div>
    <div className="button-row"><button className="button primary" onClick={retry}>Retry<Icon name="arrow" /></button><button className="button quiet" onClick={back}>Back</button></div>
  </div>;
}

export default function ArloFrameApp() {
  const [screen, setScreen] = useState('ambient');
  const [demo, setDemo] = useState(false);
  const [photos, setPhotos] = useState([]);
  const [albumState, setAlbumState] = useState('loading');
  const [albumError, setAlbumError] = useState('');
  const [albumAttempt, setAlbumAttempt] = useState(0);
  const [photoIndex, setPhotoIndex] = useState(0);
  const [rotate, setRotate] = useState(false);
  const [now, setNow] = useState(new Date());
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [fileError, setFileError] = useState('');
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [listening, setListening] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState('');
  const request = useRef(null);
  const recognition = useRef(null);
  const heading = useRef(null);
  const firstRender = useRef(true);
  const speech = useSpeech();
  const Recognition = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition);
  const visiblePhoto = photos[photoIndex % Math.max(photos.length, 1)];

  const stopRecognition = useCallback(() => {
    if (recognition.current) {
      const previous = recognition.current;
      recognition.current = null;
      previous.onresult = null;
      previous.onend = null;
      previous.onerror = null;
      previous.abort();
    }
    setListening(false);
  }, []);

  const navigate = useCallback((next) => {
    request.current?.abort();
    request.current = null;
    stopRecognition();
    speech.stop();
    setLoading(false);
    setError('');
    setResult(null);
    setSelected(null);
    setVoiceMessage('');
    setScreen(next);
  }, [speech.stop, stopRecognition]);

  const back = useCallback(() => {
    if (selected) { speech.stop(); setSelected(null); }
    else if (result || error || loading) {
      request.current?.abort(); request.current = null;
      speech.stop(); setResult(null); setError(''); setLoading(false);
    } else navigate(screen === 'home' ? 'ambient' : 'home');
  }, [selected, result, error, loading, screen, navigate, speech.stop]);

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') {
        if (listening) { stopRecognition(); return; }
        if (speech.speaking) { speech.stop(); return; }
        if (screen !== 'ambient') back();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [back, screen, listening, speech.speaking, speech.stop, stopRecognition]);

  useEffect(() => {
    if (firstRender.current) { firstRender.current = false; return; }
    heading.current?.focus();
  }, [screen, result, selected, error]);

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 30_000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setAlbumState('loading'); setAlbumError(''); setPhotoIndex(0);
    if (demo) { setPhotos(demoPhotos); setAlbumState('ready'); return () => controller.abort(); }
    setPhotos([]);
    getPhotos(controller.signal).then((items) => {
      if (!controller.signal.aborted) { setPhotos(items); setAlbumState('ready'); }
    }).catch((err) => {
      if (err.name !== 'AbortError') { setAlbumError(err.message); setAlbumState('error'); }
    });
    return () => controller.abort();
  }, [demo, albumAttempt]);

  useEffect(() => {
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (!rotate || photos.length < 2 || screen !== 'ambient' || motion.matches) return;
    const timer = setInterval(() => setPhotoIndex((value) => (value + 1) % photos.length), 20_000);
    const onChange = () => { if (motion.matches) { clearInterval(timer); setRotate(false); } };
    motion.addEventListener('change', onChange);
    return () => { clearInterval(timer); motion.removeEventListener('change', onChange); };
  }, [rotate, photos.length, screen]);

  useEffect(() => {
    if (!file) { setPreview(''); return; }
    const url = URL.createObjectURL(file); setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => () => { request.current?.abort(); recognition.current?.abort(); }, []);

  function chooseFile(event) {
    const next = event.target.files?.[0]; event.target.value = '';
    if (!next) return;
    setFileError(''); setResult(null); setError('');
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(next.type)) {
      setFile(null); setFileError('Please choose a JPEG, PNG, or WEBP photo.'); return;
    }
    if (next.size > 10 * 1024 * 1024) {
      setFile(null); setFileError('Please choose a photo smaller than 10 MB.'); return;
    }
    setFile(next);
  }

  async function submit(event) {
    event?.preventDefault();
    if (loading || (screen === 'vision' ? !file : !query.trim())) return;
    speech.stop(); stopRecognition(); setError(''); setResult(null); setSelected(null); setLoading(true);
    const controller = new AbortController(); request.current?.abort(); request.current = controller;
    try {
      const data = demo ? (screen === 'vision' ? demoVision : demoMemory)
        : screen === 'vision' ? await explainLabel(file, controller.signal) : await findProducts(query, controller.signal);
      if (!controller.signal.aborted) setResult(data);
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message);
    } finally {
      if (request.current === controller) { request.current = null; setLoading(false); }
    }
  }

  function startListening() {
    if (!Recognition || listening) return;
    speech.stop(); setVoiceMessage('');
    const instance = new Recognition();
    instance.lang = 'en-GB'; instance.interimResults = false; instance.continuous = false;
    instance.onresult = (event) => {
      if (recognition.current !== instance) return;
      const transcript = event.results?.[0]?.[0]?.transcript;
      if (transcript) { setQuery(transcript); setVoiceMessage('Check your words, then choose Find my product.'); }
    };
    instance.onend = () => { if (recognition.current === instance) { recognition.current = null; setListening(false); } };
    instance.onerror = (event) => {
      if (recognition.current !== instance) return;
      setVoiceMessage(event.error === 'not-allowed' ? 'Microphone access was not allowed. You can type your request instead.' : 'We could not hear that. Please try again or type your request.');
      setListening(false);
    };
    recognition.current = instance;
    try { instance.start(); setListening(true); }
    catch { setListening(false); setVoiceMessage('Voice input is unavailable. Please type your request.'); }
  }

  const title = screen === 'home' ? 'A little help, whenever you need it.'
    : screen === 'vision' ? result ? (result.is_blurry ? 'Let’s take a clearer photo.' : 'Here’s what the label says.') : 'Let’s make the small print clear.'
      : selected ? 'You’ve chosen your product.' : result ? 'Which one looks familiar?' : 'You don’t need to remember the name.';

  return <div className={`arlo-app ${screen === 'ambient' ? 'ambient-app' : ''}`}>
    <a className="skip-link" href="#main">Skip to content</a>
    {demo && <div className="demo-banner" role="status"><strong>Demo data - backend unavailable</strong><span>Local examples only. No live AI or purchases.</span></div>}
    <header className="app-header">
      <span className="wordmark"><Icon name="leaf" size={31} />arlo<span className="brand-dot">.</span></span>
      <span className="header-tagline">A little help. More independence.</span>
      {screen !== 'ambient' && <button className="button quiet back-button" onClick={back}><Icon name="back" />Back</button>}
    </header>

    {screen === 'ambient' ? <main id="main" className="ambient-main">
      <section className={`photo-frame ${visiblePhoto ? 'has-photo' : 'empty-frame'}`} aria-label="Family photo frame">
        {visiblePhoto && <Image src={visiblePhoto.image_url} alt={visiblePhoto.caption} className="ambient-photo" />}
        <div className="photo-shade" />
        <div className="ambient-top"><span className="eyebrow">YOUR EVERYDAY COMPANION</span><time dateTime={now.toISOString()} className="ambient-date">{now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })}</time></div>
        <div className="ambient-content">
          <time className="clock" dateTime={now.toISOString()}>{now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}</time>
          <h1 ref={heading} tabIndex={-1}>{visiblePhoto ? visiblePhoto.caption : 'Make room for a lovely day.'}</h1>
          {!visiblePhoto && <div className="album-status" role="status">
            {albumState === 'loading' ? 'Opening your family album…' : albumState === 'error' ? albumError : 'Your family photos will appear here.'}
          </div>}
          {albumState === 'error' && <button className="button frame-secondary" onClick={() => setAlbumAttempt((value) => value + 1)}>Retry album</button>}
        </div>
        <div className="ambient-bottom">
          <span className="frame-note"><span className="status-dot" />{visiblePhoto ? 'A moment to keep close' : 'Here when you need a hand'}</span>
          <button className="button ask-button" onClick={() => navigate('home')}>Ask Arlo<Icon name="arrow" /></button>
        </div>
      </section>
      {photos.length > 1 && <div className="album-controls"><button className="button quiet" onClick={() => setPhotoIndex((value) => (value + 1) % photos.length)}>Next photo<Icon name="arrow" /></button><button className="button quiet" aria-pressed={rotate} onClick={() => setRotate((value) => !value)}><Icon name={rotate ? 'pause' : 'play'} />{rotate ? 'Pause photos' : 'Rotate photos'}</button></div>}
    </main> : <main id="main" className="inspector-main">
      <div className="intro"><p className="eyebrow">{screen === 'home' ? 'LET’S TAKE IT ONE STEP AT A TIME' : screen === 'vision' ? 'EXPLAIN THIS LABEL' : 'FIND A FAMILIAR PRODUCT'}</p><h1 ref={heading} tabIndex={-1}>{title}</h1></div>

      {screen === 'home' && <div className="home-choices">
        <button className="choice-card vision-choice" onClick={() => navigate('vision')}><span className="choice-icon"><Icon name="camera" size={56} /></span><span className="choice-title">Explain this label</span><span className="choice-description">Show me the small print.<br />We’ll read it together.</span><span className="choice-end">Take or upload a photo<Icon name="arrow" /></span></button>
        <button className="choice-card buy-choice" onClick={() => navigate('memory')}><span className="choice-icon"><Icon name="bag" size={56} /></span><span className="choice-title">Help me find a product</span><span className="choice-description">A colour. A shape.<br />Tell me what you remember.</span><span className="choice-end">Describe what you need<Icon name="arrow" /></span></button>
      </div>}

      {error && <ErrorPanel error={error} retry={submit} back={back} />}
      {loading && <div className="loading-panel" role="status"><span className="loader" aria-hidden="true" /><h2>{screen === 'vision' ? 'Reading the visible label…' : 'Looking for two familiar options…'}</h2><p>Take your time. This may take up to 45 seconds.</p><button className="button quiet" onClick={back}>Cancel</button></div>}

      {screen === 'vision' && !loading && !error && !result && <form className="vision-layout" onSubmit={submit}>
        <div className={`upload-preview ${preview ? 'with-preview' : ''}`}>
          {preview ? <img src={preview} alt="Your selected label, ready to explain" /> : <><span className="upload-icon"><Icon name="camera" size={70} /></span><h2>A closer look.</h2><p>Keep the whole label in view,<br />with good light and no glare.</p></>}
        </div>
        <div className="upload-actions"><h2>{file ? 'Ready when you are.' : 'Start with a clear photo.'}</h2><p>{file ? file.name : 'A medicine label, a household notice, or instructions you’d like to read.'}</p>
          <div className="upload-buttons"><label className="button secondary file-button"><Icon name="camera" />Take a photo<input aria-label="Take a photo" type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={chooseFile} /></label><label className="button quiet file-button"><Icon name="photo" />{file ? 'Choose another photo' : 'Upload a photo'}<input aria-label="Upload a photo" type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseFile} /></label></div>
          {fileError && <p role="alert" className="inline-error">{fileError}</p>}
          <button className="button primary wide" type="submit" disabled={!file}>Explain this label<Icon name="arrow" /></button>
          <p className="small-note">JPEG, PNG or WEBP · Up to 10 MB<br />Only sent when you choose Explain this label.</p>
        </div>
      </form>}

      {screen === 'vision' && result && !error && <div className="vision-result">
        <ResultNotice result={result} demo={demo} />
        <div className="result-layout">
          {preview && <img className="result-preview" src={preview} alt="Original label for comparison" />}
          <section className="result-copy" aria-label="Label explanation" aria-live="polite">
            <span className="source-label">{result.is_blurry ? 'PHOTO NEEDS ANOTHER LOOK' : result.category}</span>
            <h2 className="takeaway">{result.is_blurry ? 'Some words are not clear enough to read.' : result.headline_large}</h2>
            {result.is_blurry ? <><p>Try better light, hold the camera steady, and include the whole label.</p><button className="button primary" onClick={() => { speech.stop(); setResult(null); setFile(null); }}>Retake photo<Icon name="camera" /></button></> : <><ul className="action-list">{result.action_items.map((item, index) => <li key={`${index}-${item}`}><span className="check-icon"><Icon name="check" /></span>{item}</li>)}</ul><p className="spoken-script">{result.audio_script}</p><SpeechControls text={result.audio_script} speech={speech} /><button className="button quiet" onClick={() => { speech.stop(); setResult(null); setFile(null); }}>Read another label<Icon name="arrow" /></button></>}
            <p className="small-note">Check the original label. Ask a pharmacist about unclear medicine instructions.</p>
          </section>
        </div>
      </div>}

      {screen === 'memory' && !result && !error && !loading && <form className="memory-form" onSubmit={submit}>
        <label htmlFor="product-query">What do you remember?</label>
        <textarea id="product-query" rows={3} maxLength={1000} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="the blue bottle my daughter bought" aria-describedby="query-help" />
        <p id="query-help">A colour, a shape, or who bought it is a good place to start.</p>
        <div className="memory-actions">
          {Recognition && <button type="button" className="button secondary" onClick={listening ? stopRecognition : startListening}><Icon name={listening ? 'stop' : 'mic'} />{listening ? 'Stop listening' : 'Speak your request'}</button>}
          <button type="submit" className="button primary" disabled={!query.trim() || listening}>Find my product<Icon name="arrow" /></button>
        </div>
        <p role="status" className="small-note">{listening ? 'Listening… Say what you remember.' : voiceMessage || (Recognition ? 'Optional voice input uses your browser’s speech service.' : 'Voice input is not available in this browser. You can type instead.')}</p>
      </form>}

      {screen === 'memory' && result && !error && <div className="memory-result">
        <ResultNotice result={result} demo={demo} />
        {!selected ? <><p className="spoken-prompt" aria-live="polite">{result.spoken_prompt}</p><div className="product-grid">{result.candidates.map((item, index) => <button className="product-card" key={item.item_id} onClick={() => { speech.stop(); setSelected({ ...item, letter: index === 0 ? 'A' : 'B' }); }}><span className="option-letter">{index === 0 ? 'A' : 'B'}</span><Image src={item.image_url} alt={item.name} className="product-image" /><span className="product-copy"><span className="product-name">{item.name}</span><span className="display-tag">{item.display_tag}</span><span className="product-select">Choose {index === 0 ? 'A' : 'B'}<Icon name="arrow" /></span></span></button>)}</div><SpeechControls text={result.spoken_prompt} speech={speech} /></>
          : <section className="confirmation" aria-live="polite"><div className="confirmation-badge"><Icon name="check" size={40} /></div><p className="eyebrow">YOU SELECTED OPTION {selected.letter}</p><h2 className="takeaway">{selected.name}</h2><p>Nothing has been ordered or paid for.</p><div className="button-row"><button className="button primary" onClick={() => navigate('ambient')}>Back to my frame<Icon name="photo" /></button><button className="button quiet" onClick={() => setSelected(null)}>Choose again</button></div></section>}
      </div>}
    </main>}
    <footer className="app-footer"><span>Made for your pace.</span><label className="demo-toggle"><input type="checkbox" checked={demo} onChange={(event) => { navigate('ambient'); setDemo(event.target.checked); }} />Use demo data</label></footer>
  </div>;
}
