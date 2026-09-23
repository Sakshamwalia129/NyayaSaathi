/**
 * ProtectedRoute.jsx
 *
 * Route-level authentication guard.
 * - While AuthContext is still restoring a session, renders nothing (no flash).
 * - If the user is authenticated, renders the requested page normally.
 * - If the user is not authenticated, immediately redirects to /login and
 *   preserves the originally requested location so Login can return there.
 */
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Wait until AuthContext finishes restoring the session.
  // Render nothing — avoids a brief flash of protected content.
  if (loading) {
    return null;
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        state={{ from: location }}
        replace
      />
    );
  }

  return children;
}
