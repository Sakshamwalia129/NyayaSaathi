import { useEffect, useRef, useState } from "react";

/**
 * GoogleSignInButton Component
 * Integrates Google Identity Services (GIS) for real Google Sign-In authentication.
 *
 * @param {object} props
 * @param {function} props.onSuccess - Callback receives Google ID credential token string
 * @param {function} props.onError - Callback receives error message string
 * @param {boolean} props.disabled - Optional disabled state
 */
export default function GoogleSignInButton({ onSuccess, onError, disabled = false }) {
  const buttonRef = useRef(null);
  const [scriptLoaded, setScriptLoaded] = useState(() => Boolean(window.google?.accounts?.id));
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

  useEffect(() => {
    if (!clientId || window.google?.accounts?.id) return;


    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => setScriptLoaded(true);
    script.onerror = () => {
      if (onError) onError("Failed to load Google Identity Services SDK.");
    };
    document.head.appendChild(script);
  }, [clientId, onError]);

  useEffect(() => {
    if (!scriptLoaded || !clientId || !buttonRef.current || !window.google?.accounts?.id) {
      return;
    }

    try {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
          if (response?.credential) {
            onSuccess(response.credential);
          } else if (onError) {
            onError("Google authentication failed. No credential received.");
          }
        },
      });

      // Clear any previous button iframe/nodes
      buttonRef.current.innerHTML = "";

      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: "outline",
        size: "large",
        width: "100%",
        text: "continue_with",
        shape: "rectangular",
        logo_alignment: "left",
      });
    } catch (err) {
      if (onError) onError(`Google Sign-In initialization error: ${err.message}`);
    }
  }, [scriptLoaded, clientId, onSuccess, onError]);

  function handleFallbackClick() {
    if (!clientId) {
      const msg =
        "Google Sign-In requires configuring VITE_GOOGLE_CLIENT_ID in your environment (.env) file.";
      if (onError) onError(msg);
      else alert(msg);
    }
  }

  // If Client ID is not set or script is still loading, show styled fallback button
  if (!clientId) {
    return (
      <button
        type="button"
        className="btn-google-fallback"
        onClick={handleFallbackClick}
        disabled={disabled}
      >
        <svg className="google-icon" viewBox="0 0 24 24" width="18" height="18">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
          />
        </svg>
        <span>Continue with Google</span>
      </button>
    );
  }

  return <div ref={buttonRef} className="google-signin-wrapper" />;
}
