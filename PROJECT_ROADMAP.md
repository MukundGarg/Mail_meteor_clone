# MailPilot Project Roadmap

## 1. Goal and execution strategy

MailPilot should reach the market in three controlled releases:

1. **Internal pilot:** prove that Gmail sending, follow-ups, reply detection, pause/resume, and Sheet synchronization work safely with accounts and recipients you control.
2. **Private beta:** support 5-20 invited users with production infrastructure, observability, recovery procedures, and clear sending safeguards.
3. **Public launch:** complete Google OAuth verification, compliance work, onboarding, support, analytics, and capacity testing before allowing self-service signups.

The current repository is a functional proof of concept, not a production-ready service. The core happy path exists, so the next work should prioritize correctness, safety, and operations rather than adding broad new features.

### Planning assumptions

- One full-time developer owns product and engineering.
- A private beta is the first commercial-quality target.
- Gmail and Google Sheets remain the only providers for v1.
- Users write their own messages; AI copy generation is out of scope.
- Target duration: **8 weeks to private beta**, then **2-4 additional weeks plus Google's review time** for public launch.
- If development is part-time, multiply the schedule by roughly two.

## 2. Current baseline

### Already implemented

- Google OAuth sign-in and encrypted refresh-token storage
- Next.js dashboard, campaign wizard, campaign details, contacts, and templates
- Manual, CSV, and Google Sheets recipient import
- Merge variables and a sample preview
- Test email to the connected account
- Immediate or scheduled campaigns
- Up to four follow-ups in the original Gmail thread
- Reply detection before follow-ups
- Pause and resume
- Status synchronization to Google Sheets
- SQLite development database and PostgreSQL driver support
- FastAPI campaign worker with retry attempts

### Baseline verification on August 20, 2026

- `uv run ruff check .`: passed
- `uv run pytest`: 2 tests passed
- `npm run build`: passed on Next.js 16.3.0

### Main gaps

- Only two narrow unit tests; no API, worker, frontend, or end-to-end coverage
- No database migrations; tables are created directly at application startup
- Worker is safe only as a single process and has no durable job lease/idempotency design
- No production observability, alerting, audit UI, or operational runbook
- No unsubscribe/suppression list, daily sending caps, quiet hours, or compliance controls
- No campaign draft/edit/cancel workflow or safe pre-send approval gate
- CSV/Sheet mapping and validation are basic; malformed rows and missing merge data need clearer handling
- Authentication needs production hardening, including CSRF review, secure-cookie policy, token revocation handling, and secret validation
- Google OAuth restricted-scope verification is required before public use
- No CI/CD, staging environment, backup/restore process, or load/recovery testing

## 3. Release roadmap

## Phase 0 — Freeze scope and clean the baseline (Days 1-2)

**Outcome:** a reproducible project with a written v1 boundary and no ambiguous local setup.

### Tasks

- Define the v1 user: an individual or small team sending low-volume, personalized outreach through one Gmail account.
- Set explicit v1 limits: maximum recipients per campaign, messages per day, follow-up count, attachment policy, and supported CSV size.
- Keep these out of v1: multi-provider email, AI writing, team workspaces, billing, A/B tests, CRM integrations, open tracking, and attachments.
- Remove generated logs and local artifacts from the product worktree or add appropriate ignore rules without deleting user-owned artifacts unexpectedly.
- Make local setup reproducible with one frontend command, one API command, and one worker command.
- Add a short architecture decision record covering the Next.js frontend, FastAPI API, PostgreSQL, worker, Gmail API, and Sheets API.
- Turn the roadmap into issues, each sized to one day or less when possible.

### Exit gate

- A new developer can start the stack from the README.
- Product limits and non-goals are written down.
- Every Phase 1 task exists as a trackable issue with an owner and acceptance criteria.

## Phase 1 — Correctness and test foundation (Week 1)

**Outcome:** campaign behavior can change without risking accidental sends or silent regressions.

### Backend work

- Introduce Alembic migrations; stop relying on `create_all` in production.
- Create test factories for users, campaigns, steps, and recipients.
- Add API tests for authentication boundaries, ownership isolation, campaign creation, pause/resume transitions, imports, templates, and validation errors.
- Mock Google APIs and test initial send, threaded follow-up, reply stop, transient retry, permanent failure, and Sheet updates.
- Define and enforce a campaign state machine. Invalid transitions must return a clear conflict response.
- Make recipient and campaign counters derived or transactionally consistent; test that retries cannot double-count sends.
- Validate scheduled times, supported source values, duplicate emails, empty rows, malformed CSV encodings, and unknown merge variables.
- Add structured error types so provider failures are safe for users but useful in logs.

### Frontend work

- Add a component/unit test setup and test the wizard's validation and payload creation.
- Add browser-level tests for login fallback, manual campaign creation, CSV import, Sheet import, test send, schedule, pause, and resume using mocked APIs.
- Add route-level loading, error, and not-found experiences.
- Break very large client pages into focused components before their behavior expands.
- Add accessible labels, keyboard flow, focus management, and actionable error messages.

### Exit gate

- Critical worker paths and API authorization paths have automated coverage.
- Duplicate worker execution cannot produce a duplicate email in tests.
- CI runs lint, backend tests, frontend tests, and a production build on every pull request.

## Phase 2 — Safe campaign creation and sending controls (Week 2)

**Outcome:** a user cannot accidentally schedule a bad or excessive campaign.

### Tasks

- Add a true `DRAFT` state and save-as-draft behavior.
- Allow editing and deleting drafts; allow canceling a scheduled campaign before its first send.
- Add a final approval screen showing exact recipient count, excluded rows, subject/body, all follow-ups, schedule timezone, interval, and daily cap.
- Require an explicit confirmation checkbox before scheduling.
- Add per-recipient previews and navigation, not only the first-row preview.
- Detect missing merge values and let the user fix, exclude, or intentionally accept affected recipients.
- Add column-mapping UI for both CSV and Sheets, with automatic suggestions and a validation summary.
- Validate and normalize email addresses; show duplicates, invalid rows, and the downloadable rejected-row report.
- Add user timezone, allowed sending days/hours, and a safe default daily message limit.
- Add a global account pause and an emergency stop that prevents new claims immediately.
- Add a suppression list and block previously unsubscribed addresses at campaign creation and again immediately before send.

### Exit gate

- Scheduling always requires a reviewed immutable snapshot of recipients and content.
- Invalid, duplicate, suppressed, and incomplete recipients are visible before approval.
- A user can stop all pending sends without database access.

## Phase 3 — Durable worker and provider resilience (Weeks 3-4)

**Outcome:** sends are durable, idempotent, rate-aware, and recoverable under restarts and provider errors.

### Data model

- Replace implicit `next_send_at` scanning with a durable send-job/outbox model.
- Give each intended message an idempotency key based on campaign, recipient, and sequence step.
- Add lease owner, lease expiry, attempt count, next retry time, provider response, and terminal error fields.
- Record an append-only event for every state transition and operator action.

### Worker behavior

- Claim jobs atomically with PostgreSQL row locking (`FOR UPDATE SKIP LOCKED`) before running more than one worker.
- Commit the claim before making the Gmail request and reconcile uncertain outcomes after crashes.
- Classify errors into retryable, rate-limited, auth-revoked, invalid-recipient, quota-exhausted, and terminal categories.
- Use exponential backoff with jitter and honor provider retry guidance.
- Enforce account-level concurrency and daily caps across all campaigns.
- Re-check campaign pause, suppression, and replies immediately before each send.
- Make reply synchronization incremental and resumable; avoid repeatedly scanning every recent thread.
- Handle expired/revoked Google access and refresh tokens with a visible reconnect state.
- Remove long sleeps from a claimed worker path; schedule future work rather than holding the process.

### Operations

- Add a dead-letter view and safe retry/skip controls.
- Create reconciliation commands for stuck jobs, counter repair, and reply re-sync.
- Test worker termination immediately before and after Gmail submission.

### Exit gate

- Restarting or running multiple workers does not duplicate sends in the test environment.
- Rate limits and transient failures recover automatically.
- Every send has a traceable intent, attempt history, provider result, and final state.

## Phase 4 — Security, privacy, and compliance (Week 5)

**Outcome:** the private beta has defensible handling of accounts, tokens, recipient data, and outreach preferences.

### Tasks

- Fail startup in production when encryption, session, cron, or OAuth secrets are missing or use development defaults.
- Store secrets in the hosting platform's secret manager and define a rotation procedure.
- Review session cookies (`Secure`, `HttpOnly`, `SameSite`, domain, lifetime) for the final deployment topology.
- Add CSRF protection to cookie-authenticated state-changing routes and validate origins.
- Add request-size limits, upload-type checks, CSV formula-injection protections for exports, and rate limits.
- Minimize Google scopes where possible and document why each remaining scope is needed.
- Encrypt sensitive fields, restrict database access, and avoid recipient/message content in application logs.
- Add account deletion, Google disconnect/token revocation, and recipient-data deletion/export flows.
- Implement unsubscribe links and a durable suppression list if the use case includes commercial outreach.
- Draft privacy policy, terms, acceptable-use policy, retention policy, and abuse-report process with qualified legal review for target markets.
- Prepare Google OAuth verification materials: verified domain, homepage, privacy policy, scope justification, demo video, and test account.
- Run dependency, secret, and static security scans in CI.

### Exit gate

- A documented threat model has no unresolved critical/high findings.
- Token revocation and account deletion are tested.
- Suppressed recipients cannot be sent to through any normal or retry path.
- Legal/compliance requirements for the target audience and regions are signed off by a qualified reviewer.

## Phase 5 — Production infrastructure and observability (Week 6)

**Outcome:** a staging and production system can be deployed, monitored, backed up, and restored.

### Recommended topology

- Next.js frontend on a managed web platform
- FastAPI as a separately deployed API service
- Worker as a separately deployed long-running service
- Managed PostgreSQL with automated backups and point-in-time recovery
- Centralized logs, exception tracking, metrics, and alerting

### Tasks

- Create separate local, test, staging, and production configurations.
- Containerize or otherwise make API and worker deployments reproducible.
- Add readiness and liveness checks that cover database connectivity without exposing secrets.
- Set up CI/CD with migration-before-rollout handling and a rollback procedure.
- Emit structured logs with request, campaign, recipient, job, and provider correlation IDs; hash or redact personal data.
- Track queue depth, oldest due job, sends/replies/failures, retry rate, Gmail latency, auth failures, worker heartbeat, and quota utilization.
- Alert on a stopped worker, growing queue age, duplicate/idempotency conflict, elevated failure rate, database saturation, and OAuth failures.
- Configure automated database backups and perform a staging restore drill.
- Write runbooks for paused queues, Gmail outage/rate limiting, revoked tokens, bad deployment, stuck jobs, accidental campaign, and data deletion.

### Exit gate

- Staging is production-like and deploys automatically from the release branch.
- A backup has been restored successfully.
- A simulated worker failure alerts the operator and recovers without duplicate sends.

## Phase 6 — Internal pilot (Week 7)

**Outcome:** the full system is proven with real Gmail behavior and controlled recipients.

### Pilot protocol

1. Connect one test Google Workspace or Gmail account.
2. Import 3-5 addresses owned by the team through each supported source.
3. Test missing values, duplicate rows, non-ASCII content, long subjects, and timezone boundaries.
4. Send one initial message and two follow-ups with short test delays.
5. Reply before each possible step and verify later sends stop.
6. Pause and resume mid-campaign; restart the API and worker during processing.
7. Trigger a recoverable error and verify retry behavior; trigger a permanent error and verify operator visibility.
8. Verify Sheet statuses, unsubscribe/suppression behavior, account disconnect, and deletion.
9. Compare Gmail sent mail, database events, dashboard counters, and logs recipient by recipient.

### Exit gate

- Zero unexplained or duplicate messages across at least 10 controlled campaigns.
- Every discrepancy is fixed and covered by a regression test.
- The operational runbook is usable by someone other than the developer who wrote the feature.

## Phase 7 — Private beta (Week 8)

**Outcome:** 5-20 invited users can complete the core workflow with close monitoring and support.

### Tasks

- Add a guided onboarding checklist and Gmail connection health indicator.
- Add in-product explanations of sending limits, reply-stop behavior, and required recipient consent/compliance.
- Add lightweight product analytics for onboarding completion, campaign approval, first send, failures, and retention; do not capture email content.
- Add a feedback/report-problem path with correlation IDs.
- Invite users in cohorts: 2, then 5, then 10+, expanding only after reviewing metrics and support issues.
- Keep conservative hard limits and manually approve increases.
- Hold a daily beta review of failures, queue health, duplicate-send signals, user feedback, and quota usage.

### Private-beta success criteria

- At least 80% of invited users who connect Google successfully schedule a controlled first campaign.
- At least 99% of accepted send jobs reach a correct terminal state without manual database repair.
- Zero duplicate sends and zero sends to suppressed recipients.
- Provider/auth failures are visible to users and actionable by operators.
- No unresolved severity-1 security or data-loss incident.

## Phase 8 — Public launch readiness (Weeks 9-12 plus external review time)

**Outcome:** self-service acquisition can begin without relying on manual developer intervention.

### Tasks

- Complete Google OAuth restricted-scope verification and any required security assessment.
- Finish production legal pages, domain verification, support channels, status page, and incident communications.
- Load-test API and job claiming; capacity-test at two to three times expected launch traffic without sending real email.
- Test multi-account fairness so one large campaign cannot starve others.
- Add abuse detection and enforce acceptable-use and sending limits.
- Define pricing and billing only after beta usage establishes real cost drivers.
- Publish onboarding documentation, troubleshooting, data handling, and account deletion instructions.
- Run a launch-readiness review covering security, privacy, reliability, product, support, and rollback.

### Exit gate

- Google approval is complete for the intended audience.
- Capacity, security, restore, and incident drills pass.
- Support ownership and on-call response expectations are explicit.

## 4. Prioritized backlog

### P0 — Must be complete before any external user

- Database migrations
- Worker idempotency and atomic job claiming
- Campaign state machine and immutable send snapshot
- Automated API/worker/end-to-end tests
- Production secret validation and secure auth controls
- Suppression/unsubscribe enforcement appropriate to the use case
- Daily caps, quiet hours, emergency stop
- Structured logs, alerts, backups, restore drill
- OAuth verification plan and compliant privacy/legal materials

### P1 — Must be complete before public launch

- Draft/edit/cancel workflow
- Better CSV/Sheet column mapping and rejected-row report
- Per-recipient previews and missing-variable resolution
- Reconnect, dead-letter, and recovery UI
- Account export/deletion and Google disconnect
- Guided onboarding, product analytics, support flow
- Load, failover, and multi-account fairness testing

### P2 — Add after product-market evidence

- Team workspaces and roles
- Multiple sender accounts
- Attachments
- A/B tests
- CRM integrations
- Custom domains/tracking
- Billing and usage tiers
- AI-assisted copy

## 5. Execution system

### Weekly rhythm

- **Monday:** choose one release outcome, define acceptance tests, and cap work in progress.
- **Tuesday-Thursday:** implement in vertical slices that include migration, API, UI, tests, and telemetry.
- **Friday:** deploy to staging, run the release checklist, fix regressions, update documentation, and review metrics.
- Do not begin the next phase while a current exit gate is failing.

### Ticket template

Every issue should contain:

- User or operator problem
- In-scope and out-of-scope behavior
- Data-model/API/UI changes
- Security and privacy considerations
- Acceptance criteria
- Automated test cases
- Telemetry and alert changes
- Rollout and rollback plan

### Definition of done

A task is done only when:

- Acceptance criteria pass locally and in CI.
- Error, empty, loading, permission, and retry states are handled.
- Relevant events/metrics are emitted without leaking personal data.
- Migrations are forward-safe and rollback behavior is understood.
- User-facing and operational documentation is updated.
- The change has been exercised in staging.

### Branch and release discipline

- Use short-lived branches and small pull requests.
- Require green lint, tests, type checking, build, migration checks, and security scans.
- Promote the same built artifact from staging to production.
- Use feature flags for risky behavior changes.
- Tag releases and maintain a concise changelog.

## 6. Product and reliability metrics

### Product funnel

- OAuth connection success rate
- Import completion rate by source
- Validation failure and rejected-row rate
- Draft-to-approved campaign conversion
- Time to first controlled send
- Weekly active senders and repeat-campaign rate

### Delivery correctness

- Accepted, sent, replied, suppressed, skipped, retrying, and failed jobs
- Duplicate-send count (target: zero)
- Send-to-terminal-state latency
- Queue age and retry rate
- Reply-detection latency
- Sheet synchronization failure rate
- OAuth reconnect rate

### Safety and support

- Unsubscribe/suppression violations (target: zero)
- Emergency-stop time
- Abuse reports
- Security and privacy incidents
- Support tickets per active sender and median resolution time

## 7. Key risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Duplicate sends after crash or concurrent workers | Severe trust damage | Durable outbox, idempotency keys, atomic leases, reconciliation tests |
| Gmail quota/rate limiting | Delayed or failed campaigns | Account caps, backoff, fair scheduling, visible queue state |
| Reply not detected | Unwanted follow-ups | Pre-send reply check, incremental sync, reconciliation, user stop controls |
| OAuth verification delay | Public launch blocked | Start verification preparation in Week 1; keep beta explicitly limited |
| Revoked refresh token | Campaign silently stalls | Classify auth errors, pause account, notify user, reconnect workflow |
| Sensitive recipient/content exposure | Legal and trust harm | Data minimization, encryption, redacted logs, retention/deletion controls |
| Non-compliant outreach | Account suspension or legal exposure | Suppression/unsubscribe, caps, acceptable-use policy, qualified legal review |
| Scope creep | Launch delay | Enforce v1 non-goals and phase exit gates |

## 8. Immediate next 10 actions

Execute these in order:

1. Confirm the v1 target user, recipient limit, daily cap, quiet hours, supported regions, and whether messages are commercial.
2. Create issues for all Phase 1 items and label them by backend, frontend, worker, security, and operations.
3. Add CI for Ruff, pytest, frontend tests/type checks, and `next build`.
4. Add Alembic and create the baseline database migration.
5. Write the campaign state machine and its API tests.
6. Mock Gmail/Sheets and cover duplicate prevention, reply stop, retry, and synchronization paths.
7. Design the durable send-job/outbox schema and idempotency rules before changing worker code.
8. Implement draft, approval snapshot, cancel, emergency stop, and account caps.
9. Establish staging with managed PostgreSQL, centralized errors/logs, metrics, and backups.
10. Run the internal pilot protocol and expand to private beta only after every exit gate passes.

The critical path is **tests and migrations → safe campaign approval → idempotent worker → security/compliance → production operations → internal pilot → private beta → OAuth-approved public launch**.
