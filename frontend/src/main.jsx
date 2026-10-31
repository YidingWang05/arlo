import React from 'react';
import { createRoot } from 'react-dom/client';
import ArloFrameApp from './ArloFrameApp.jsx';
import './styles.css';

createRoot(document.getElementById('root')).render(
  <React.StrictMode><ArloFrameApp /></React.StrictMode>,
);
