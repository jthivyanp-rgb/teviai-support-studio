# Deploy to Streamlit Community Cloud

The [public TeviAI demo](https://teviai-support-studio.streamlit.app/) was deployed on 21 November 2026 from [release commit `35227c0`](https://github.com/jthivyanp-rgb/teviai-support-studio/commit/35227c067fb05aea1516838925cff6263f4ec33e), using Python 3.12 and rule-based drafting. [Hosted verification](test_report.md#hosted-verification)

Publication changes who can see the source and demo. Obtain TeviAI owner approval for the repository visibility and public app before enabling access.

1. Run the test suite on Python 3.12 and follow the local demo workflow in the README.
2. Review Git status, the tracked file list and the intended remotes. Keep .env files, .streamlit/secrets.toml, virtual environments, CSV exports and any real records local.
3. Push the reviewed branch to the authorised GitHub repository. Choose the repository owner and visibility before initial upload.
4. In Community Cloud choose **Create app**. Select the repository and branch, set app.py as the entry point, and verify the Python version under **Advanced settings**. [Deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
5. Keep the shared demo in rule-based mode by leaving the Gemini secrets unset. For an authorised provider test, add GEMINI_API_KEY and optionally GEMINI_MODEL only in the secrets settings. [Community Cloud secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
6. Once deployed, verify the intended sharing setting and open the URL in a clean browser. Load fictional samples and run draft → submit → approve → copy, then test privacy escalation and CSV export. Open a second browser session and check that its inbox starts empty.
7. Record the deployment URL, commit, verification date and outcomes in the portfolio. Use the live URL only after verification.

The app has no account sign-in of its own. Shared deployments are suitable only for the fictional demo workflow and do not provide production access controls.

## Final portfolio release

The final [runtime revision](https://github.com/jthivyanp-rgb/teviai-support-studio/commit/350ae7906ac4b5a34d1d84fdd951550c1009c93b) was checked on the public site in a fresh Chrome session. The final test run exercised the updated dashboard, new-enquiry selection, decision controls and CSV. The [final QA review](final_review.md) links the evidence and scope.
