import Disclaimer from "../components/Disclaimer";
import "./DisclaimerPage.css";

export default function DisclaimerPage() {
  return (
    <main className="disclaimer-page">
      <div className="container">
        <div className="disclaimer-header animate-fade-in">
          <p className="eyebrow">Legal Disclaimer</p>
          <h1 className="heading-serif disclaimer-header__title">
            Terms of Use & Legal Information Notice
          </h1>
          <p className="disclaimer-header__subtitle">
            NyayaSaathi is an educational legal information technology platform designed to improve legal awareness in India.
          </p>
        </div>

        <div className="disclaimer-content card animate-fade-in">
          <Disclaimer />

          <section className="disclaimer-section">
            <h2 className="heading-serif disclaimer-section__title">1. Educational & Informational Purpose Only</h2>
            <p>
              All content, summaries, legal provisions, and judgment analysis provided on NyayaSaathi are generated for general educational and informational purposes only. Nothing on this website constitutes legal advice, legal opinion, or formal legal representation.
            </p>
          </section>

          <section className="disclaimer-section">
            <h2 className="heading-serif disclaimer-section__title">2. No Advocate-Client Relationship</h2>
            <p>
              Using NyayaSaathi, sending queries through the Rights Checker, or uploading court documents to the Judgment Simplifier does not create an advocate-client relationship between you and NyayaSaathi, its developers, or any associated persons.
            </p>
          </section>

          <section className="disclaimer-section">
            <h2 className="heading-serif disclaimer-section__title">3. Consultation with Legal Professionals</h2>
            <p>
              Legal matters depend heavily on specific facts, jurisdiction, local court procedures, and applicable laws which may be amended or re-interpreted over time. You should always consult a qualified practising advocate before taking or refraining from any legal action based on information obtained from this platform.
            </p>
          </section>

          <section className="disclaimer-section">
            <h2 className="heading-serif disclaimer-section__title">4. Document & Source Verification</h2>
            <p>
              While NyayaSaathi links explanations directly to cited legal acts, sections, and judgment paragraphs, automated summaries may contain omissions or simplifications. Users are advised to review official gazettes, court orders, or primary legal statutes for definitive legal proceedings.
            </p>
          </section>

          <section className="disclaimer-section">
            <h2 className="heading-serif disclaimer-section__title">5. Emergency Legal Matters</h2>
            <p>
              If you are facing an urgent legal emergency, immediate threat to personal safety, arrest, or strict statutory limitation deadlines, do not rely on online automated tools. Contact local emergency authorities, legal aid services, or approach the nearest court immediately.
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
