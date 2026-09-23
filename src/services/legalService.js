import { getToken } from "./authService";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Helper to extract a clean error message from API responses
function getErrorMessage(errorData, statusText) {
  if (!errorData) return statusText || "Unable to process your request.";
  if (typeof errorData.detail === "string") return errorData.detail;

  if (Array.isArray(errorData.detail)) {
    return errorData.detail
      .map((d) => d.msg || d.message)
      .join("; ");
  }

  if (errorData.error?.message) return errorData.error.message;
  if (errorData.message) return errorData.message;

  return statusText || "Unable to process your request.";
}

function getAuthHeaders(extraHeaders = {}) {
  const token = getToken();
  const headers = { ...extraHeaders };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
}

async function parseResponse(response) {
  const result = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      getErrorMessage(result, response.statusText)
    );
  }

  return result;
}

/**
 * Submit user query and optional category to Rights Checker endpoint.
 */
export async function checkRights(query, category) {
  let response;

  try {
    response = await fetch(`${API_URL}/api/rights-check`, {
      method: "POST",
      headers: getAuthHeaders({
        "Content-Type": "application/json",
      }),
      body: JSON.stringify({
        query,
        category: category || null,
      }),
    });
  } catch {
    throw new Error(
      `Cannot connect to the NyayaSaathi backend server (${API_URL}). Please ensure the backend is running.`
    );
  }

  const result = await parseResponse(response);

  if (result?.success === false) {
    throw new Error(
      result.error?.message ||
      "Unable to process your legal query."
    );
  }

  return result;
}

/**
 * Upload court judgment file to Judgment Simplifier.
 */
export async function simplifyJudgment(file) {
  const formData = new FormData();
  formData.append("file", file);

  let response;

  try {
    response = await fetch(
      `${API_URL}/api/simplify-judgment`,
      {
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
      }
    );
  } catch {
    throw new Error(
      `Cannot connect to the NyayaSaathi backend server (${API_URL}). Please ensure the backend is running.`
    );
  }

  const result = await parseResponse(response);

  if (result?.success === false) {
    throw new Error(
      result.error?.message ||
      "Unable to simplify this judgment."
    );
  }

  return result;
}

/**
 * Fetch saved Rights Checker history.
 */
export async function getRightsHistory() {
  let response;

  try {
    response = await fetch(
      `${API_URL}/api/rights-history`,
      {
        headers: getAuthHeaders({
          Accept: "application/json",
        }),
      }
    );
  } catch {
    throw new Error(
      `Cannot connect to the NyayaSaathi backend server (${API_URL}). Please ensure the backend is running.`
    );
  }

  const result = await parseResponse(response);

  if (result?.success === false) {
    throw new Error(
      result.error?.message ||
      "Unable to load Rights Checker history."
    );
  }

  return result;
}

/**
 * Fetch saved Judgment Simplifier history.
 */
export async function getJudgmentHistory() {
  let response;

  try {
    response = await fetch(
      `${API_URL}/api/judgment-history`,
      {
        headers: getAuthHeaders({
          Accept: "application/json",
        }),
      }
    );
  } catch {
    throw new Error(
      `Cannot connect to the NyayaSaathi backend server (${API_URL}). Please ensure the backend is running.`
    );
  }

  const result = await parseResponse(response);

  if (result?.success === false) {
    throw new Error(
      result.error?.message ||
      "Unable to load Judgment Simplifier history."
    );
  }

  return result;
}


// ============================================================
// LATEST SUPREME COURT JUDGMENTS
// ============================================================

/**
 * Fetch processed Supreme Court judgments.
 *
 * Supported filters:
 * - all
 * - today
 * - 7d
 * - 30d
 * - 6m
 * - custom
 *
 * For custom filtering:
 * fromDate and toDate must use YYYY-MM-DD format.
 */
export async function getLatestJudgments(
  limit = 20,
  period = "all",
  fromDate = null,
  toDate = null
) {
  const params = new URLSearchParams();

  params.set("limit", String(limit));
  params.set("period", period);

  if (period === "custom") {
    if (fromDate) {
      params.set("from_date", fromDate);
    }

    if (toDate) {
      params.set("to_date", toDate);
    }
  }

  let response;

  try {
    response = await fetch(
      `${API_URL}/api/latest-judgments?${params.toString()}`,
      {
        headers: {
          Accept: "application/json",
        },
      }
    );
  } catch {
    throw new Error(
      `Cannot connect to the NyayaSaathi backend server (${API_URL}). Please ensure the backend is running.`
    );
  }

  const result = await parseResponse(response);

  if (result?.success === false) {
    throw new Error(
      result.error?.message ||
      "Unable to load latest Supreme Court judgments."
    );
  }

  return result;
}

/**
 * Fetch one Supreme Court judgment.
 */
export async function getLatestJudgment(judgmentId) {
  let response;

  try {
    response = await fetch(
      `${API_URL}/api/latest-judgments/${judgmentId}`,
      {
        headers: {
          Accept: "application/json",
        },
      }
    );
  } catch {
    throw new Error(
      `Cannot connect to the NyayaSaathi backend server (${API_URL}). Please ensure the backend is running.`
    );
  }

  return parseResponse(response);
}

/**
 * Analyze a Supreme Court judgment using the existing
 * Judgment Simplifier pipeline.
 *
 * Authentication required.
 */
export async function analyzeLatestJudgment(judgmentId) {
  let response;

  try {
    response = await fetch(
      `${API_URL}/api/latest-judgments/${judgmentId}/analyze`,
      {
        method: "POST",
        headers: getAuthHeaders({
          Accept: "application/json",
        }),
      }
    );
  } catch {
    throw new Error(
      `Cannot connect to the NyayaSaathi backend server (${API_URL}). Please ensure the backend is running.`
    );
  }

  const result = await parseResponse(response);

  if (result?.success === false) {
    throw new Error(
      result.error?.message ||
      "Unable to analyze this judgment."
    );
  }

  return result;
}