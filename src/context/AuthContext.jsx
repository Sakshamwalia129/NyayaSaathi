import { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  getToken,
  removeToken,
  registerUser,
  loginUser,
  googleAuth,
  getCurrentUser,
} from "../services/authService";


const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setTokenState] = useState(() => getToken());
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Restore authenticated session on mount
  useEffect(() => {
    let isMounted = true;
    async function restoreSession() {
      const existingToken = getToken();
      if (existingToken) {
        try {
          const userData = await getCurrentUser(existingToken);
          if (isMounted) {
            if (userData) {
              setUser(userData);
              setTokenState(existingToken);
            } else {
              removeToken();
              setTokenState(null);
              setUser(null);
            }
          }
        } catch {
          if (isMounted) {
            removeToken();
            setTokenState(null);
            setUser(null);
          }
        }
      }
      if (isMounted) {
        setLoading(false);
      }
    }

    restoreSession();
    return () => {
      isMounted = false;
    };
  }, []);

  const register = useCallback(async (data) => {
    setAuthError(null);
    try {
      const response = await registerUser(data);
      if (response?.user && response?.access_token) {
        setUser(response.user);
        setTokenState(response.access_token);
        return response.user;
      }
      throw new Error("Registration response missing token or user details.");
    } catch (err) {
      setAuthError(err.message);
      throw err;
    }
  }, []);

  const login = useCallback(async (data) => {
    setAuthError(null);
    try {
      const response = await loginUser(data);
      if (response?.user && response?.access_token) {
        setUser(response.user);
        setTokenState(response.access_token);
        return response.user;
      }
      throw new Error("Login response missing token or user details.");
    } catch (err) {
      setAuthError(err.message);
      throw err;
    }
  }, []);

  const googleLogin = useCallback(async (credential) => {
    setAuthError(null);
    try {
      const response = await googleAuth(credential);
      if (response?.user && response?.access_token) {
        setUser(response.user);
        setTokenState(response.access_token);
        return response.user;
      }
      throw new Error("Google login response missing token or user details.");
    } catch (err) {
      setAuthError(err.message);
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    removeToken();
    setTokenState(null);
    setUser(null);
    setAuthError(null);
  }, []);

  const value = {
    user,
    token,
    loading,
    authError,
    register,
    login,
    googleLogin,
    logout,
    clearError: () => setAuthError(null),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
