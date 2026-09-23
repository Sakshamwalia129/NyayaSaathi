import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import {
    analyzeLatestJudgment,
    getLatestJudgments,
} from "../services/legalService";

import "./LatestJudgments.css";


function formatDate(value, includeTime = false) {
    if (!value) return "Not available";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Not available";
    }

    return new Intl.DateTimeFormat("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        ...(includeTime
            ? {
                hour: "2-digit",
                minute: "2-digit",
            }
            : {}),
    }).format(date);
}


const FILTERS = [
    { value: "all", label: "All" },
    { value: "today", label: "Today" },
    { value: "7d", label: "7 Days" },
    { value: "30d", label: "30 Days" },
    { value: "6m", label: "6 Months" },
    { value: "custom", label: "Custom" },
];


export default function LatestJudgments() {
    const [judgments, setJudgments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [analyzingId, setAnalyzingId] = useState(null);

    const [period, setPeriod] = useState("all");
    const [fromDate, setFromDate] = useState("");
    const [toDate, setToDate] = useState("");

    const { user } = useAuth();
    const navigate = useNavigate();


    useEffect(() => {
        let active = true;

        async function loadJudgments() {
            if (
                period === "custom" &&
                (!fromDate || !toDate)
            ) {
                if (active) {
                    setJudgments([]);
                    setLoading(false);
                    setError("");
                }

                return;
            }

            try {
                setLoading(true);
                setError("");

                const result = await getLatestJudgments(
                    100,
                    period,
                    fromDate || null,
                    toDate || null
                );

                if (active) {
                    setJudgments(result?.data || []);
                }
            } catch (err) {
                if (active) {
                    setError(
                        err.message ||
                        "Unable to load latest judgments."
                    );
                }
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        }

        loadJudgments();

        return () => {
            active = false;
        };
    }, [period, fromDate, toDate]);


    function handleFilterChange(selectedPeriod) {
        setPeriod(selectedPeriod);
        setError("");

        if (selectedPeriod !== "custom") {
            setFromDate("");
            setToDate("");
        }
    }


    async function handleAnalyze(judgment) {
        if (!user) {
            navigate("/login", {
                state: {
                    from: "/latest-judgments",
                },
            });

            return;
        }

        try {
            setAnalyzingId(judgment.id);
            setError("");

            await analyzeLatestJudgment(
                judgment.id
            );

            /*
             * The analysis is automatically stored by the backend
             * in the current user's Judgment History.
             *
             * Navigate to the existing Judgment Simplifier page,
             * where that history can be viewed.
             */
            navigate("/judgment-simplifier");

        } catch (err) {
            setError(
                err.message ||
                "Unable to analyze this judgment."
            );
        } finally {
            setAnalyzingId(null);
        }
    }


    return (
        <main className="latest-judgments">

            <section className="latest-judgments__hero">
                <div className="container">

                    <div className="latest-judgments__hero-layout">

                        <div className="latest-judgments__hero-content">

                            <span className="latest-judgments__eyebrow">
                                Supreme Court of India
                            </span>

                            <h1>
                                Latest Supreme Court Judgments
                            </h1>

                            <p>
                                Explore recently uploaded Supreme Court
                                judgments with official case information and
                                AI-generated plain-language summaries.
                            </p>

                            <div className="latest-judgments__notice">
                                <span
                                    className="latest-judgments__notice-icon"
                                    aria-hidden="true"
                                >
                                    ⚖
                                </span>

                                <span>
                                    Official case information and judgment links
                                    are sourced from the Supreme Court of India.
                                    AI summaries are generated by NyayaSaathi and
                                    are not official court summaries.
                                </span>
                            </div>

                        </div>


                        <div className="latest-judgments__hero-visual">

                            <div className="latest-judgments__image-frame">
                                <img
                                    src="/assets/supreme-court.png"
                                    alt="Supreme Court of India"
                                    className="latest-judgments__hero-image"
                                />

                                <div className="latest-judgments__image-overlay" />

                                <div className="latest-judgments__image-label">
                                    <span
                                        className="latest-judgments__image-label-icon"
                                        aria-hidden="true"
                                    >
                                        ⚖
                                    </span>

                                    <div>
                                        <strong>
                                            Supreme Court of India
                                        </strong>

                                        <span>
                                            New Delhi
                                        </span>
                                    </div>
                                </div>
                            </div>

                        </div>

                    </div>

                </div>
            </section>


            <section className="latest-judgments__content">
                <div className="container">

                    <div className="latest-judgments__heading-row">
                        <div>
                            <h2>Recently Uploaded</h2>

                            <p>
                                Latest judgments currently available in
                                NyayaSaathi.
                            </p>
                        </div>

                        {!loading && !error && (
                            <span className="latest-judgments__count">
                                {judgments.length}{" "}
                                {judgments.length === 1
                                    ? "judgment"
                                    : "judgments"}
                            </span>
                        )}
                    </div>


                    {/* DATE FILTERS */}
                    <div className="latest-judgments__filters">

                        <div className="latest-judgments__filter-buttons">
                            {FILTERS.map((filter) => (
                                <button
                                    key={filter.value}
                                    type="button"
                                    className={
                                        period === filter.value
                                            ? "latest-judgments__filter-btn latest-judgments__filter-btn--active"
                                            : "latest-judgments__filter-btn"
                                    }
                                    onClick={() =>
                                        handleFilterChange(filter.value)
                                    }
                                >
                                    {filter.label}
                                </button>
                            ))}
                        </div>


                        {period === "custom" && (
                            <div className="latest-judgments__custom-filter">

                                <div className="latest-judgments__date-field">
                                    <label htmlFor="latest-from-date">
                                        From
                                    </label>

                                    <input
                                        id="latest-from-date"
                                        type="date"
                                        value={fromDate}
                                        max={toDate || undefined}
                                        onChange={(event) =>
                                            setFromDate(event.target.value)
                                        }
                                    />
                                </div>


                                <span
                                    className="latest-judgments__date-separator"
                                    aria-hidden="true"
                                >
                                    →
                                </span>


                                <div className="latest-judgments__date-field">
                                    <label htmlFor="latest-to-date">
                                        To
                                    </label>

                                    <input
                                        id="latest-to-date"
                                        type="date"
                                        value={toDate}
                                        min={fromDate || undefined}
                                        onChange={(event) =>
                                            setToDate(event.target.value)
                                        }
                                    />
                                </div>

                            </div>
                        )}

                    </div>


                    {period === "custom" &&
                        (!fromDate || !toDate) && (
                            <div className="latest-judgments__custom-hint">
                                Select both From and To dates to view
                                judgments from a custom period.
                            </div>
                        )}


                    {loading && (
                        <div className="latest-judgments__state">
                            <div className="latest-judgments__spinner" />

                            <h3>Loading latest judgments</h3>

                            <p>
                                Fetching Supreme Court judgment information...
                            </p>
                        </div>
                    )}


                    {!loading && error && (
                        <div
                            className="latest-judgments__error"
                            role="alert"
                        >
                            <strong>
                                Unable to load judgments
                            </strong>

                            <p>{error}</p>
                        </div>
                    )}


                    {!loading &&
                        !error &&
                        judgments.length === 0 &&
                        !(
                            period === "custom" &&
                            (!fromDate || !toDate)
                        ) && (
                            <div className="latest-judgments__state">
                                <div className="latest-judgments__empty-icon">
                                    ⚖
                                </div>

                                <h3>
                                    No judgments found
                                </h3>

                                <p>
                                    No processed Supreme Court judgments
                                    were found for the selected period.
                                </p>
                            </div>
                        )}


                    {!loading &&
                        !error &&
                        judgments.length > 0 && (
                            <div className="latest-judgments__grid">

                                {judgments.map((judgment) => {
                                    const official =
                                        judgment.official || {};

                                    const ai =
                                        judgment.ai || {};

                                    const analyzing =
                                        analyzingId === judgment.id;

                                    return (
                                        <article
                                            key={judgment.id}
                                            className="judgment-card"
                                        >
                                            <div className="judgment-card__top">

                                                <div className="judgment-card__court">
                                                    <span aria-hidden="true">
                                                        ⚖
                                                    </span>

                                                    Supreme Court of India
                                                </div>

                                                <span className="judgment-card__status">
                                                    Judgment
                                                </span>

                                            </div>


                                            <h3 className="judgment-card__title">
                                                {official.caseTitle ||
                                                    "Supreme Court Judgment"}
                                            </h3>


                                            <div className="judgment-card__metadata">

                                                <div className="judgment-card__metadata-item">
                                                    <span>Case Number</span>

                                                    <strong>
                                                        {official.caseNumber ||
                                                            "Not available"}
                                                    </strong>
                                                </div>


                                                <div className="judgment-card__metadata-item">
                                                    <span>Diary Number</span>

                                                    <strong>
                                                        {official.diaryNumber ||
                                                            "Not available"}
                                                    </strong>
                                                </div>


                                                <div className="judgment-card__metadata-item">
                                                    <span>Judgment Date</span>

                                                    <strong>
                                                        {formatDate(
                                                            official.judgmentDate
                                                        )}
                                                    </strong>
                                                </div>


                                                <div className="judgment-card__metadata-item">
                                                    <span>Uploaded</span>

                                                    <strong>
                                                        {formatDate(
                                                            official.uploadedAt,
                                                            true
                                                        )}
                                                    </strong>
                                                </div>

                                            </div>


                                            <div className="judgment-card__ai">

                                                <div className="judgment-card__ai-header">
                                                    <span className="judgment-card__ai-badge">
                                                        AI-generated summary
                                                    </span>
                                                </div>


                                                {ai.headline && (
                                                    <h4>
                                                        {ai.headline}
                                                    </h4>
                                                )}


                                                <p>
                                                    {ai.summary ||
                                                        "AI summary is not available for this judgment yet."}
                                                </p>


                                                <div className="judgment-card__ai-warning">
                                                    This summary is generated for
                                                    informational purposes. Refer to the
                                                    official judgment for authoritative
                                                    text.
                                                </div>

                                            </div>


                                            <div className="judgment-card__actions">

                                                {official.pdfUrl && (
                                                    <a
                                                        href={official.pdfUrl}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="judgment-card__official-btn"
                                                    >
                                                        View Official Judgment
                                                        <span aria-hidden="true">
                                                            ↗
                                                        </span>
                                                    </a>
                                                )}


                                                <button
                                                    type="button"
                                                    className="judgment-card__analyze-btn"
                                                    onClick={() =>
                                                        handleAnalyze(judgment)
                                                    }
                                                    disabled={analyzing}
                                                >
                                                    {analyzing
                                                        ? "Analyzing..."
                                                        : user
                                                            ? "Analyze Judgment"
                                                            : "Sign in to Analyze"}
                                                </button>

                                            </div>


                                            <div className="judgment-card__source">
                                                Source: Supreme Court of India
                                            </div>

                                        </article>
                                    );
                                })}

                            </div>
                        )}

                </div>
            </section>

        </main>
    );
}