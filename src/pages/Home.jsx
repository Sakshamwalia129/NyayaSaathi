import { Link } from "react-router-dom";
import "./Home.css";

// --- Simple inline SVG icons ---
function CheckIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  );
}

function ScalesIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="12" y1="2" x2="12" y2="22" />
      <path d="M5 10l7-8 7 8" />
      <path d="M2 18h6a2 2 0 0 0 0-4H2" />
      <path d="M16 18h6a2 2 0 0 0 0-4h-6" />
      <line x1="5" y1="22" x2="19" y2="22" />
    </svg>
  );
}

function SourceIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="11" y1="8" x2="11" y2="14" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

// --- Process step row ---
function ProcessStep({ number, title, description, isLast }) {
  return (
    <div className="process-step">
      <div className="process-step__connector">
        <div className="process-step__number">{number}</div>
        {!isLast && <div className="process-step__line" aria-hidden="true" />}
      </div>
      <div className="process-step__content">
        <h3 className="process-step__title">{title}</h3>
        <p className="process-step__desc">{description}</p>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <main>
      {/* ======================== HERO ======================== */}
      <section className="hero" aria-labelledby="hero-heading">
        <div className="container hero__inner">
          {/* Left: text */}
          <div className="hero__text">
            <p className="eyebrow hero__eyebrow">Legal Information • Simplified</p>

            <h1 id="hero-heading" className="heading-serif hero__heading">
              Know Your Rights.<br />
              Understand the Law.
            </h1>

            <p className="hero__body">
              NyayaSaathi helps you understand legal information and court
              judgments in simple language, with every important answer connected
              to its original source.
            </p>

            <div className="hero__actions">
              <Link to="/rights-checker" className="btn-secondary hero__btn-primary">
                Check Your Rights
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>
              <Link to="/judgment-simplifier" className="btn-secondary">
                Simplify a Judgment
              </Link>
            </div>

            <p className="hero__trust">
              <span><CheckIcon /> Source-grounded</span>
              <span><CheckIcon /> Easy to understand</span>
              <span><CheckIcon /> Not a substitute for legal advice</span>
            </p>
          </div>

          {/* Right: Constitution image */}
          <div className="hero__image-wrapper" aria-label="Constitution of India">
            <div className="hero__image-frame">
              <img
                src="/assets/constitution.jpg"
                alt="Constitution of India — a burgundy book with the national emblem, hands resting on it"
                className="hero__image"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ======================== HOW IT HELPS ======================== */}
      <section className="section helps-section" aria-labelledby="helps-heading">
        <div className="container">
          <div className="section-header">
            <p className="eyebrow">What We Offer</p>
            <h2 id="helps-heading" className="heading-serif section-heading">
              How NyayaSaathi Helps
            </h2>
          </div>

          <div className="helps-grid">
            <article className="helps-card">
              <div className="helps-card__number" aria-hidden="true">01</div>
              <div className="helps-card__icon">
                <ScalesIcon />
              </div>
              <h3 className="helps-card__title">Understand Your Rights</h3>
              <p className="helps-card__body">
                Describe your situation in plain language. Get legal information
                explained clearly, without confusing jargon.
              </p>
              <Link to="/rights-checker" className="helps-card__link">
                Try Rights Checker
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>
            </article>

            <article className="helps-card">
              <div className="helps-card__number" aria-hidden="true">02</div>
              <div className="helps-card__icon">
                <DocumentIcon />
              </div>
              <h3 className="helps-card__title">Read Judgments Faster</h3>
              <p className="helps-card__body">
                Upload a court judgment and get a structured breakdown of the
                facts, arguments, decision, and key legal principles.
              </p>
              <Link to="/judgment-simplifier" className="helps-card__link">
                Try Judgment Simplifier
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>
            </article>

            <article className="helps-card">
              <div className="helps-card__number" aria-hidden="true">03</div>
              <div className="helps-card__icon">
                <SourceIcon />
              </div>
              <h3 className="helps-card__title">Trace Every Important Claim</h3>
              <p className="helps-card__body">
                Every piece of legal information is linked to its original
                source—an act, section, or judgment paragraph—so you can verify
                it yourself.
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* ======================== HOW IT WORKS ======================== */}
      <section
        id="how-it-works"
        className="section process-section"
        aria-labelledby="process-heading"
      >
        <div className="container process-inner">
          <div className="process-left">
            <p className="eyebrow">Process</p>
            <h2 id="process-heading" className="heading-serif section-heading">
              How It Works
            </h2>
            <p className="process-intro">
              NyayaSaathi is designed to be transparent about how it works.
              Every step in the process is traceable back to legal sources.
            </p>
          </div>

          <div className="process-steps">
            <ProcessStep
              number="01"
              title="Describe your situation"
              description="Tell us what happened in simple words—no legal terminology needed."
            />
            <ProcessStep
              number="02"
              title="Relevant legal sources are retrieved"
              description="NyayaSaathi identifies the relevant legal acts, sections, and precedents for your query."
            />
            <ProcessStep
              number="03"
              title="Information is explained in simple language"
              description="The legal content is summarised in plain English so you can understand what the law says."
            />
            <ProcessStep
              number="04"
              title="Sources are shown alongside the explanation"
              description="Every claim is shown with its source. You can read the original text and understand why it was used."
              isLast
            />
          </div>
        </div>
      </section>

      {/* ======================== TRUST SECTION ======================== */}
      <section className="section trust-section" aria-labelledby="trust-heading">
        <div className="container">
          <p className="eyebrow" style={{ textAlign: "center" }}>Our Approach</p>
          <h2
            id="trust-heading"
            className="heading-serif section-heading"
            style={{ textAlign: "center", marginBottom: "var(--space-4)" }}
          >
            Built around clarity and source transparency.
          </h2>
          <p className="trust-intro">
            NyayaSaathi does not claim to replace a legal professional. It is
            designed to make legal information more accessible, understandable,
            and traceable.
          </p>

          <div className="trust-grid">
            <div className="trust-item">
              <span className="trust-item__icon" aria-hidden="true">
                <CheckIcon />
              </span>
              <div>
                <h3 className="trust-item__title">Source-grounded answers</h3>
                <p className="trust-item__body">
                  Responses are linked to specific sections of Indian laws and
                  court judgments.
                </p>
              </div>
            </div>
            <div className="trust-item">
              <span className="trust-item__icon" aria-hidden="true">
                <CheckIcon />
              </span>
              <div>
                <h3 className="trust-item__title">Clear explanations</h3>
                <p className="trust-item__body">
                  Legal language is translated into accessible plain-language
                  summaries.
                </p>
              </div>
            </div>
            <div className="trust-item">
              <span className="trust-item__icon" aria-hidden="true">
                <CheckIcon />
              </span>
              <div>
                <h3 className="trust-item__title">Structured legal information</h3>
                <p className="trust-item__body">
                  Answers are organized with clear sections: situation summary,
                  legal provisions, and next steps.
                </p>
              </div>
            </div>
            <div className="trust-item">
              <span className="trust-item__icon" aria-hidden="true">
                <CheckIcon />
              </span>
              <div>
                <h3 className="trust-item__title">Persistent disclaimer</h3>
                <p className="trust-item__body">
                  NyayaSaathi clearly states on every result that it does not
                  replace qualified legal advice.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ======================== DISCLAIMER SECTION ======================== */}
      <section className="section disclaimer-section" aria-labelledby="disclaimer-heading">
        <div className="container">
          <div className="big-disclaimer">
            <div className="big-disclaimer__icon" aria-hidden="true">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <div>
              <h2
                id="disclaimer-heading"
                className="heading-serif big-disclaimer__heading"
              >
                Important Notice
              </h2>
              <p className="big-disclaimer__text">
                NyayaSaathi is designed to provide general legal information and
                help users understand legal documents. It is not a substitute
                for advice from a qualified advocate or other legal professional.
                For specific legal problems, please consult a practising
                advocate.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
