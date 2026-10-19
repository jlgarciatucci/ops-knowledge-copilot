# Azure/Streamlit login and usage tracking

This feature branch introduces an authenticated workspace, individual usage tracking, and a shared backend credential.

## Required configuration

1. Register a **Web** application in Microsoft Entra ID. Scope it to your tenant if this is an internal app.
2. Add the Streamlit callback address as a Web redirect URI: `https://<frontend-host>/oauth2callback`.
3. Create an Entra client secret. Store the client ID, client secret and OIDC issuer metadata in the Streamlit deployment secrets; refer to `.streamlit/secrets.example.toml`. Do **not** commit `.streamlit/secrets.toml`.
4. Generate **two independent strong random strings**: an OIDC `cookie_secret` for the Streamlit config, and a `FRONTEND_API_KEY` shared by the frontend and API. Set `FRONTEND_API_KEY` on the backend environment and in Streamlit secrets.
5. Run `scripts/user_usage_migration.sql` on the existing Postgres database **before** deploying the new API.
6. Deploy the backend and Streamlit frontend from this feature branch. Upgrade Streamlit to >=1.42 because `st.login` and `st.user` require OIDC support.
7. Log in and ask a question; visit **My usage** and verify that the record is attributed to your Microsoft account.

## Security boundaries

- Streamlit uses Microsoft's OIDC sign-in. Visitors cannot see the workspace before authentication.
- The backend is secured with a shared server-to-server API key. Only the trusted Streamlit server should have the key; **never** embed it in browser JavaScript or a public repository.
- The backend accepts an `x-user-email` header **only from callers with the shared key**. It does not independently validate an Entra token. This is a reasonable first-party demo design **but not sufficient for a multi-client enterprise system**.
- For enterprise deployment, require Entra-issued JWT bearer tokens in FastAPI, validate signature/issuer/audience/expiry, bind users by immutable Entra `oid` + tenant `tid`, and implement role-based authorization and per-document access policies.
- `/usage/me`, `/metrics/{query_id}`, and `/feedback` are user-scoped. Uploaded documents, ingestion, and vector retrieval are **still shared among all signed-in users**; upload privileges should be restricted before accepting untrusted users.
- The email address is used for simple reporting. Email is not an immutable user identifier; when hardening the system use Entra object IDs and keep email as a display field.
- Existing anonymous `query_logs` remain without an owner and are not displayed in per-user statistics.
- If Streamlit reports a missing email claim, configure Entra optional claims or use an appropriate account type. Test with the exact tenant/account you expect.
- Query logging records prompts and answers alongside the user's email; create a privacy notice, retention policy and delete/export process before inviting outside users.

## Deployment prerequisites

You must run the SQL migration, supply the OIDC configuration, and provide the matching shared key **before** deploying the UI. An absent key intentionally blocks API requests.

Microsoft Entra tutorial: https://docs.streamlit.io/develop/tutorials/authentication/microsoft
