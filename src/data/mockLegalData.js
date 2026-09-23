// ============================================================
// mockLegalData.js
// Demo data for NyayaSaathi frontend.
// Replace with real API responses when backend is ready.
// ============================================================

// --- Example queries shown when user clicks "Use an example" ---
export const EXAMPLE_QUERIES = [
  {
    category: "Rental / Property",
    text: "My landlord has not returned my security deposit even after I vacated the house two months ago. He is not responding to my calls or messages.",
  },
  {
    category: "Workplace",
    text: "My employer terminated me without giving any notice or reason. I had worked there for three years and I did not receive any severance pay.",
  },
  {
    category: "Consumer",
    text: "I bought a refrigerator six months ago. It stopped working and the company is refusing to repair or replace it despite being under warranty.",
  },
];

// --- Mock responses for each scenario ---
// The key is a simplified identifier matched in legalService.js
export const MOCK_RESPONSES = {
  deposit: {
    situation: "Security Deposit Not Returned",
    explanation:
      "When a tenant vacates a rented property, the landlord is generally obligated to return the security deposit within a reasonable time after the tenancy ends. Withholding the deposit without a valid and documented reason—such as unpaid rent or actual damage beyond normal wear and tear—may be considered unlawful. You have the right to seek recovery through appropriate legal channels.",
    provisions: [
      {
        id: "p1",
        source: "Transfer of Property Act, 1882",
        section: "Section 108",
        summary:
          "Defines the duties and liabilities of landlord and tenant. A landlord must allow the tenant to peacefully enjoy the property and is responsible for returning the deposit at the end of the tenancy after deducting any lawful charges.",
        originalText:
          "[SAMPLE TEXT] Section 108 of the Transfer of Property Act, 1882 outlines the rights and liabilities of both lessor and lessee. It specifies that the lessor shall disclose any material defect in the property and that the lessee is entitled to a peaceful possession of the property for the duration of the lease. The section also implies an obligation to restore the property and settle deposits upon termination of the lease.",
        whyUsed:
          "This provision governs the landlord–tenant relationship and is the primary legal basis for claiming return of a security deposit.",
      },
      {
        id: "p2",
        source: "Consumer Protection Act, 2019",
        section: "Section 2(7) – Definition of Consumer",
        summary:
          "If the tenancy involves a service agreement, the tenant may also qualify as a consumer and pursue a complaint before the District Consumer Disputes Redressal Commission for deficiency in service.",
        originalText:
          "[SAMPLE TEXT] Under the Consumer Protection Act, 2019, a 'consumer' means any person who buys goods or avails services for consideration. Courts have in certain cases recognised rental housing as a 'service', thereby allowing tenants to file consumer complaints against landlords for deficiency in service, including wrongful withholding of security deposits.",
        whyUsed:
          "Depending on the nature of the rental agreement, the Consumer Forum may offer a faster and simpler forum for redressal.",
      },
    ],
    nextSteps: [
      "Document all communication with your landlord—keep messages, emails, and records of calls.",
      "Send a formal written notice (by post or email) requesting the return of your deposit within a specified time.",
      "Check your rental agreement for any clause specifying the timeline and conditions for deposit return.",
      "If the landlord does not respond, consider approaching the Rent Controller or appropriate civil court in your area.",
      "You may also file a complaint with the District Consumer Disputes Redressal Commission if the rental involved a service agreement.",
    ],
    groundingNote:
      "This response is based on general legal provisions under the Transfer of Property Act, 1882 and the Consumer Protection Act, 2019. Specific state laws and the terms of your rental agreement may also apply.",
  },

  termination: {
    situation: "Employer Termination Without Notice",
    explanation:
      "An employer generally cannot terminate a permanent employee without providing adequate notice or payment in lieu of notice, unless there is proven gross misconduct. Sudden termination without following due process—including a show-cause notice and an opportunity to be heard—may be considered wrongful termination. The applicable rules depend on the type of employment, the size of the establishment, and whether it is governed by the Industrial Disputes Act or a service agreement.",
    provisions: [
      {
        id: "p1",
        source: "Industrial Disputes Act, 1947",
        section: "Section 25-F",
        summary:
          "A workman who has completed one year of continuous service cannot be retrenched without: (1) one month's written notice or payment in lieu, and (2) retrenchment compensation equivalent to 15 days' average pay for every completed year of service.",
        originalText:
          "[SAMPLE TEXT] Section 25-F of the Industrial Disputes Act, 1947: No workman employed in any industry who has been in continuous service for not less than one year under an employer shall be retrenched by that employer until— (a) the workman has been given one month's notice in writing indicating the reasons for retrenchment and the period of notice has expired, or the workman has been paid in lieu of such notice, wages for the period of the notice; (b) the workman has been paid, at the time of retrenchment, compensation which shall be equivalent to fifteen days' average pay for every completed year of continuous service.",
        whyUsed:
          "This is the primary statutory protection against sudden termination for workers covered under the Industrial Disputes Act.",
      },
      {
        id: "p2",
        source: "Shops and Establishments Act (State-specific)",
        section: "Notice and Compensation Provisions",
        summary:
          "Each state has its own Shops and Establishments Act which typically requires employers to give advance notice or pay in lieu of notice before termination, even for commercial establishments not covered under the Industrial Disputes Act.",
        originalText:
          "[SAMPLE TEXT] Most state-level Shops and Establishments Acts provide that no employer shall dispense with the services of an employee who has been in continuous employment for a specified period (often six months to one year), without giving prior notice or wages in lieu of notice. The exact notice period varies by state and length of service.",
        whyUsed:
          "Many employees in commercial establishments are covered under state Shops and Establishments Acts rather than the Industrial Disputes Act.",
      },
    ],
    nextSteps: [
      "Obtain a copy of your appointment letter and any employment contract.",
      "Request a written explanation for termination from your employer in writing.",
      "Check whether your employer issued any prior notice or show-cause notice.",
      "Calculate the notice period and retrenchment compensation you may be entitled to.",
      "Consider filing a complaint with the Labour Commissioner in your district if the termination appears unlawful.",
      "Consult an advocate to assess whether to approach the Labour Court or Industrial Tribunal.",
    ],
    groundingNote:
      "This response is based on the Industrial Disputes Act, 1947 and general principles of state Shops and Establishments Acts. The applicability depends on your role, the size of the employer, and your state of employment.",
  },

  product: {
    situation: "Defective Product – Refund Refused",
    explanation:
      "As a consumer, you have the right to receive goods that are free from defects and match the description provided at the time of sale. If a product fails within its warranty period and the seller or manufacturer refuses to repair, replace, or refund it, this constitutes a deficiency in service and a violation of your consumer rights. You can approach the Consumer Disputes Redressal Commission for redressal.",
    provisions: [
      {
        id: "p1",
        source: "Consumer Protection Act, 2019",
        section: "Section 2(10) – Defect",
        summary:
          "A 'defect' means any fault, imperfection, shortcoming or inadequacy in the quality, quantity, potency, purity or standard of goods. A product failing during its warranty period is typically considered defective.",
        originalText:
          "[SAMPLE TEXT] Section 2(10) of the Consumer Protection Act, 2019: 'defect' means any fault, imperfection or shortcoming in the quality, quantity, potency, purity or standard which is required to be maintained by or under any law for the time being in force or under any contract, express or implied, or as is claimed by the trader in any manner whatsoever in relation to any goods or product.",
        whyUsed:
          "This definition establishes the legal basis for treating a malfunctioning product as defective under consumer law.",
      },
      {
        id: "p2",
        source: "Consumer Protection Act, 2019",
        section: "Section 35 – Complaint Before District Commission",
        summary:
          "A consumer can file a complaint with the District Consumer Disputes Redressal Commission for claims up to ₹1 crore. The Commission can direct replacement, repair, refund, and even award compensation for mental agony.",
        originalText:
          "[SAMPLE TEXT] Section 35 of the Consumer Protection Act, 2019 provides that a complaint may be filed before the District Commission where the value of goods or services paid as consideration does not exceed one crore rupees. The complaint may be filed by the consumer, a consumer association, or the Central or State Government on behalf of consumers.",
        whyUsed:
          "This provision gives you the right to file a formal legal complaint and seek a remedy from the appropriate consumer forum.",
      },
    ],
    nextSteps: [
      "Preserve all documentation: purchase invoice, warranty card, and records of complaints made to the seller or manufacturer.",
      "Send a formal written complaint to the seller and manufacturer requesting repair, replacement, or refund.",
      "If no satisfactory response within a reasonable time, file a consumer complaint before the District Consumer Disputes Redressal Commission.",
      "You may file the complaint yourself or through a consumer advocacy organisation. No advocate is mandatory at the District Commission level.",
      "The commission may award a replacement, refund, compensation, and recovery of legal costs.",
    ],
    groundingNote:
      "This response is based on the Consumer Protection Act, 2019. Remedies available may vary based on the value of the product and the specific facts of your case.",
  },
};

// --- Mock judgment result (used on Judgment Simplifier page) ---
export const MOCK_JUDGMENT = {
  caseTitle: "Lucknow Development Authority v. M.K. Gupta",
  court: "Supreme Court of India",
  year: "1993",
  caseType: "Consumer Law – Housing / Service Deficiency",
  brief:
    "The Supreme Court held that government authorities and statutory bodies providing housing or allied services fall within the definition of 'service' under consumer law. A consumer who suffers due to deficiency in such service is entitled to seek redressal before the Consumer Forum.",
  facts:
    "M.K. Gupta had booked a flat with the Lucknow Development Authority (LDA). Despite full payment, possession was delayed significantly without explanation. Gupta approached the Consumer Forum, which directed the LDA to hand over possession and pay compensation. The LDA challenged the jurisdiction of the Consumer Forum.",
  arguments:
    "LDA argued that as a statutory authority it was not a 'service provider' under the Consumer Protection Act and therefore the Consumer Forum had no jurisdiction. Gupta argued that the sale of a flat by LDA clearly constituted a service and that delay in delivery amounted to a deficiency in service.",
  issues: [
    "Whether a statutory authority providing housing falls within the definition of 'service' under the Consumer Protection Act.",
    "Whether delay in delivery of a flat constitutes deficiency in service.",
    "Whether the Consumer Forum has jurisdiction over complaints against statutory bodies.",
  ],
  decision:
    "The Supreme Court held that the LDA was indeed providing a 'service' within the meaning of the Act. The delay in handing over possession was a clear deficiency in service. The Court upheld the Consumer Forum's jurisdiction and affirmed the right of the consumer to seek compensation.",
  legalPrinciples: [
    "Statutory bodies and government departments engaged in commercial activities are not exempt from consumer law.",
    "Unreasonable delay in delivery of goods or services constitutes deficiency in service.",
    "Consumer Forums have broad jurisdiction and should be interpreted in a manner that advances consumer protection.",
    "Compensation may include the mental agony and harassment suffered by the consumer due to the deficiency.",
  ],
  paragraphs: [
    {
      id: "para1",
      number: "Paragraph 14",
      text: "The Act has to be interpreted keeping in mind the object for which it has been enacted. The consumer is not to be left without remedy merely because the service provider is a statutory body.",
      highlighted: false,
    },
    {
      id: "para2",
      number: "Paragraph 22",
      text: "Deficiency in service means any fault, imperfection, shortcoming or inadequacy in the quality, nature and manner of performance which is required to be maintained under any law or undertaken to be performed.",
      highlighted: false,
    },
    {
      id: "para3",
      number: "Paragraph 31",
      text: "The Commission has wide power to grant relief to the consumer. The power to award compensation for the harassment, agony and mental suffering caused to the consumer is incidental to the main power to redress the grievance.",
      highlighted: false,
    },
  ],
};
