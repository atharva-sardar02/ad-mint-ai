import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Filter out browser extension console errors
if (typeof window !== 'undefined') {
  const originalError = console.error;
  const originalWarn = console.warn;
  const originalLog = console.log;

  const shouldIgnore = (message: any): boolean => {
    const messageStr = String(message);
    return (
      messageStr.includes('ResumeSwitcher') ||
      messageStr.includes('autofillInstance') ||
      messageStr.includes('updateFilling Resume') ||
      messageStr.includes('chrome-extension://') ||
      messageStr.includes('userReportLinkedCandidate')
    );
  };

  console.error = (...args: any[]) => {
    if (!shouldIgnore(args[0])) {
      originalError.apply(console, args);
    }
  };

  console.warn = (...args: any[]) => {
    if (!shouldIgnore(args[0])) {
      originalWarn.apply(console, args);
    }
  };

  console.log = (...args: any[]) => {
    if (!shouldIgnore(args[0])) {
      originalLog.apply(console, args);
    }
  };
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
