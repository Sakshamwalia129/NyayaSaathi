import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  checkRights,
  getRightsHistory,
} from "../services/legalService";
import SourceCard from "../components/SourceCard";
import LoadingState from "../components/LoadingState";
import Disclaimer from "../components/Disclaimer";
import "./RightsChecker.css";

export default function RightsChecker() {
  const { user, loading: authLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
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
        const response = await getRightsHistory();

        if (isMounted) {
          setHistory(response?.data || []);
        }
      } catch (err) {
        console.error("Failed to load rights history:", err);
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
  // SUBMIT RIGHTS QUERY
  // ============================================================

  async function handleSubmit(e) {
    e.preventDefault();

    if (!user) {
      navigate("/login", { state: { from: location } });
      return;
    }

    if (!query.trim()) {
      setError("Please describe your situation first.");
      return;
    }

    if (query.trim().length < 5) {
      setError(
        "Please describe your situation in a little more detail (at least 5 characters)."
      );
      return;
    }

    setError("");
    setLoading(true);
    setResult(null);

    try {
      const response = await checkRights(query, "");

      setResult(response.data);

      // Refresh PostgreSQL history after successful query
      try {
        const historyResponse = await getRightsHistory();
        setHistory(historyResponse?.data || []);
      } catch (historyError) {
        console.error(
          "Failed to refresh rights history:",
          historyError
        );
      }
    } catch (err) {
      setError(
        err?.message ||
        "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  // ============================================================
  // RESET
  // ============================================================

  function handleReset() {
    setQuery("");
    setResult(null);
    setError("");
  }

  // ============================================================
  // OPEN SAVED HISTORY ITEM
  // ============================================================

  function handleHistoryClick(item) {
    setQuery(item.query || "");

    const savedResult = item.response?.data;

    if (savedResult) {
      setResult(savedResult);
      setError("");

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    }
  }

  return (
    <main className="checker-page">
      <div className="container">

        {/* Unauthenticated requirement prompt */}
        {!user && !authLoading && (
          <div
            className="card"
            style={{
              marginBottom: "2rem",
              padding: "1.5rem",
              borderLeft: "4px solid #c5a059",
            }}
          >
            <h3
              style={{
                fontFamily: "Playfair Display, serif",
                margin: "0 0 0.5rem 0",
                color: "#1b365d",
              }}
            >
              Sign In to Save Your Activity
            </h3>

            <p
              style={{
                color: "#6b7280",
                margin: "0 0 1rem 0",
                fontSize: "0.95rem",
              }}
            >
              Signing in lets you run personalized Rights Checks and
              save your activity history securely in your private
              account.
            </p>

            <Link
              to="/login"
              state={{ from: location }}
              className="btn-primary"
              style={{ display: "inline-block" }}
            >
              Sign In to NyayaSaathi
            </Link>
          </div>
        )}

        {/* =====================================================
            SAVED HISTORY
        ===================================================== */}

        {user && (historyLoading || history.length > 0) && (
          <section
            className="rights-history"
            aria-labelledby="rights-history-heading"
          >
            <div className="rights-history__header">
              <div>
                <p className="eyebrow">Saved Activity</p>

                <h2
                  id="rights-history-heading"
                  className="heading-serif rights-history__title"
                >
                  Previous Rights Checks
                </h2>
              </div>

              {!historyLoading && (
                <span className="rights-history__count">
                  {history.length} saved
                </span>
              )}
            </div>

            {historyLoading ? (
              <p className="rights-history__loading">
                Loading previous checks...
              </p>
            ) : (
              <div className="rights-history__list">
                {history.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className="rights-history__item card"
                    onClick={() => handleHistoryClick(item)}
                  >
                    <span className="rights-history__category">
                      {item.category || "General"}
                    </span>

                    <span className="rights-history__query">
                      {item.query}
                    </span>

                    <span className="rights-history__date">
                      {item.createdAt
                        ? new Date(item.createdAt).toLocaleString()
                        : ""}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </section>
        )}

        {/* =====================================================
            PAGE HEADER
        ===================================================== */}

        <div className="checker-header animate-fade-in">
          <p className="eyebrow">Rights Checker</p>

          <h1 className="heading-serif checker-header__title">
            Tell us what happened.
          </h1>

          <p className="checker-header__subtitle">
            Describe your situation in simple words.
            NyayaSaathi will help you understand the legal
            information that may be relevant.
          </p>
        </div>

        {/* =====================================================
            INPUT FORM
        ===================================================== */}

        <form
          className="checker-form card animate-fade-in"
          onSubmit={handleSubmit}
          noValidate
          aria-label="Rights checker form"
        >
          <label
            htmlFor="query-input"
            className="checker-form__label"
          >
            Describe your situation
          </label>

          <textarea
            id="query-input"
            className="checker-form__textarea"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);

              if (error) {
                setError("");
              }
            }}
            placeholder="Example: My landlord has not returned my security deposit even after I vacated the house..."
            rows={5}
            aria-describedby={error ? "query-error" : undefined}
          />

          {error && (
            <p
              id="query-error"
              className="error-text"
              role="alert"
            >
              {error}
            </p>
          )}

          {/* Actions */}

          <div className="checker-form__actions">
            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              aria-busy={loading}
            >
              {loading
                ? "Reviewing..."
                : "Check My Rights"}
            </button>

            {result && (
              <button
                type="button"
                className="btn-ghost checker-form__reset"
                onClick={handleReset}
              >
                Start over
              </button>
            )}
          </div>
        </form>

        {/* =====================================================
            LOADING
        ===================================================== */}

        {loading && (
          <LoadingState messages="Analyzing query & searching relevant legal provisions..." />
        )}

        {/* =====================================================
            RESULTS
        ===================================================== */}

        {result && !loading && (
          <div className="checker-result animate-fade-in">

            {/* Situation */}

            <section
              className="result-section"
              aria-labelledby="situation-heading"
            >
              <h2
                id="situation-heading"
                className="result-section__heading heading-serif"
              >
                Understanding Your Situation
              </h2>

              <div className="result-section__card card">
                <p className="result-situation-label">
                  {result.situation}
                </p>

                <p className="result-explanation">
                  {result.explanation}
                </p>
              </div>
            </section>

            {/* Legal provisions */}

            <section
              className="result-section"
              aria-labelledby="provisions-heading"
            >
              <h2
                id="provisions-heading"
                className="result-section__heading heading-serif"
              >
                Relevant Legal Provisions
              </h2>

              <p className="result-section__sub">
                These are the legal sources that are most
                relevant to your situation based on our
                analysis.
              </p>

              <div className="provisions-list">
                {(result.provisions || []).map(
                  (provision, index) => (
                    <SourceCard
                      key={provision.id}
                      provision={provision}
                      citationNumber={index + 1}
                    />
                  )
                )}
              </div>
            </section>

            {/* Existing Next Steps */}

            <section
              className="result-section"
              aria-labelledby="steps-heading"
            >
              <h2
                id="steps-heading"
                className="result-section__heading heading-serif"
              >
                Possible Next Steps
              </h2>

              <div className="result-section__card card">
                <ol className="next-steps-list">
                  {(result.nextSteps || []).map(
                    (step, index) => (
                      <li
                        key={index}
                        className="next-steps-list__item"
                      >
                        <span
                          className="next-steps-list__number"
                          aria-hidden="true"
                        >
                          {index + 1}
                        </span>

                        <span>{step}</span>
                      </li>
                    )
                  )}
                </ol>
              </div>
            </section>

            {/* =================================================
                LEGAL ACTION PLAN
            ================================================= */}

            {result.actionPlan && (
              <section
                className="result-section action-plan"
                aria-labelledby="action-plan-heading"
              >
                <h2
                  id="action-plan-heading"
                  className="result-section__heading heading-serif"
                >
                  ⚖️ Your Legal Action Plan
                </h2>

                <p className="result-section__sub">
                  A practical sequence of actions based on the
                  legal information available for your situation.
                </p>

                {/* Action steps */}

                {result.actionPlan.steps?.length > 0 && (
                  <div className="action-plan__steps">
                    {result.actionPlan.steps.map(
                      (step, index) => (
                        <div
                          key={`${step.step}-${index}`}
                          className="action-plan__step card"
                        >
                          <div
                            className="action-plan__step-number"
                            aria-hidden="true"
                          >
                            {step.step || index + 1}
                          </div>

                          <div className="action-plan__step-content">
                            <h3 className="action-plan__step-title">
                              {step.title}
                            </h3>

                            <p className="action-plan__step-description">
                              {step.description}
                            </p>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                )}

                {/* Documents */}

                {result.actionPlan.documents?.length > 0 && (
                  <div className="action-plan__detail-card card">
                    <h3 className="action-plan__detail-title">
                      📄 Documents to Keep Ready
                    </h3>

                    <ul className="action-plan__documents">
                      {result.actionPlan.documents.map(
                        (document, index) => (
                          <li key={index}>
                            {document}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}

                {/* Relevant Authority */}

                {result.actionPlan.authority && (
                  <div className="action-plan__detail-card card">
                    <h3 className="action-plan__detail-title">
                      🏛️ Relevant Authority
                    </h3>

                    <p className="action-plan__authority-name">
                      {result.actionPlan.authority.name}
                    </p>

                    {result.actionPlan.authority.whenToApproach && (
                      <p className="action-plan__authority-description">
                        <strong>When to approach: </strong>
                        {
                          result.actionPlan.authority
                            .whenToApproach
                        }
                      </p>
                    )}
                  </div>
                )}

                <div className="action-plan__notice">
                  <strong>Important:</strong>{" "}
                  This action plan is based on the legal sources
                  retrieved for your query and provides general
                  legal information, not professional legal advice.
                </div>
              </section>
            )}

            {/* Grounding */}

            <section
              className="result-section"
              aria-labelledby="grounding-heading"
            >
              <h2
                id="grounding-heading"
                className="result-section__heading heading-serif"
              >
                Why this answer?
              </h2>

              <div className="result-section__card card grounding-card">
                <span
                  className="grounding-card__dot"
                  aria-hidden="true"
                />

                <div>
                  <p className="grounding-card__note">
                    {result.groundingNote}
                  </p>

                  <p className="grounding-card__tag">
                    Based on legal sources retrieved for
                    your query.
                  </p>
                </div>
              </div>
            </section>

            <Disclaimer compact />
          </div>
        )}

        {/* =====================================================
            EMPTY STATE
        ===================================================== */}

        {!result && !loading && !error && (
          <div
            className="checker-empty"
            aria-hidden="true"
          >
            <p className="checker-empty__text">
              Enter your situation above and click{" "}
              <strong>Check My Rights</strong> to see
              relevant legal information.
            </p>
          </div>
        )}
      </div>
    </main>
  );
}