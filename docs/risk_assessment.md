# Prototype risk assessment

Scope covers an unauthenticated, fictional-data demo for small-business support. The controls below reduce specific risks. The remaining exposure determines what would be needed before any use with customer data.

| Risk | Possible consequence | Implemented control | Remaining exposure |
| --- | --- | --- | --- |
| Real data entered by mistake | Personal information viewed or shared | Fictional-data copy, limited fields, masking of detected patterns in customer message views, minimal CSV, provider restricted to built-in samples | Free text can hold undiscovered identifiers in session memory. No authentication or retention guarantee. |
| Customer text contains an instruction override | Unsafe draft or disclosure | Pattern checks, separation of system instructions from sample text, approved model output keys, no provider tools | Pattern checks miss paraphrases. Reviewers see untrusted text. |
| Unsupported delivery, pricing or transaction claim | Incorrect customer expectation | Templates omit live claims, draft screening blocks detected claims, policy changes require regeneration | Rules have false positives and false negatives. Reviewers must independently verify facts. |
| Health, legal or privacy request goes through routine approval | Mishandled specialist case | High-risk topic checks and mandatory escalation on detected routes | Some phrasing will escape detection. Escalation is an in-app status and the owner must follow up outside the demo. |
| Approval mistaken for execution | Message sent or transaction action assumed | Approved — Not Sent, manual copy surface, no integrations for transmission or transactions | A person can still misuse copied content outside the system. |
| Reviewer identity disputed | Weak accountability | Selectable demo roles and a timestamped workflow history | Anyone with the session can select either role. Records clear with the session and can be altered by the host. |
| AI unavailable or invalid | Workflow interrupted | Bounded timeout, schema and key checks, visible rule-based fallback | Live service availability and model access depend on the configured account. |
| Spreadsheet evaluates exported metadata | Executable content in a spreadsheet cell | Metadata allowlist and formula-prefix escaping | Spreadsheet behaviour varies. The export should still be treated as data. |

Before a production pilot, design and test authentication, authorisation, durable audit records, customer-data isolation, retention and deletion controls, provider governance and ongoing evaluation. Assess performance on representative, approved test data before relying on the alerts.

## Observed risk controls

The live privacy wording defect, its correction and the results of all 15 scenarios are recorded in the functional register. The safety assessment links the tested safeguards to residual exposure. [Live test register](phase2_live_register.md) · [Responsible AI assessment](responsible_ai_assessment.md)
