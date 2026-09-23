import { Link } from "react-router-dom";
import "./Footer.css";

export default function Footer() {
  return (
    <footer className="footer" role="contentinfo">
      <div className="container">
        <div className="footer__top">
          {/* Brand */}
          <div className="footer__brand">
            <span className="footer__logo">NyayaSaathi</span>
            <p className="footer__tagline">
              Understand Your Rights. Understand the Law.
            </p>
            <p className="footer__project-note">
              Built as an educational legal technology project.
            </p>
          </div>

          {/* Links */}
          <nav aria-label="Footer navigation" className="footer__links">
            <h3 className="footer__links-heading">Navigation</h3>
            <ul>
              <li>
                <Link to="/">Home</Link>
              </li>
              <li>
                <Link to="/rights-checker">Rights Checker</Link>
              </li>
              <li>
                <Link to="/judgment-simplifier">Judgment Simplifier</Link>
              </li>
              <li>
                <a
                  href="#how-it-works"
                  onClick={(e) => {
                    e.preventDefault();
                    document
                      .getElementById("how-it-works")
                      ?.scrollIntoView({ behavior: "smooth" });
                  }}
                >
                  How It Works
                </a>
              </li>
              <li>
                <Link to="/disclaimer">Disclaimer</Link>
              </li>
            </ul>
          </nav>

          {/* Disclaimer note */}
          <div className="footer__disclaimer-note">
            <h3 className="footer__links-heading">Disclaimer</h3>
            <p>
              NyayaSaathi provides general legal information only. It is not a
              substitute for advice from a qualified legal professional.
            </p>
          </div>
        </div>

        <div className="footer__bottom">
          <p>
            © {new Date().getFullYear()} NyayaSaathi. Educational project only.
          </p>
          <p>
            Simple legal information, grounded in authentic sources.
          </p>
        </div>
      </div>
    </footer>
  );
}
