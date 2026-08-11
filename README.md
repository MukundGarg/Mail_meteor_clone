# Mail Automator MVP

A lightweight Mailmeteor-style mail merge application built with Gmail, Google Sheets, Next.js, and PostgreSQL.

The goal of this project is to provide a simple workflow for sending personalized email campaigns directly from a Google Sheet without building a full CRM or complex marketing platform.

---

# Features

* Google account connection using OAuth
* Send emails through the Gmail API
* Use Google Sheets as the recipient source
* Personalized email templates
* Variables such as `{{Name}}`, `{{Company}}`, `{{Role}}`
* Campaign scheduling
* Campaign status tracking
* Recipient-level status tracking
* Automatic Google Sheet updates
* Pause and resume campaigns
* Retry failed emails
* Background campaign worker

Recipient statuses:

```text
PENDING
SENT
FAILED
SKIPPED
```

Campaign statuses include:

```text
SCHEDULED
RUNNING
PAUSED
COMPLETED
FAILED
```

---

# How It Works

The basic workflow is:

```text
Google Sheet
     ↓
Create Campaign
     ↓
Write Email Template
     ↓
Personalize Using Sheet Columns
     ↓
Schedule / Start Campaign
     ↓
Worker Sends Emails Through Gmail
     ↓
Google Sheet Is Updated
```

Example Google Sheet:

| Email                                       | Name | Company     | Role    |
| ------------------------------------------- | ---- | ----------- | ------- |
| [jane@example.com](mailto:jane@example.com) | Jane | Acme        | Founder |
| [john@example.com](mailto:john@example.com) | John | Example Inc | CTO     |

You can then write:

```text
Hi {{Name}},

I came across {{Company}} and noticed that you work there as {{Role}}.

I wanted to reach out regarding...
```

Each recipient receives a personalized email.

---

# Requirements

Before running the project, install:

* Node.js
* npm
* PostgreSQL
* Git
* A Google account
* A Google Cloud project

Recommended Node version:

```text
Node.js 20+
```

---

# 1. Clone the Repository

```bash
git clone https://github.com/MukundGarg/Mail_meteor_clone.git
cd Mail_meteor_clone
```

Install dependencies:

```bash
npm install
```

---

# 2. Create a PostgreSQL Database

Make sure PostgreSQL is running.

Create the database:

```bash
createdb mailmerge
```

Or open PostgreSQL:

```bash
psql postgres
```

and run:

```sql
CREATE DATABASE mailmerge;
```

Exit with:

```sql
\q
```

---

# 3. Initialize the Database Tables

Run the included schema:

```bash
psql "postgres://postgres:postgres@localhost:5432/mailmerge" -f sql/schema.sql
```

Change the username/password if your PostgreSQL setup is different.

You can verify the tables:

```bash
psql "postgres://postgres:postgres@localhost:5432/mailmerge"
```

Then:

```sql
\dt
```

You should see tables similar to:

```text
users
templates
campaigns
recipients
```

Exit:

```sql
\q
```

---

# 4. Configure Environment Variables

Copy:

```bash
cp .env.example .env.local
```

Your `.env.local` should look similar to:

```env
DATABASE_URL=postgres://postgres:postgres@localhost:5432/mailmerge

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/google/callback

APP_URL=http://localhost:3000

SESSION_SECRET=
TOKEN_ENCRYPTION_KEY=
CRON_SECRET=
```

---

# 5. Generate Application Secrets

Generate random secrets using:

```bash
openssl rand -hex 32
```

Run this command three times.

Use the generated values for:

```env
SESSION_SECRET=YOUR_SECRET
TOKEN_ENCRYPTION_KEY=YOUR_64_CHARACTER_HEX_KEY
CRON_SECRET=YOUR_SECRET
```

Important:

`TOKEN_ENCRYPTION_KEY` must be exactly 64 hexadecimal characters.

Example:

```env
TOKEN_ENCRYPTION_KEY=9a2f4c7b8d1e3f0a6b5c4d2e1f9876543210abcdef1234567890abcdef123456
```

Do not commit `.env.local` to GitHub.

---

# 6. Configure Google Cloud

Go to Google Cloud Console and create or select a project.

You need to configure Google OAuth and enable the APIs used by the application.

## Enable APIs

Enable:

* Gmail API
* Google Sheets API

---

# 7. Configure Google OAuth

Open:

```text
Google Cloud Console
→ Google Auth Platform
```

Configure the OAuth consent screen.

For development, you can keep the app in:

```text
Testing
```

Then create an OAuth Client.

Choose:

```text
Application type: Web application
```

Add this Authorized Redirect URI:

```text
http://localhost:3000/api/auth/google/callback
```

Copy the generated Client ID and Client Secret into `.env.local`:

```env
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET
```

---

# 8. Add Yourself as a Test User

If your Google OAuth app is in Testing mode, Google only allows approved test accounts to sign in.

Go to:

```text
Google Auth Platform
→ Audience
→ Test users
```

Add the Gmail account you plan to use.

For example:

```text
youraccount@gmail.com
```

Otherwise, you may see:

```text
Access blocked: App has not completed the Google verification process
```

---

# 9. Start the Application

Run:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

You should see the Mail Automator dashboard.

---

# 10. Connect Your Google Account

Click:

```text
Connect Google Account
```

Sign in using the same Google account that you added as an OAuth test user.

The application requests permission to:

* identify your Google account
* send email through Gmail
* read and update Google Sheets

---

# 11. Prepare Your Google Sheet

Create a Google Sheet.

Example:

| email                                       | name | company | role    |
| ------------------------------------------- | ---- | ------- | ------- |
| [test@example.com](mailto:test@example.com) | Jane | Acme    | Founder |

The exact column names can be used as template variables.

For example:

```text
{{name}}
{{company}}
{{role}}
```

The Google account connected to Mail Automator must have:

```text
Editor
```

permission on the Sheet.

Viewer or Commenter access is not enough because the application writes campaign statuses back to the Sheet.

---

# 12. Google Sheet Status Columns

When a campaign is created, the application automatically adds:

```text
Status
Sent At
Error
```

Your Sheet may become:

| email                                       | name | company | Status | Sent At    | Error |
| ------------------------------------------- | ---- | ------- | ------ | ---------- | ----- |
| [test@example.com](mailto:test@example.com) | Jane | Acme    | SENT   | 2026-08-11 |       |

These columns are managed automatically.

---

# 13. Create Your First Campaign

Open:

```text
New Campaign
```

Then:

1. Paste or select your Google Sheet.
2. Select the required Sheet tab.
3. Choose the email column.
4. Enter the email subject.
5. Write your email body.
6. Insert Sheet variables using `{{Column Name}}`.
7. Preview the campaign.
8. Schedule or start the campaign.

Example subject:

```text
Quick question for {{name}}
```

Example email:

```text
Hi {{name}},

I came across {{company}} and wanted to reach out.

Would you be available for a quick conversation?

Regards,
Your Name
```

---

# 14. Start the Campaign Worker

The web application and campaign worker run separately during local development.

Keep your app running in Terminal 1:

```bash
npm run dev
```

Open Terminal 2.

Because `.env.local` may not automatically load into the worker process, run:

```bash
set -a
source .env.local
set +a
npm run worker
```

You should see output like:

```text
200 {"processed":1,"results":[{"status":"SENT"}]}
```

When the campaign finishes:

```text
200 {"processed":1,"results":[{"status":"COMPLETED"}]}
```

If you see:

```text
{"processed":0,"results":[]}
```

that is normal.

It simply means there are currently no campaigns ready to process.

---

# Optional: Automatically Load `.env.local` in the Worker

Instead of manually running:

```bash
set -a
source .env.local
set +a
```

you can install dotenv:

```bash
npm install dotenv
```

Then add this at the top of:

```text
scripts/worker.mjs
```

```js
import { config } from 'dotenv';

config({ path: '.env.local' });
```

After that:

```bash
npm run worker
```

should work directly.

---

# 15. Monitor Campaign Status

Open the campaign details page.

You should see statuses such as:

```text
SCHEDULED
RUNNING
COMPLETED
PAUSED
FAILED
```

Individual recipients can have:

```text
PENDING
SENT
FAILED
SKIPPED
```

The Google Sheet will also be updated after every send.

---

# Testing Recommendation

Before sending any real campaign, create a small Sheet containing only your own email addresses.

Example:

| email                                                       | name        |
| ----------------------------------------------------------- | ----------- |
| [youraccount@gmail.com](mailto:youraccount@gmail.com)       | Test User   |
| [anotheraccount@gmail.com](mailto:anotheraccount@gmail.com) | Test User 2 |

Start with 1–3 recipients.

Verify:

```text
Campaign created
        ↓
Worker processes campaign
        ↓
Email received
        ↓
Recipient becomes SENT
        ↓
Google Sheet updated
        ↓
Campaign becomes COMPLETED
```

---

# Troubleshooting

## Missing `client_id`

Error:

```text
Missing required parameter: client_id
```

Check:

```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

Make sure both values are configured in `.env.local`.

Restart:

```bash
npm run dev
```

---

## Google OAuth Access Blocked

Error:

```text
Access blocked: App has not completed the Google verification process
```

Go to:

```text
Google Auth Platform
→ Audience
→ Test users
```

Add the Google account you are trying to use.

---

## TOKEN_ENCRYPTION_KEY Error

Error:

```text
TOKEN_ENCRYPTION_KEY must be 64 hex chars
```

Generate a valid key:

```bash
openssl rand -hex 32
```

Put the output into:

```env
TOKEN_ENCRYPTION_KEY=
```

---

## Database Does Not Exist

Error:

```text
database "mailmerge" does not exist
```

Create it:

```bash
createdb mailmerge
```

---

## Relation `users` Does Not Exist

Error:

```text
relation "users" does not exist
```

Initialize the database:

```bash
psql "$DATABASE_URL" -f sql/schema.sql
```

Or use the full URL:

```bash
psql "postgres://postgres:postgres@localhost:5432/mailmerge" -f sql/schema.sql
```

---

## Google Sheets Permission Error

Error:

```text
403 Forbidden
The caller does not have permission
```

Make sure the Google account connected to Mail Automator has:

```text
Editor
```

access to the Google Sheet.

Also check that the Sheet or header row is not protected.

---

## Worker Says `CRON_SECRET is required`

Run:

```bash
set -a
source .env.local
set +a
npm run worker
```

Or configure the worker to load `.env.local` using `dotenv`.

---

## Worker Shows `processed: 0`

Example:

```text
{"processed":0,"results":[]}
```

This is not an error.

It means no campaign is currently:

* scheduled for the current time
* running
* waiting for recipients to be processed

Create or resume a campaign and wait for the next worker cycle.

---

# Sending Behavior

The MVP intentionally processes a small number of emails per worker cycle.

This is designed to keep local development predictable and reduce the chance of accidentally sending a large batch.

Do not significantly increase throughput until you have added proper:

* rate limiting
* locking
* retries
* abuse prevention
* concurrency handling

---

# Project Structure

A simplified overview:

```text
Mail_meteor_clone/
│
├── app/
│   ├── api/
│   ├── campaigns/
│   └── ...
│
├── lib/
│   ├── db.ts
│   ├── google.ts
│   ├── crypto.ts
│   └── ...
│
├── scripts/
│   └── worker.mjs
│
├── sql/
│   └── schema.sql
│
├── .env.example
├── package.json
└── README.md
```

---

# Security

Never commit:

```text
.env.local
GOOGLE_CLIENT_SECRET
DATABASE_URL
TOKEN_ENCRYPTION_KEY
SESSION_SECRET
CRON_SECRET
```

Make sure `.gitignore` contains:

```gitignore
.env
.env.local
.env*.local
node_modules
.next
```

If a secret is accidentally committed publicly, rotate it immediately.

---

# Production Notes

This project is an MVP and should not be treated as a production-ready mass-email platform.

Before a public launch, consider adding:

* Google OAuth verification
* unsubscribe functionality
* compliance controls
* Gmail sending-limit handling
* bounce handling
* rate limiting
* anti-abuse protections
* idempotency
* campaign locking
* monitoring
* structured logging
* database backups
* automatic production scheduling
* better error reporting

You should also ensure that your email usage complies with applicable anti-spam, privacy, and marketing laws.

---

# Current MVP Goal

The current version focuses on a single simple workflow:

```text
Google Sheet
+
Personalized Template
+
Gmail
+
Campaign Scheduler
=
Simple Mail Merge
```

It intentionally avoids features such as CRM management, complex analytics, AI writing, A/B testing, team management, and advanced marketing automation.
