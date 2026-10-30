# Paper Digest Environment

This file is the dedicated environment specification for Paper Digest.
`requirements.txt` is the authoritative Python dependency source,
`.env.example` is the authoritative environment-variable schema, and
`README.md` plus `AGENTS.md` define setup and validation commands.

## Required runtime

- Python 3.10 or newer.
- A project-local virtual environment at `venv`.
- Every dependency and version constraint in `requirements.txt`.
- A private `.env` derived from `.env.example` with your research `KEYWORDS`.

Source URLs, RSS overrides, filters, maximum-entry settings, and the user agent
have application defaults or optional values documented in `.env.example`.
No special hardware or GPU is required.

Operational runs require outbound HTTP access to paper sources. Readiness checks
do not access the network and therefore cannot validate feed availability.
Cron or Windows Task Scheduler is an optional deployment integration, not a
manual-runtime prerequisite.

## Setup

From the project root on Linux/WSL:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your keywords and source preferences. Do not commit or print
the file. Legacy `SMTP_*` and `EMAIL_*` settings are ignored.

## Read-only verification

```bash
venv/bin/python --version
venv/bin/python -m pip check
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -c 'import bs4, dateutil, dotenv, feedparser, lxml, paper_digest, pytest, requests'
RSS_FEEDS= PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider
```

The test command clears `RSS_FEEDS` only for that process so private `.env`
feed overrides do not interfere with configuration-test expectations.

`python run.py` is not a readiness validator: it accesses external services,
fetches paper metadata, and updates the state file.
`python run.py review`, `python run.py status`, and `python run.py decide ID
accept` (or `skip`) use local metadata only and need no network access.
They share the digest's state lock; use one process/computer at a time.

`venv/bin/python run.py review --web` starts a loopback HTTP server and opens
the pending-paper review window. It requires a browser and permission to bind
`127.0.0.1`, but no external network access or additional dependencies. Use
`--no-browser` to open the printed URL manually (including in Windows from WSL).
Keep the server running during review. **Save and finish review** saves explicit
choices, emits `paper_review_completed`, and stops the server with exit 0.
Ctrl+C cancels waiting with exit 130 and no completion event. The active
`paper-tracker` agent waits for successful completion and refreshes the summary;
the standalone server does not run an exporter. Review HTTP tests also need loopback
socket access and use disposable ledgers, not the real tracking file.
