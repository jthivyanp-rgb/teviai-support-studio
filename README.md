# TeviAI Support Studio

Responsible customer-support automation for small businesses. TeviAI helps a reviewer classify enquiries, draft a reply, and record a decision. Approved replies are available to copy. The application has no customer messaging, refund, booking, or account-action integrations.

TeviAI is an independent GovAI Fellowship portfolio project. Use fictional data throughout the demo.

[Open the public TeviAI demo](https://teviai-support-studio.streamlit.app/)

## Run on Windows

Use Python 3.12. In PowerShell from this folder:

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe -m pytest -q
    .\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1

Open [the local app](http://localhost:8501/). If the existing virtual environment is already installed, start with the test or launch command.

## Try the workflow

1. Open Dashboard and choose **Load fictional samples**, or submit a fictional message in Customer Enquiries.
2. Open a delivery case in Draft Studio. Generate a rule-based draft, edit it if needed, and select **Submit for review**.
3. Open Approval Centre, choose a demo reviewer, and approve, reject or escalate the draft. The refund sample requires the reviewer to acknowledge its high-risk flag. Flagged privacy cases go to escalation.
4. Find approved text under **Approved replies**. Open Activity Log to filter and export the decision metadata.
5. Open Safety Lab to run the repeatable scenarios. Use Settings to adjust fictional policies and reset the session with confirmation.

## Optional Gemini mode

Use rule-based mode without credentials. To try AI-assisted drafting, set GEMINI_API_KEY as an environment variable or copy the supplied example to .streamlit/secrets.toml and fill it locally. GEMINI_MODEL overrides the configured default of gemini-3.8-flash. Choose **AI-Assisted** in Settings. In Draft Studio, explicitly opt in for an eligible built-in fictional enquiry.

The provider selects an acknowledgement from an allowlist. TeviAI validates the response and uses its rule-based policy text. Manual enquiries, flagged personal information, and high-risk cases stay local. Provider failures produce a visibly labelled rule-based draft. Review [the Gemini model reference](https://aistudio.google.com/docs/models/gemini-3.8-flash) and [Gemini API terms](https://aistudio.google.com/docs/terms).

## Evidence and deployment

- [Architecture and workflow](docs/architecture.md)
- [Risk assessment](docs/risk_assessment.md)
- [Test report](docs/test_report.md)
- [Deployment guide](docs/deployment.md)
- [Portfolio case study](docs/portfolio_case_study.md) and [PDF](output/pdf/teviai-case-study.pdf)

Active records live in Streamlit Session State. A reload or lost session can clear them. Reviewer roles demonstrate a human decision and are selectable demo identities. The risk checks are heuristics, and the export is temporary session history. See [Streamlit Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state).

[Product screenshots](docs/screenshots/README.md)
