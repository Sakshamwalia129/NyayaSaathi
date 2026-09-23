import { useState, useEffect, useRef } from "react";
import "./CitationCard.css";

// Inline citation tag — shown inline in text
// Clicking it opens a mini panel
export default function CitationCard({ source, section, explanation, originalText }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    }

    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open]);

  return (
    <span className="citation-wrapper" ref={containerRef}>
      <button
        className="citation-tag"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label={`View source: ${source}, ${section}`}
      >
        Source: {source}{section ? `, ${section}` : ""}
      </button>

      {open && (
        <span className="citation-panel animate-fade-in" role="dialog" aria-label="Citation details">
          <span className="citation-panel__close-row">
            <span className="citation-panel__label">Citation</span>
            <button
              className="citation-panel__close"
              onClick={() => setOpen(false)}
              aria-label="Close citation panel"
            >
              ✕
            </button>
          </span>
          <span className="citation-panel__source">{source}</span>
          {section && (
            <span className="citation-panel__section">{section}</span>
          )}
          {originalText && (
            <span className="citation-panel__text">{originalText}</span>
          )}
          {explanation && (
            <span className="citation-panel__why">
              <strong>Why used:</strong> {explanation}
            </span>
          )}
        </span>
      )}
    </span>
  );
}
