import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";

import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import ProtectedRoute from "./components/ProtectedRoute";

import Home from "./pages/Home";
import RightsChecker from "./pages/RightsChecker";
import JudgmentSimplifier from "./pages/JudgmentSimplifier";
import LatestJudgments from "./pages/LatestJudgments";
import DisclaimerPage from "./pages/DisclaimerPage";
import Login from "./pages/Login";
import Register from "./pages/Register";


export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>

          {/* ── Public routes ── */}

          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/*
           * ── Protected application routes ──
           *
           * The wildcard "/*" catches every URL that isn't /login or /register.
           * ProtectedRoute:
           *   - waits for AuthContext to finish loading (prevents flash)
           *   - if authenticated → renders children (Navbar + page)
           *   - if unauthenticated → <Navigate to="/login" state={{ from: location }} />
           *
           * Inner <Routes> use relative paths (no leading "/") because they
           * are resolved relative to the matched "/*" prefix in React Router v7.
           */}

          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <div className="app-wrapper">

                  <Navbar />

                  <Routes>
                    <Route index element={<Home />} />
                    <Route path="rights-checker" element={<RightsChecker />} />
                    <Route path="judgment-simplifier" element={<JudgmentSimplifier />} />
                    <Route path="latest-judgments" element={<LatestJudgments />} />
                    <Route path="disclaimer" element={<DisclaimerPage />} />

                    {/* Fallback — unknown protected URLs */}
                    <Route
                      path="*"
                      element={
                        <div
                          style={{
                            textAlign: "center",
                            padding: "5rem 2rem",
                            minHeight: "60vh",
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "1rem",
                          }}
                        >
                          <h1
                            style={{
                              fontFamily: "Playfair Display, serif",
                              fontSize: "2rem",
                              color: "#2c2c2c",
                            }}
                          >
                            Page not found
                          </h1>

                          <p style={{ color: "#6b6b6b" }}>
                            The page you are looking for does not exist.
                          </p>

                          <a
                            href="/"
                            className="btn-primary"
                            style={{ marginTop: "1rem" }}
                          >
                            Return to Home
                          </a>
                        </div>
                      }
                    />
                  </Routes>

                  <Footer />

                </div>
              </ProtectedRoute>
            }
          />

        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}