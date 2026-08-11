# SheetMailer MVP

A deliberately small Mailmeteor-style mail merge app using Gmail + Google Sheets.

## Included

- Google OAuth
- Gmail sending through the Gmail API
- Google Sheet recipients
- Saved mailing templates
- `{{Column Header}}` personalization
- Scheduled campaigns
- Campaign statuses
- Per-recipient `PENDING / SENT / FAILED / SKIPPED`
- Writes `Status`, `Sent At`, and `Error` back to the source Sheet
- Pause / resume
- Retry failed sends
- Simple cron/worker

## Setup

1. Create a PostgreSQL database.
2. Run `sql/schema.sql` against it.
3. Copy `.env.example` to `.env.local`.
4. Generate secrets:
   - `SESSION_SECRET`: a long random string
   - `TOKEN_ENCRYPTION_KEY`: 32 random bytes encoded as 64 hex characters
   - `CRON_SECRET`: another long random string
5. In Google Cloud Console create an OAuth Web Client.
6. Enable **Gmail API** and **Google Sheets API**.
7. Add the redirect URI: `http://localhost:3000/api/auth/google/callback` for local development.
8. Fill `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
9. Install and run:

```bash
npm install
npm run dev
```

For local scheduled sending in another terminal:

```bash
npm run worker
```

On Vercel, `vercel.json` calls `/api/cron/process`. Set all environment variables in the project settings.

## Google Sheet format

Example:

| Email | Name | Company |
|---|---|---|
| jane@example.com | Jane | Acme |

Template:

```text
Subject: Quick question for {{Name}}

Hi {{Name}},

I wanted to reach out regarding {{Company}}.
```

The app automatically adds these columns when a campaign is created:

- Status
- Sent At
- Error

## Important production notes

This is an MVP, not a complete commercial mail platform. Before public launch, add:

- stronger OAuth verification/consent handling
- unsubscribe/compliance workflow appropriate to your use case and jurisdiction
- rate limiting and abuse prevention
- idempotency/locking for high concurrency
- monitoring/logging
- bounce handling if required
- database backups

The worker intentionally sends at most one pending recipient per campaign on each tick. This keeps the scheduler simple and avoids bursts. Increase throughput only after implementing proper rate controls and locking.
