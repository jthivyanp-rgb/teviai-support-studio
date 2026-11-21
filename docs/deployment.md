# Deploy to Streamlit Community Cloud

Publication changes who can see the source and demo. Obtain TeviAI owner approval for the repository visibility and public app before enabling access.

1. Run the test suite on Python 3.12 and follow the local demo workflow in the README.
2. Review Git status, the tracked file list and the intended remotes. Keep .env files, .streamlit/secrets.toml, virtual environments, CSV exports and any real records local.
3. Push the reviewed branch to the authorised GitHub repository. Choose the repository owner and visibility before initial upload.
4. In Community Cloud choose **Create app**. Select the repository and branch, set app.py as the entry point, and verify the Python version under **Advanced settings**. [Deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
5. Keep the shared demo in rule-based mode by leaving the Gemini secrets unset. For an authorised provider test, add GEMINI_API_KEY and optionally GEMINI_MODEL only in the secrets settings. [Community Cloud secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
6. Once deployed, verify the intended sharing setting and open the URL in a clean browser. Load fictional samples and run draft → submit → approve → copy, then test privacy escalation and CSV export. Open a second browser session and check that its inbox starts empty.
7. Record the deployment URL, commit, verification date and outcomes in the portfolio. Use the live URL only after verification.

The app has no account sign-in of its own. Shared deployments are suitable only for the fictional demo workflow and do not provide production access controls.
