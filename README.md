# MailPilot

MailPilot is a Gmail mail merge and campaign scheduling application inspired by Mailmeteor.

It allows users to connect Gmail, import recipients from Google Sheets or CSV, personalize messages with merge variables, schedule campaigns, send follow-ups, track replies, and sync sending status back to Google Sheets.

---

# Features

- Google OAuth login
- Gmail sending through Gmail API
- Google Sheets integration
- CSV import
- Manual recipient entry
- Personalized merge variables
- Test email sending
- Campaign scheduling
- Configurable delay between recipients
- Up to 4 follow-up emails
- Follow-ups in the same Gmail thread
- Reply detection
- Automatic stopping of follow-ups after reply
- Pause and resume campaigns
- Campaign status tracking
- Google Sheets status updates
- Duplicate-email handling
  - Send once per unique email address
  - Send once for every imported row

---

# Tech Stack

## Frontend

- Next.js
- React
- TypeScript

## Backend

- FastAPI
- SQLAlchemy
- Python
- SQLite for local development
- PostgreSQL-ready for production

## Google APIs

- Google OAuth 2.0
- Gmail API
- Google Sheets API

## Background Processing

- Python campaign worker

---

# Project Structure

```text
Mail_meteor_clone/
├── app/
│   ├── campaigns/
│   ├── components/
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── api.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   ├── worker.py
│   │   └── services/
│   │
│   ├── run_worker.py
│   ├── tests/
│   ├── .env.example
│   └── mailpilot.db
│
├── package.json
├── next.config.*
└── README.md
```

---

# Requirements

Before running the project, install:

- Node.js
- npm
- Python 3.11+
- Git
- `uv`
- Google Cloud account

Check your installations:

```bash
node --version
npm --version
python3 --version
git --version
uv --version
```

If `uv` is not installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the terminal if needed.

---

# 1. Clone the Repository

```bash
git clone https://github.com/MukundGarg/Mail_meteor_clone.git
cd Mail_meteor_clone
```

---

# 2. Install Frontend Dependencies

From the project root:

```bash
npm install
```

---

# 3. Install Backend Dependencies

Open a terminal:

```bash
cd backend
uv sync
```

This creates or uses the backend virtual environment and installs the Python dependencies.

---

# 4. Create the Backend Environment File

From the backend directory:

```bash
cp .env.example .env
```

The backend reads environment variables from its environment configuration.

The project may also read values from the root `.env.local`.

If the same variable exists in multiple environment files, keep the values consistent.

Never commit real secrets.

---

# 5. Configure Backend Environment Variables

Edit:

```text
backend/.env
```

Example:

```env
DATABASE_URL=sqlite+aiosqlite:///./mailpilot.db

FRONTEND_URL=http://localhost:3000

GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET

GOOGLE_REDIRECT_URI=http://localhost:3000/backend/api/v1/auth/google/callback

TOKEN_ENCRYPTION_KEY=YOUR_FERNET_KEY
SESSION_SECRET=YOUR_SESSION_SECRET
CRON_SECRET=YOUR_CRON_SECRET
```

If the root `.env.local` also contains these values, make sure they match.

---

# 6. Generate `TOKEN_ENCRYPTION_KEY`

From:

```bash
cd backend
```

Run:

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the generated value into:

```env
TOKEN_ENCRYPTION_KEY=GENERATED_VALUE
```

Do not manually invent a Fernet key.

Verify that the key is valid:

```bash
uv run python -c "from app.config import settings; from cryptography.fernet import Fernet; Fernet(settings.token_encryption_key.encode()); print('Fernet key OK')"
```

Expected:

```text
Fernet key OK
```

---

# 7. Generate `SESSION_SECRET`

Run:

```bash
openssl rand -hex 32
```

Copy the result into:

```env
SESSION_SECRET=GENERATED_VALUE
```

---

# 8. Generate `CRON_SECRET`

Run again:

```bash
openssl rand -hex 32
```

Copy the new result into:

```env
CRON_SECRET=GENERATED_VALUE
```

Use a different value from `SESSION_SECRET`.

---

# 9. Configure Google Cloud

Open Google Cloud Console.

Create or select a project.

Enable:

- Gmail API
- Google Sheets API

---

# 10. Configure OAuth Consent Screen

Configure the OAuth consent screen.

If your OAuth application is still in testing mode, add the Google accounts that should be allowed to sign in as test users.

---

# 11. Create Google OAuth Client

Create an OAuth Client ID.

Choose:

```text
Web application
```

Add this Authorized JavaScript Origin:

```text
http://localhost:3000
```

Add this Authorized Redirect URI:

```text
http://localhost:3000/backend/api/v1/auth/google/callback
```

Copy the generated Client ID and Client Secret into:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

The Client ID and Client Secret must belong to the same OAuth client.

---

# 12. Verify Google OAuth Configuration

From the backend directory:

```bash
cd backend
```

Check the Client ID:

```bash
uv run python -c "from app.config import settings; print(settings.google_client_id)"
```

Check the redirect URI:

```bash
uv run python -c "from app.config import settings; print(settings.google_redirect_uri)"
```

Expected redirect URI:

```text
http://localhost:3000/backend/api/v1/auth/google/callback
```

---

# 13. Run the FastAPI Backend

MailPilot requires three running processes:

1. FastAPI backend
2. Next.js frontend
3. Campaign worker

Open **Terminal 1**.

From the backend directory:

```bash
cd backend
```

For local OAuth development:

```bash
export OAUTHLIB_INSECURE_TRANSPORT=1
export OAUTHLIB_RELAX_TOKEN_SCOPE=1
```

Start FastAPI:

```bash
uv run uvicorn app.main:app --reload
```

Expected output:

```text
Uvicorn running on http://127.0.0.1:8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

Important:

```text
OAUTHLIB_INSECURE_TRANSPORT=1
```

is only intended for localhost development.

Do not use it in production.

---

# 14. Run the Next.js Frontend

Open **Terminal 2**.

Go to the project root:

```bash
cd Mail_meteor_clone
```

Run:

```bash
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

Open this URL in your browser.

---

# 15. Run the Campaign Worker

Open **Terminal 3**.

Go to the backend:

```bash
cd backend
```

Start the worker:

```bash
uv run python run_worker.py
```

Leave this terminal running.

The worker is responsible for:

- Checking scheduled campaigns
- Finding due recipients
- Sending Gmail messages
- Processing follow-ups
- Detecting replies
- Updating campaign counters
- Updating recipient status
- Updating Google Sheet status

If the worker is not running, campaigns may be scheduled successfully but emails will not be sent.

---

# 16. Verify That the Worker Is Running

On macOS or Linux:

```bash
ps aux | grep run_worker.py
```

A running worker should show lines similar to:

```text
uv run python run_worker.py
.../.venv/bin/python3 run_worker.py
```

A line containing only:

```text
grep run_worker.py
```

is not the worker.

---

# 17. Normal Local Development Setup

For normal local development, keep three terminals open.

## Terminal 1 — Backend

```bash
cd backend

export OAUTHLIB_INSECURE_TRANSPORT=1
export OAUTHLIB_RELAX_TOKEN_SCOPE=1

uv run uvicorn app.main:app --reload
```

## Terminal 2 — Frontend

```bash
npm run dev
```

## Terminal 3 — Worker

```bash
cd backend
uv run python run_worker.py
```

Then open:

```text
http://localhost:3000
```

---

# 18. Sign In With Google

Open:

```text
http://localhost:3000
```

Click the Google sign-in button.

Approve the requested permissions.

MailPilot requires Google permissions for:

- User identity
- Gmail sending
- Gmail thread access
- Reply detection
- Google Sheets reading
- Google Sheets updating

After login, MailPilot stores the Google refresh token in encrypted form.

---

# 19. Create a New Campaign

Inside MailPilot:

1. Open **New Campaign**
2. Choose a recipient source
3. Import recipients
4. Compose the email
5. Add optional follow-ups
6. Review the campaign
7. Select a scheduled time
8. Confirm and schedule

---

# 20. Add Recipients Manually

Choose:

```text
Manual
```

Enter recipient information such as:

- Email
- First name
- Last name
- Company

Add additional contacts as required.

---

# 21. Import Recipients From CSV

Choose:

```text
CSV
```

Upload a `.csv` file.

Example:

```csv
email,first_name,last_name,company
person@example.com,Mukund,Garg,Example Company
```

Additional CSV columns can also be used as personalization variables.

---

# 22. Import Recipients From Google Sheets

Choose:

```text
Google Sheets
```

Paste a Google Sheet URL:

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

Enter the sheet tab:

```text
Sheet1
```

Specify the email column.

MailPilot reads the rows from the sheet and converts them into campaign contacts.

---

# 23. Use Personalization Variables

MailPilot supports merge variables.

Example:

```text
Hi {{first_name}},
```

Example:

```text
I wanted to reach out regarding {{company}}.
```

Built-in fields include:

```text
{{first_name}}
{{last_name}}
{{company}}
```

Other imported spreadsheet or CSV columns may also be available.

---

# 24. Send a Test Email

Before scheduling a campaign, use:

```text
Send test to myself
```

The test email is sent to the currently connected Gmail account.

Use this to verify:

- Subject
- Body
- Merge variables
- Gmail connection
- Formatting

---

# 25. Add Follow-Ups

MailPilot supports up to four follow-up messages.

Each follow-up can contain:

- Delay in days
- Optional subject override
- Message body

Follow-ups are sent in the same Gmail thread.

If MailPilot detects that the recipient replied, future follow-ups are stopped.

---

# 26. Schedule a Campaign

Select:

- Start date
- Start time
- Delay between recipients

Available delay examples include:

```text
30 seconds
45 seconds
1 minute
2 minutes
```

The frontend converts the selected date and time to an ISO timestamp before sending it to the backend.

The backend stores scheduled campaign times in UTC.

---

# 27. Duplicate Email Handling

MailPilot supports duplicate email addresses.

Example imported data:

```text
person@example.com
person@example.com
person@example.com
other@example.com
```

This contains:

```text
4 imported rows
2 unique email addresses
2 duplicate rows
```

The user can decide how MailPilot should handle duplicates.

## Option 1 — Send only once to each email address

MailPilot deduplicates recipients.

Result:

```text
2 emails
```

## Option 2 — Send once for every imported row

MailPilot keeps every row.

Result:

```text
4 emails
```

This is useful when the same email address appears multiple times with different row data.

Each row keeps its own personalization information.

---

# 28. Google Sheets Campaign Status

For campaigns imported from Google Sheets, MailPilot can update status columns.

Example columns:

```text
MailPilot Status
MailPilot Last Sent
MailPilot Replied At
```

Possible status example:

```text
SENT
```

A `SENT` status means that Gmail accepted the send request through the Gmail API.

It does not guarantee inbox placement.

Final delivery can still depend on:

- Recipient email server
- Spam filtering
- Gmail reputation
- Bounces
- Recipient mailbox configuration

---

# 29. Local SQLite Database

Local development uses:

```text
backend/mailpilot.db
```

The database stores information such as:

- Users
- Encrypted Google refresh tokens
- Campaigns
- Recipients
- Sequence steps
- Campaign events
- Send state
- Reply state
- Failure information

---

# 30. Back Up the Local Database

Before database schema changes:

```bash
cd backend
cp mailpilot.db mailpilot.db.backup
```

Do not commit database backups to GitHub.

---

# 31. Recreate the Local Database

SQLAlchemy `create_all()` creates missing tables, but it does not automatically modify existing table constraints.

During local MVP development, if the schema changes significantly, you may need to recreate SQLite.

First stop:

- FastAPI backend
- Campaign worker

Then:

```bash
cd backend

cp mailpilot.db mailpilot.db.backup
rm mailpilot.db
```

Restart FastAPI:

```bash
export OAUTHLIB_INSECURE_TRANSPORT=1
export OAUTHLIB_RELAX_TOKEN_SCOPE=1

uv run uvicorn app.main:app --reload
```

The database will be recreated.

Important:

Deleting `mailpilot.db` removes:

- Existing users
- Existing campaigns
- Existing recipients
- Stored encrypted Google refresh tokens

You will need to sign in with Google again.

For production, proper database migrations should be used instead of deleting the database.

---

# 32. Production Database

For production, PostgreSQL is recommended.

Example:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mailpilot
```

Before using multiple workers, implement proper row-level job locking or claiming to avoid duplicate sends.

---

# 33. Troubleshooting OAuth HTTPS Error

If you see:

```text
InsecureTransportError:
OAuth 2 MUST utilize https.
```

Stop FastAPI.

Then restart it using:

```bash
cd backend

export OAUTHLIB_INSECURE_TRANSPORT=1
export OAUTHLIB_RELAX_TOKEN_SCOPE=1

uv run uvicorn app.main:app --reload
```

This is only for localhost development.

---

# 34. Troubleshooting OAuth Scope Error

If OAuth reports that the granted scopes changed, start the local backend with:

```bash
export OAUTHLIB_RELAX_TOKEN_SCOPE=1
```

Then:

```bash
uv run uvicorn app.main:app --reload
```

---

# 35. Troubleshooting Fernet Encryption Error

If you see:

```text
Fernet key must be 32 url-safe base64-encoded bytes
```

Generate a correct key:

```bash
cd backend

uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set:

```env
TOKEN_ENCRYPTION_KEY=GENERATED_VALUE
```

Verify:

```bash
uv run python -c "from app.config import settings; from cryptography.fernet import Fernet; Fernet(settings.token_encryption_key.encode()); print('Fernet key OK')"
```

Expected:

```text
Fernet key OK
```

---

# 36. Troubleshooting After Changing the Fernet Key

Google refresh tokens are encrypted using:

```text
TOKEN_ENCRYPTION_KEY
```

If this key changes after a Google account has already signed in, the existing encrypted refresh token may no longer be decryptable.

Fix:

1. Restart backend
2. Restart worker
3. Log out from MailPilot
4. Sign in with Google again

---

# 37. Troubleshooting Scheduled Campaigns Not Sending

First check whether the worker is running:

```bash
ps aux | grep run_worker.py
```

If the worker is missing:

```bash
cd backend
uv run python run_worker.py
```

Keep it running.

Without the worker, scheduled campaigns will not send.

---

# 38. Inspect Campaign and Recipient Errors

If a campaign is `RUNNING` but emails are not being sent, inspect the database.

From `backend`:

```bash
uv run python - <<'PY'
import asyncio

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Campaign, Recipient


async def main():
    async with SessionLocal() as db:
        campaigns = (
            await db.execute(
                select(Campaign)
                .order_by(Campaign.created_at.desc())
                .limit(5)
            )
        ).scalars().all()

        for campaign in campaigns:
            print(
                "\nCAMPAIGN:",
                campaign.name,
                "status=", campaign.status,
                "scheduled_at=", campaign.scheduled_at,
                "sent=", campaign.sent_count,
                "failed=", campaign.failed_count,
            )

            recipients = (
                await db.execute(
                    select(Recipient).where(
                        Recipient.campaign_id == campaign.id
                    )
                )
            ).scalars().all()

            for recipient in recipients:
                print(
                    "  ",
                    recipient.email,
                    "status=", recipient.status,
                    "next_send_at=", recipient.next_send_at,
                    "attempts=", recipient.attempts,
                    "error=", recipient.error,
                )


asyncio.run(main())
PY
```

Look at:

```text
error=
```

for the exact failure.

---

# 39. Stop MailPilot

Each process can be stopped using:

```text
Ctrl + C
```

Stop all three terminals:

- Backend
- Frontend
- Worker

---

# 40. Restart MailPilot

## Backend

```bash
cd backend

export OAUTHLIB_INSECURE_TRANSPORT=1
export OAUTHLIB_RELAX_TOKEN_SCOPE=1

uv run uvicorn app.main:app --reload
```

## Frontend

From project root:

```bash
npm run dev
```

## Worker

```bash
cd backend
uv run python run_worker.py
```

---

# 41. Run Backend Tests

From `backend`:

```bash
uv run pytest
```

---

# 42. Run Ruff

From `backend`:

```bash
uv run ruff check .
```

---

# 43. Build the Frontend

From the project root:

```bash
npm run build
```

Fix any build errors before deployment.

---

# 44. Git Workflow

Check changed files:

```bash
git status
```

Stage only the files you intentionally changed.

Example:

```bash
git add backend/app/api.py
git add backend/app/models.py
git add backend/app/schemas.py
git add app/campaigns/new/page.tsx
git add README.md
```

Commit:

```bash
git commit -m "Update MailPilot campaign handling and documentation"
```

Push:

```bash
git push origin main
```

---

# 45. Files That Must Not Be Committed

Never commit:

```text
.env
.env.local
backend/.env
backend/mailpilot.db
backend/mailpilot.db.backup
```

Also never commit:

- Google Client Secret
- Google OAuth authorization code
- Google refresh tokens
- `TOKEN_ENCRYPTION_KEY`
- `SESSION_SECRET`
- `CRON_SECRET`

---

# 46. Security Notes

- Never expose OAuth credentials publicly.
- Never commit environment secrets.
- Never commit the SQLite database.
- Use HTTPS in production.
- Do not use `OAUTHLIB_INSECURE_TRANSPORT=1` in production.
- Store encryption keys securely.
- Respect Gmail sending limits.
- Complete required Google OAuth verification before public deployment.
- Test campaigns with email addresses you control first.
- Follow applicable anti-spam and privacy regulations.

---

# 47. Quick Start

After completing initial setup, MailPilot requires three terminals.

## Terminal 1 — Backend

```bash
cd backend
export OAUTHLIB_INSECURE_TRANSPORT=1
export OAUTHLIB_RELAX_TOKEN_SCOPE=1
uv run uvicorn app.main:app --reload
```

## Terminal 2 — Frontend

```bash
npm run dev
```

## Terminal 3 — Worker

```bash
cd backend
uv run python run_worker.py
```

Then open:

```text
http://localhost:3000
```

Sign in with Google and create a campaign.

---

# 48. Quick Health Checklist

Before testing a campaign, confirm:

```text
[ ] Frontend is running on localhost:3000
[ ] FastAPI is running on 127.0.0.1:8000
[ ] Campaign worker is running
[ ] Google OAuth login works
[ ] Gmail API is enabled
[ ] Google Sheets API is enabled
[ ] GOOGLE_CLIENT_ID is correct
[ ] GOOGLE_CLIENT_SECRET is correct
[ ] GOOGLE_REDIRECT_URI is correct
[ ] TOKEN_ENCRYPTION_KEY is valid
[ ] SESSION_SECRET is configured
[ ] CRON_SECRET is configured
[ ] Test email works
```

Once all checks pass, MailPilot is ready for local campaign testing.