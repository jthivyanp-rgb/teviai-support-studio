# Final quality assurance and safety review

TeviAI is an independent, publicly hosted portfolio prototype. The review started from the existing Streamlit app and kept the rule-based public workflow. The fictional scenarios demonstrate tested behaviours and human decision boundaries. [Live app](https://teviai-support-studio.streamlit.app/) · [Portfolio PDF](../output/pdf/teviai-final-portfolio.pdf)

## Release checks

| Check | Observed result |
| --- | --- |
| Python regression suite | 89 passed. Includes the regression for opening the newly submitted enquiry after filters were active. |
| Public 15-case register | 15 passed, 0 failed, 0 pending on the final runtime replay. The initial run recorded 14 pass and one privacy wording miss. |
| Hosted browser workflow | Chrome normal and fresh Incognito sessions opened the public app. Tested intake, dashboard counts, filters, drafts, reviewer edits, approval, rejection, escalation, clipboard copy, CSV, and the seven navigation destinations. |
| Mobile and accessibility | Chrome emulation at 320 and 390 CSS pixels. Axe-core reported zero violations across 13 tested states. The findings are scoped to the tested states. |
| Hosted Safety Lab | 18 of 18 cases passed. The provider failure scenario uses a local test double. |
| Runtime dependencies | The original Python 3.12 environment passed pip check for the installed packages. The requirements file defines the package ranges used by the app. |
| Public data and credentials | Reviewed the tracked release for common key signatures. Public scenarios used fictional data and rule-based drafts with no provider requests. |

[Scenario inputs, expected outcomes and retests](phase2_live_register.md) · [Phase 1 browser checklist](phase1_audit.md) · [12 evidence captures](screenshots/README.md) · [Risk register](risk_assessment.md)

## Feature status

| Status | Features and evidence |
| --- | --- |
| Implemented and tested | Public Streamlit pages, session-backed inbox and dashboard, rule classification and safety flags, policy-based drafts, human editing and review transitions, case escalation, filtered metadata export, session reset, and executable safety tests. |
| Implemented with some paths outside testing | The optional adapter requests a structured acknowledgement from Google Gemini. A live call with valid credentials and provider-side availability were outside the evaluation. Mobile results use Chrome emulation. Other browsers and assistive technologies were outside the browser check. |
| Simulated | Fictional business settings, selectable demo reviewer roles, and support requests about an order, booking, privacy or refund. Escalation assigns an in-session status for the demo reviewer. |
| Optional | Gemini-assisted acknowledgements for eligible built-in samples. Local test doubles verified valid selection, invalid output, provider failure and fallback labels. |
| Planned for any real-data pilot | Authenticated reviewer identities, role-based authorisation, protected audit storage, a data retention and deletion policy, and verified customer-system integrations. |

## Known limitations

Rules are heuristic and depend on wording. Free text lives in session memory, and redaction only covers recognised patterns. Activity Log is temporary and has no tamper protection. The public demo has no account login and does not have a connection to any order, booking, refund, payment or outbound messaging service. There is no evidence of real-customer adoption, measured time savings, full accessibility conformance, production readiness or official endorsement.

## Changes made during this review

- Moved the dashboard’s Open inbox and Load fictional samples actions above the charts. Added count labels to the category bars and kept the text alternative.
- Fixed a navigation problem found during the live register. Successful submission clears inbox filters and opens the new enquiry. Filter changes also recover an invalid selection.
- Put the CSV export and matching-event count above the Activity Log table.
- Added the filtered-inbox submission regression and made the browser tests wait for the dashboard metrics to render. Replayed the 15-case register and the browser audit on the final release.
- Captured the 12 workflow and test views. The CSV preview was rendered from the downloaded file. Updated the README, architecture, deployment instructions, test report, risk register and case study, and added the project overview, responsible AI assessment, this review and the final PDF.

[Project overview](project_overview.md) · [Responsible AI safety assessment](responsible_ai_assessment.md) · [Deployment instructions](deployment.md) · [Case study and contribution disclosure](portfolio_case_study.md)
