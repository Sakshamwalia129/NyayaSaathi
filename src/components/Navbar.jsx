import {
  useState,
  useEffect,
} from "react";

import {
  Link,
  NavLink,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";

import "./Navbar.css";


function ScalesIcon() {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Decorative top */}
      <circle
        cx="32"
        cy="8"
        r="3"
        fill="currentColor"
      />

      {/* Central pillar */}
      <path
        d="M32 11V49"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />

      {/* Balance beam */}
      <path
        d="M13 19H51"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />

      {/* Small centre detail */}
      <path
        d="M27 16L32 11L37 16"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Left chains */}
      <path
        d="M19 20L11 35"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
      />

      <path
        d="M19 20L27 35"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
      />

      {/* Right chains */}
      <path
        d="M45 20L37 35"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
      />

      <path
        d="M45 20L53 35"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
      />

      {/* Left scale bowl */}
      <path
        d="M8 35H30C29 42 24.8 46 19 46C13.2 46 9 42 8 35Z"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />

      {/* Right scale bowl */}
      <path
        d="M34 35H56C55 42 50.8 46 45 46C39.2 46 35 42 34 35Z"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />

      {/* Pillar detail */}
      <path
        d="M28 49H36"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />

      {/* Base */}
      <path
        d="M24 54H40"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />

      <path
        d="M19 59H45"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}


export default function Navbar() {
  const [scrolled, setScrolled] =
    useState(false);

  const [menuOpen, setMenuOpen] =
    useState(false);

  // If Google/profile image URL exists but fails to load,
  // show the user's initial instead of a broken image.
  const [avatarError, setAvatarError] =
    useState(false);

  const { user, logout } = useAuth();

  const navigate = useNavigate();


  useEffect(() => {
    function onScroll() {
      setScrolled(
        window.scrollY > 40
      );
    }

    window.addEventListener(
      "scroll",
      onScroll,
      {
        passive: true,
      }
    );

    return () =>
      window.removeEventListener(
        "scroll",
        onScroll
      );
  }, []);


  // Reset avatar error whenever the logged-in user changes.
  useEffect(() => {
    setAvatarError(false);
  }, [user?.profile_picture_url]);


  function handleNavClick() {
    setMenuOpen(false);
  }


  function handleLogout() {
    logout();
    handleNavClick();
    navigate("/login");
  }


  function handleHowItWorks(e) {
    e.preventDefault();

    handleNavClick();

    const el =
      document.getElementById(
        "how-it-works"
      );

    if (el) {
      el.scrollIntoView({
        behavior: "smooth",
      });
    } else {
      navigate("/#how-it-works");
    }
  }


  function renderUserAvatar() {
    if (
      user?.profile_picture_url &&
      !avatarError
    ) {
      return (
        <img
          src={user.profile_picture_url}
          alt=""
          className="navbar__user-avatar"
          onError={() =>
            setAvatarError(true)
          }
        />
      );
    }

    return (
      <span className="navbar__user-initial">
        {user?.name
          ? user.name
            .charAt(0)
            .toUpperCase()
          : "U"}
      </span>
    );
  }


  return (
    <header
      className={
        `navbar${scrolled
          ? " navbar--scrolled"
          : ""
        }`
      }
      role="banner"
    >
      <div className="container navbar__inner">

        {/* Logo */}
        <Link
          to="/"
          className="navbar__logo"
          aria-label="NyayaSaathi Home"
        >
          <span
            className="navbar__logo-icon"
            aria-hidden="true"
          >
            <ScalesIcon />
          </span>

          <span className="navbar__logo-text">
            NyayaSaathi
          </span>
        </Link>


        {/* Desktop Navigation */}
        <nav
          className="navbar__nav"
          aria-label="Primary navigation"
        >
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              "navbar__link" +
              (
                isActive
                  ? " navbar__link--active"
                  : ""
              )
            }
            onClick={handleNavClick}
          >
            Home
          </NavLink>


          <NavLink
            to="/rights-checker"
            className={({ isActive }) =>
              "navbar__link" +
              (
                isActive
                  ? " navbar__link--active"
                  : ""
              )
            }
            onClick={handleNavClick}
          >
            Rights Checker
          </NavLink>


          <NavLink
            to="/judgment-simplifier"
            className={({ isActive }) =>
              "navbar__link" +
              (
                isActive
                  ? " navbar__link--active"
                  : ""
              )
            }
            onClick={handleNavClick}
          >
            Judgment Simplifier
          </NavLink>


          <NavLink
            to="/latest-judgments"
            className={({ isActive }) =>
              "navbar__link" +
              (
                isActive
                  ? " navbar__link--active"
                  : ""
              )
            }
            onClick={handleNavClick}
          >
            Latest Judgments
          </NavLink>


          <NavLink
            to="/#how-it-works"
            className="navbar__link"
            onClick={handleHowItWorks}
          >
            How It Works
          </NavLink>
        </nav>


        {/* Auth / CTA */}
        <div className="navbar__cta">
          {user ? (
            <div className="navbar__user-menu">

              <div className="navbar__user-badge">
                {renderUserAvatar()}

                <span className="navbar__user-name">
                  {user.name}
                </span>
              </div>


              <button
                type="button"
                onClick={handleLogout}
                className="navbar__logout-btn"
                title="Sign out of your account"
              >
                Logout
              </button>

            </div>
          ) : (
            <div className="navbar__auth-btns">

              <Link
                to="/login"
                className="navbar__login-link"
              >
                Sign In
              </Link>

              <Link
                to="/register"
                className="btn-primary navbar__cta-btn"
              >
                Register
              </Link>

            </div>
          )}
        </div>


        {/* Hamburger */}
        <button
          className="navbar__hamburger"
          onClick={() =>
            setMenuOpen(
              (value) => !value
            )
          }
          aria-expanded={menuOpen}
          aria-label="Toggle navigation menu"
        >
          <span
            className={
              `hamburger-line${menuOpen ? " open" : ""
              }`
            }
          />

          <span
            className={
              `hamburger-line${menuOpen ? " open" : ""
              }`
            }
          />

          <span
            className={
              `hamburger-line${menuOpen ? " open" : ""
              }`
            }
          />
        </button>

      </div>


      {/* Mobile Menu */}
      {menuOpen && (
        <div
          className="navbar__mobile-menu"
          role="navigation"
          aria-label="Mobile navigation"
        >

          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              "navbar__mobile-link" +
              (
                isActive
                  ? " navbar__mobile-link--active"
                  : ""
              )
            }
            onClick={handleNavClick}
          >
            Home
          </NavLink>


          <NavLink
            to="/rights-checker"
            className={({ isActive }) =>
              "navbar__mobile-link" +
              (
                isActive
                  ? " navbar__mobile-link--active"
                  : ""
              )
            }
            onClick={handleNavClick}
          >
            Rights Checker
          </NavLink>


          <NavLink
            to="/judgment-simplifier"
            className={({ isActive }) =>
              "navbar__mobile-link" +
              (
                isActive
                  ? " navbar__mobile-link--active"
                  : ""
              )
            }
            onClick={handleNavClick}
          >
            Judgment Simplifier
          </NavLink>


          <NavLink
            to="/latest-judgments"
            className={({ isActive }) =>
              "navbar__mobile-link" +
              (
                isActive
                  ? " navbar__mobile-link--active"
                  : ""
              )
            }
            onClick={handleNavClick}
          >
            Latest Judgments
          </NavLink>


          {user ? (
            <div className="navbar__mobile-user">

              <div className="navbar__user-badge">
                {renderUserAvatar()}

                <span className="navbar__user-name">
                  {user.name}
                </span>
              </div>


              <button
                type="button"
                onClick={handleLogout}
                className="btn-primary navbar__mobile-cta navbar__mobile-logout"
              >
                Logout
              </button>

            </div>
          ) : (
            <div className="navbar__mobile-auth">

              <Link
                to="/login"
                className="navbar__mobile-link"
                onClick={handleNavClick}
              >
                Sign In
              </Link>


              <Link
                to="/register"
                className="btn-primary navbar__mobile-cta"
                onClick={handleNavClick}
              >
                Register
              </Link>

            </div>
          )}

        </div>
      )}

    </header>
  );
}