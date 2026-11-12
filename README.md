# Placement Application Tracker

The Streamlit app tracks job applications and includes company search, status
filters and updates, confirmed deletion, CSV export, and upcoming interview
dates. It also has an OpenAI-powered placement preparation chatbot.

## Run locally

Install the requirements and initialize the database:

```powershell
python -m pip install -r requirements.txt
python init_db.py
```

Set your OpenAI key in the current PowerShell session, then start the app:

```powershell
$env:OPENAI_API_KEY = "your-openai-api-key"
python -m streamlit run app.py
```

You can also configure `OPENAI_API_KEY` in `.streamlit/secrets.toml`. That
secrets file is excluded by `.gitignore`; never commit or share your API key.
For Streamlit Community Cloud, add `OPENAI_API_KEY` under the app's **Settings
→ Secrets**.

The chatbot conversation is kept for the current Streamlit session. The tracker
uses the local SQLite database; local database changes may not persist when
hosted on Streamlit Community Cloud.
