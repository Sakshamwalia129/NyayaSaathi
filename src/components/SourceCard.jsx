import { useState } from "react";
import "./SourceCard.css";

export default function SourceCard({ provision, citationNumber }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className="source-card card animate-fade-in" aria-label={`Source: ${provision.source}`}>
      <div className="source-card__header">
        <div className="source-card__meta">
          <span className="source-card__badge">
            [{citationNumber}] Source
          </span>
          <h3 className="source-card__title">{provision.source}</h3>
          <p className="source-card__section">{provision.section}</p>
        </div>
        {/* Scales icon */}
        <span className="source-card__icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="2" x2="12" y2="22" />
            <path d="M5 10l7-8 7 8" />
            <path d="M2 18h6a2 2 0 0 0 0-4H2" />
            <path d="M16 18h6a2 2 0 0 0 0-4h-6" />
            <line x1="5" y1="22" x2="19" y2="22" />
          </svg>
        </span>
      </div>

      <p className="source-card__summary">{provision.summary}</p>

      {/* Expand button */}
      <button
        className="source-card__expand-btn btn-ghost"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        aria-controls={`source-text-${provision.id}`}
      >
        {expanded ? "Hide original text" : "View original text"}
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`source-card__chevron${expanded ? " source-card__chevron--up" : ""}`}
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Expanded original text */}
      {expanded && (
        <div
          id={`source-text-${provision.id}`}
          className="source-card__original animate-fade-in"
        >
          <p className="source-card__original-label">Original Text (Sample)</p>
          <blockquote className="source-card__blockquote">
            {provision.originalText}
          </blockquote>
          <p className="source-card__why">
            <strong>Why this source:</strong> {provision.whyUsed}
          </p>
        </div>
      )}
    </article>
  );
}
