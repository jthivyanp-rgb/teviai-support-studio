# Architecture

Streamlit runs the seven screens and keeps each browser session’s enquiries, business settings, and event list isolated. Core classification, screening, drafting and review routines run in Python and can be exercised without the browser.

~~~mermaid
flowchart TD
    A["Manual fictional entry or built-in sample"] --> B["Validate and assign an enquiry ID"]
    B --> C["Classify and flag risk"]
    C --> T["Compose local policy template"]
    C -->|"Eligible built-in sample and opt-in"| G["Gemini selects an approved acknowledgement"]
    G --> V["Validate opening or fall back"]
    V --> T
    C -->|"Specialist case"| E["Escalate to owner"]
    T --> D["Edit and submit draft"]
    D --> R["Human review and fresh checks"]
    R -->|"Approve"| P["Approved — Not Sent · copy available"]
    R -->|"Reject"| X["Rejected"]
    R -->|"Escalate"| E
    R -->|"Return"| D
    C -.-> L["Session activity metadata and CSV"]
    T -.-> L
    R -.-> L
    E -.-> L
~~~

| Module | Responsibility |
| --- | --- |
| app.py | Streamlit pages, per-session navigation, review controls |
| src/classification.py | Keyword labels, confidence and matches |
| src/risk_detection.py | Privacy, instruction override, sensitive cases and draft claims |
| src/response_generator.py | Policy-grounded templates and missing-policy wording |
| src/ai_provider.py | Sample eligibility, structured response validation, fallback |
| src/approval_workflow.py | Transitions, draft review and event recording |
| src/activity_logger.py | Field allowlist and spreadsheet-safe CSV |
| src/business_config.py and src/data_models.py | Fictional defaults, status, reviewer roles and input bounds |
| src/safety_lab.py | Executable fictional test scenarios |

The normal lifecycle is New → Classified → Draft ready → Pending review → Approved, Rejected, or Escalated. Classified and draft-ready cases can be escalated directly. Pending reviews can return for revision. If the underlying policies changed, the reviewer must regenerate the draft before approving. Terminal statuses close the enquiry in this session.

Events capture timestamp, enquiry ID, action, category, risk level and codes, draft mode, reviewer role, and previous/current status. Free-form messages, draft text, customer names and decision notes are excluded. The reviewer can select a predefined decision reason, which stays with the enquiry.
