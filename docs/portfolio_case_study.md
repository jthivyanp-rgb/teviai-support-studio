# TeviAI: Designing Human-Centred AI Automation for Small Businesses

Independent GovAI Fellowship portfolio project. This project was neither commissioned nor endorsed by GovAI.

## The problem

Small retailers and service businesses receive similar questions about orders, returns, products and bookings. Responding to routine messages takes time. The same inbox also receives cases that depend on specialist knowledge, customer identity checks or decisions that are outside a drafting tool’s authority.

The primary stakeholder is a small-business owner who needs to review replies efficiently and see which cases need attention. A shift lead needs clear escalation and consistent fictional policies. A customer needs a reply grounded in facts and a route to a person when context is missing. The prototype does not measure time saved or customer satisfaction.

## What was built

TeviAI uses Streamlit and Python to take fictional enquiries through classification, risk screening, drafting and human review. The seven pages cover session metrics, inbox search, drafting, approval, metadata export, business settings and executable safety scenarios. The workflow checks which actions are available at each stage. The default rule-based path runs locally without a provider key.

## Design decisions

- **Make approval a separate step.** A reviewer sees the original message, edits the draft and chooses a decision. Approved replies become available to copy. A detected specialist request requires escalation.
- **Keep business facts local.** Template wording comes from fictional policies or asks staff to verify the information. An optional model selects only the acknowledgement for an eligible built-in example. The workflow accepts an allowlisted response key and uses a visible fallback on failure.
- **Record decisions with less data.** The history captures metadata and demo reviewer roles. Enquiry text and drafted replies are excluded from CSV exports.
- **Show what the checks observed.** Safety Lab exposes expected and actual outcomes. Dashboard counts come from session records.

## Evidence and limitations

The [test report](test_report.md) records the executed checks and remaining verification gaps. The [architecture](architecture.md) shows how generation, review and activity logging connect. The [risk assessment](risk_assessment.md) records residual privacy, reliability and oversight risks.

The warning rules are deliberately simple and can miss unfamiliar wording. The session can disappear on reload and has no durable, tamper-protected history. Reviewer roles represent a decision in the demo and are not authenticated user identities. Live Gemini behaviour and real-world outcomes require separate evidence.

## Lessons

Separating drafting and approval makes authority visible at the point where a decision happens. Restricting provider output can remove entire classes of unsupported generated claims while giving the model a useful, narrow role. A local prototype can demonstrate these controls, while a production pilot would need validated data governance, identity management, escalation ownership and measurement with real stakeholders.

## Contribution and AI assistance

The project owner supplied the project brief, required safeguards and live test inputs, and authorised the public demo and source release. The existing Streamlit project was the starting point. Codex assisted with implementation changes, regression tests, Chrome automation, defect investigation, screenshot capture and documentation. The evidence distinguishes the owner's project decisions from work performed with AI assistance.
