import "./LoadingState.css";

export default function LoadingState({ messages }) {
  const text = Array.isArray(messages) ? messages[0] : messages;

  return (
    <div className="loading-state card animate-fade-in" role="status" aria-live="polite" aria-label="Processing request">
      <div className="loading-state__icon-wrapper" aria-hidden="true">
        <svg className="loading-state__icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="2" x2="12" y2="22" />
          <path d="M5 10l7-8 7 8" />
          <path d="M2 18h6a2 2 0 0 0 0-4H2" />
          <path d="M16 18h6a2 2 0 0 0 0-4h-6" />
          <line x1="5" y1="22" x2="19" y2="22" />
        </svg>
      </div>
      <div className="loading-dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <p key={text} className="loading-state__text animate-fade-in">
        {text || "Processing legal documents..."}
      </p>
    </div>
  );
}
