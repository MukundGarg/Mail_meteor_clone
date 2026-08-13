# MailPilot

A Mailmeteor-style Gmail mail merge application with a Next.js dashboard and a rules-based FastAPI backend.

## Included workflow

- Sign in and connect Gmail through Google OAuth
- Import recipients from Google Sheets or CSV, or add them manually
- Personalize subject and body with `{{column_name}}` merge variables
- Preview merged content and send a test email
- Send immediately or schedule a campaign
- Add up to four user-written follow-ups
- Send follow-ups in the original Gmail thread
- Check Gmail before every follow-up and stop the sequence when a reply is detected
- Pause and resume campaigns
- Synchronize sent/replied status back to imported Google Sheets
- View campaign, contact, template, failure, and reply status in the dashboard

The application does not generate email copy and does not create Gmail drafts. The user writes and approves the complete campaign before scheduling it.

## Project structure

```text
app/                   Next.js and React frontend
backend/app/           FastAPI application
backend/app/worker.py  Durable campaign processor
backend/tests/         Backend tests
```

## 1. Backend setup with uv

```powershell
cd backend
Copy-Item .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

SQLite is used by default so the project starts without a separate database. For production, set an async PostgreSQL connection string:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mailpilot
```

Generate a Fernet encryption key for `TOKEN_ENCRYPTION_KEY`:

```powershell
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 2. Google Cloud configuration

Enable these APIs:

- Gmail API
- Google Sheets API

Create a Web OAuth client and register:

```text
http://localhost:3000/backend/api/v1/auth/google/callback
```

Add the credentials to `backend/.env`:

```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:3000/backend/api/v1/auth/google/callback
```

The application requests `gmail.modify` because it must send messages, keep follow-ups in a thread, and detect replies. This is a restricted scope and requires Google OAuth verification before a public launch.

## 3. Frontend

From the repository root:

```powershell
npm install
npm run dev
```

Open `http://localhost:3000`. Next.js proxies `/backend/*` to FastAPI at `http://127.0.0.1:8000`.

## 4. Campaign worker

In another terminal:

```powershell
cd backend
uv run python run_worker.py
```

Run only one worker for the current MVP. A production deployment should use PostgreSQL row-level job claiming before scaling to multiple workers.

## Verification

```powershell
cd backend
uv run ruff check .
uv run pytest

cd ..
npm run build
```

## Safety before real outreach

- Start with one to three addresses that you control.
- Confirm merge-variable previews and test emails.
- Respect Gmail sending limits and applicable anti-spam/privacy requirements.
- Configure a real encryption key and strong session/cron secrets.
- Complete Google verification before inviting public users.
