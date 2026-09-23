import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  simplifyJudgment,
  getJudgmentHistory,
} from "../services/legalService";
import FileUpload from "../components/FileUpload";
import LoadingState from "../components/LoadingState";
import Disclaimer from "../components/Disclaimer";
import "./JudgmentSimplifier.css";

const LOADING_MESSAGES = [
  "Reading judgment...",
  "Identifying key paragraphs...",
  "Preparing simplified explanation...",
];

// A single paragraph card on the right panel
function ParagraphCard({ para, onHighlight }) {
  return (
    <article
      id={`para-card-${para.id}`}
      className={`para-card${para.highlighted ? " para-card--highlighted" : ""
        }`}
      aria-label={para.number}
    >
      <p className="para-card__number">{para.number}</p>

      <blockquote className="para-card__text">
        "{para.text}"
      </blockquote>

      <button
        type="button"
        className="btn-ghost para-card__btn"
        onClick={() => onHighlight(para.id)}
        aria-pressed={para.highlighted}
      >
        {para.highlighted
          ? "Highlighted"
          : "View in judgment"}
      </button>
    </article>
  );
}

export default function JudgmentSimplifier() {
  const { user, loading: authLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState(
    LOADING_MESSAGES[0]
  );
  const [result, setResult] = useState(null);
  const [paragraphs, setParagraphs] = useState([]);
  const [error, setError] = useState("");

  // PostgreSQL history
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // ============================================================
  // LOAD SAVED HISTORY (USER-SPECIFIC)
  // ============================================================

  useEffect(() => {
    if (authLoading || !user) return;

    let isMounted = true;
    async function loadHistory() {
      setHistoryLoading(true);
      try {
        const response = await getJudgmentHistory();
        if (isMounted) {
          setHistory(response?.data || []);
        }
      } catch (err) {
        console.error("Failed to load judgment history:", err);
      } finally {
        if (isMounted) {
          setHistoryLoading(false);
        }
      }
    }

    loadHistory();
    return () => {
      isMounted = false;
    };
  }, [user, authLoading]);



  // ============================================================
  // FILE HANDLING
  // ============================================================

  function handleFileChange(f) {
    setFile(f);
    setResult(null);
    setParagraphs([]);
    setError("");
  }

  function handleFileRemove() {
    setFile(null);
    setResult(null);
    setParagraphs([]);
    setError("");
  }

  // ============================================================
  // ANALYZE JUDGMENT
  // ============================================================

  async function handleAnalyze() {
    if (!user) {
      navigate("/login", { state: { from: location } });
      return;
    }

    if (!file) {
      setError(
        "Please select a PDF or text file."
      );
      return;
    }

    setError("");
    setLoading(true);
    setResult(null);

    let msgIdx = 0;

    setLoadingMsg(LOADING_MESSAGES[0]);

    const msgInterval = setInterval(() => {
      msgIdx =
        (msgIdx + 1) %
        LOADING_MESSAGES.length;

      setLoadingMsg(
        LOADING_MESSAGES[msgIdx]
      );
    }, 1200);

    try {
      const response =
        await simplifyJudgment(file);

      clearInterval(msgInterval);

      setResult(response.data);

      setParagraphs(
        (response.data?.paragraphs || []).map(
          (paragraph) => ({
            ...paragraph,
            highlighted: false,
          })
        )
      );

      // Refresh PostgreSQL history
      try {
        const historyResponse =
          await getJudgmentHistory();

        setHistory(
          historyResponse?.data || []
        );
      } catch (historyError) {
        console.error(
          "Failed to refresh judgment history:",
          historyError
        );
      }
    } catch (err) {
      clearInterval(msgInterval);

      setError(
        err?.message ||
        "Something went wrong while analyzing the judgment. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  // ============================================================
  // OPEN SAVED HISTORY ITEM
  // ============================================================

  function handleHistoryClick(item) {
    const savedResult =
      item.response?.data;

    if (!savedResult) {
      return;
    }

    setFile(null);
    setResult(savedResult);
    setError("");

    setParagraphs(
      (savedResult.paragraphs || []).map(
        (paragraph) => ({
          ...paragraph,
          highlighted: false,
        })
      )
    );

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  // ============================================================
  // PARAGRAPH HIGHLIGHT
  // ============================================================

  function handleHighlight(id) {
    setParagraphs((prev) =>
      prev.map((paragraph) => ({
        ...paragraph,
        highlighted:
          paragraph.id === id
            ? !paragraph.highlighted
            : false,
      }))
    );

    setTimeout(() => {
      const element =
        document.getElementById(
          `para-card-${id}`
        );

      if (element) {
        element.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }
    }, 50);
  }

  // ============================================================
  // RESET
  // ============================================================

  function handleReset() {
    setFile(null);
    setResult(null);
    setParagraphs([]);
    setError("");
  }

  return (
    <main className="simplifier-page">
      <div className="container">

        {/* Unauthenticated requirement prompt */}
        {!user && !authLoading && (
          <div className="card" style={{ marginBottom: "2rem", padding: "1.5rem", borderLeft: "4px solid #c5a059" }}>
            <h3 style={{ fontFamily: "Playfair Display, serif", margin: "0 0 0.5rem 0", color: "#1b365d" }}>
              Sign In to Save Your Activity
            </h3>
            <p style={{ color: "#6b7280", margin: "0 0 1rem 0", fontSize: "0.95rem" }}>
              Signing in lets you upload judgments for simplified legal analysis and access your saved judgment history.
            </p>
            <Link to="/login" state={{ from: location }} className="btn-primary" style={{ display: "inline-block" }}>
              Sign In to NyayaSaathi
            </Link>
          </div>
        )}

        {/* =====================================================
            SAVED HISTORY
        ===================================================== */}

        {user && (historyLoading ||
          history.length > 0) && (

            <section
              className="judgment-history"
              aria-labelledby="judgment-history-heading"
            >
              <div className="judgment-history__header">
                <div>
                  <p className="eyebrow">
                    Saved Activity
                  </p>

                  <h2
                    id="judgment-history-heading"
                    className="heading-serif judgment-history__title"
                  >
                    Previous Judgment Analyses
                  </h2>
                </div>

                {!historyLoading && (
                  <span className="judgment-history__count">
                    {history.length} saved
                  </span>
                )}
              </div>

              {historyLoading ? (
                <p className="judgment-history__loading">
                  Loading previous analyses...
                </p>
              ) : (
                <div className="judgment-history__list">
                  {history.map((item) => {
                    const savedData =
                      item.response?.data;

                    return (
                      <button
                        key={item.id}
                        type="button"
                        className="judgment-history__item card"
                        onClick={() =>
                          handleHistoryClick(item)
                        }
                      >
                        <span className="judgment-history__type">
                          Judgment
                        </span>

                        <span className="judgment-history__filename">
                          {item.filename ||
                            "Uploaded judgment"}
                        </span>

                        {savedData?.caseTitle && (
                          <span className="judgment-history__case">
                            {savedData.caseTitle}
                          </span>
                        )}

                        <span className="judgment-history__date">
                          {item.createdAt
                            ? new Date(
                              item.createdAt
                            ).toLocaleString()
                            : ""}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </section>
          )}

        {/* =====================================================
            PAGE HEADER
        ===================================================== */}

        <div className="simplifier-header animate-fade-in">
          <p className="eyebrow">
            Judgment Simplifier
          </p>

          <h1 className="heading-serif simplifier-header__title">
            Understand a judgment without
            reading every page.
          </h1>

          <p className="simplifier-header__subtitle">
            Upload a court judgment and get a
            structured explanation of the facts,
            arguments, decision and important
            legal principles.
          </p>
        </div>

        {/* =====================================================
            UPLOAD AREA
        ===================================================== */}

        {!result && (
          <div className="simplifier-upload-area card animate-fade-in">
            <FileUpload
              file={file}
              onFileChange={
                handleFileChange
              }
              onFileRemove={
                handleFileRemove
              }
            />

            {error && (
              <p
                className="error-text"
                role="alert"
                style={{
                  marginTop:
                    "var(--space-3)",
                }}
              >
                {error}
              </p>
            )}

            {file && !loading && (
              <div className="simplifier-upload-area__actions">
                <button
                  type="button"
                  className="btn-primary"
                  onClick={handleAnalyze}
                  disabled={loading}
                >
                  Analyze Judgment

                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <line
                      x1="5"
                      y1="12"
                      x2="19"
                      y2="12"
                    />

                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>

                <p className="simplifier-upload-area__note">
                  Uploaded files are
                  processed securely by the
                  local backend.
                </p>
              </div>
            )}
          </div>
        )}

        {/* =====================================================
            LOADING
        ===================================================== */}

        {loading && (
          <LoadingState
            messages={loadingMsg}
          />
        )}

        {/* =====================================================
            RESULTS
        ===================================================== */}

        {result && !loading && (
          <div className="simplifier-result animate-fade-in">

            {/* Toolbar */}

            <div className="simplifier-result__toolbar">
              <button
                type="button"
                className="btn-ghost"
                onClick={handleReset}
              >
                ← Analyze another judgment
              </button>
            </div>

            <div className="simplifier-result__layout">

              {/* LEFT: Judgment analysis */}

              <div className="judgment-analysis">

                {/* Case overview */}

                <div className="case-overview card">
                  <p className="case-overview__label eyebrow">
                    Case Overview
                  </p>

                  <h2 className="heading-serif case-overview__title">
                    {result.caseTitle}
                  </h2>

                  <div className="case-overview__meta">
                    <span className="case-meta-chip">
                      {result.court}
                    </span>

                    <span className="case-meta-chip">
                      {result.year}
                    </span>

                    <span className="case-meta-chip">
                      {result.caseType}
                    </span>
                  </div>
                </div>

                {/* Sections */}

                <div className="judgment-sections">
                  <JudgmentSection
                    title="Case in Brief"
                    content={result.brief}
                  />

                  <JudgmentSection
                    title="Facts"
                    content={result.facts}
                  />

                  <JudgmentSection
                    title="Arguments"
                    content={result.arguments}
                  />

                  <JudgmentSection
                    title="Issues Before the Court"
                    content={null}
                    items={
                      result.issues || []
                    }
                  />

                  <JudgmentSection
                    title="Decision"
                    content={result.decision}
                  />

                  <JudgmentSection
                    title="Key Legal Principles"
                    content={null}
                    items={
                      result.legalPrinciples ||
                      []
                    }
                  />
                </div>

                <Disclaimer compact />
              </div>

              {/* RIGHT: Important paragraphs */}

              <aside
                className="judgment-paragraphs"
                aria-label="Important paragraphs"
              >
                <h2 className="judgment-paragraphs__heading heading-serif">
                  Important Paragraphs
                </h2>

                <p className="judgment-paragraphs__sub">
                  Click "View in judgment"
                  to highlight a key
                  paragraph.
                </p>

                <div className="para-list">
                  {paragraphs.map(
                    (paragraph) => (
                      <ParagraphCard
                        key={
                          paragraph.id
                        }
                        para={
                          paragraph
                        }
                        onHighlight={
                          handleHighlight
                        }
                      />
                    )
                  )}
                </div>
              </aside>
            </div>
          </div>
        )}

        {/* =====================================================
            EMPTY STATE
        ===================================================== */}

        {!file &&
          !result &&
          !loading && (
            <p className="simplifier-empty">
              Select a court judgment PDF
              or text file to get started.
            </p>
          )}
      </div>
    </main>
  );
}


// ============================================================
// INDIVIDUAL JUDGMENT SECTION
// ============================================================

function JudgmentSection({
  title,
  content,
  items,
}) {
  const sectionId = `js-${title
    .replace(/\s/g, "-")
    .toLowerCase()}`;

  return (
    <section
      className="judgment-section"
      aria-labelledby={sectionId}
    >
      <h3
        id={sectionId}
        className="judgment-section__title"
      >
        {title}
      </h3>

      {content && (
        <p className="judgment-section__content">
          {content}
        </p>
      )}

      {items && items.length > 0 && (
        <ol className="judgment-section__list">
          {items.map((item, index) => (
            <li
              key={index}
              className="judgment-section__list-item"
            >
              {item}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}