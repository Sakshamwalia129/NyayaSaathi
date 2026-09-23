// ============================================================
// authService.js
// Authentication service for NyayaSaathi frontend.
// Communicates with FastAPI backend /api/auth endpoints.
// ============================================================

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "nyayasaathi_auth_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function getErrorMessage(errorData, statusText) {
  if (!errorData) return statusText || "An unexpected authentication error occurred.";
  if (typeof errorData.detail === "string") return errorData.detail;
  if (Array.isArray(errorData.detail)) {
    return errorData.detail.map((d) => d.msg || d.message).join("; ");
  }
  if (errorData.error?.message) return errorData.error.message;
  if (errorData.message) return errorData.message;
  return statusText || "An unexpected authentication error occurred.";
}

/**
 * Register a new user account with email and password.
 */
export async function registerUser({ name, email, password }) {
  let response;
  try {
    response = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, email, password }),
    });
  } catch {
    throw new Error(`Cannot connect to NyayaSaathi backend server (${API_URL}).`);
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getErrorMessage(data, response.statusText));
  }

  if (data?.access_token) {
    setToken(data.access_token);
  }

  return data;
}

/**
 * Log in an existing user with email and password.
 */
export async function loginUser({ email, password }) {
  let response;
  try {
    response = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    throw new Error(`Cannot connect to NyayaSaathi backend server (${API_URL}).`);
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getErrorMessage(data, response.statusText));
  }

  if (data?.access_token) {
    setToken(data.access_token);
  }

  return data;
}

/**
 * Authenticate or register using a Google ID token credential.
 */
export async function googleAuth(credential) {
  let response;
  try {
    response = await fetch(`${API_URL}/api/auth/google`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ credential }),
    });
  } catch {
    throw new Error(`Cannot connect to NyayaSaathi backend server (${API_URL}).`);
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getErrorMessage(data, response.statusText));
  }

  if (data?.access_token) {
    setToken(data.access_token);
  }

  return data;
}

/**
 * Fetch the currently authenticated user session.
 */
export async function getCurrentUser(authToken) {
  const token = authToken || getToken();
  if (!token) return null;

  let response;
  try {
    response = await fetch(`${API_URL}/api/auth/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
      },
    });
  } catch {
    return null;
  }

  if (!response.ok) {
    removeToken();
    return null;
  }

  const data = await response.json().catch(() => null);
  return data?.user || null;
}
