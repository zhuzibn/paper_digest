# Paper Digest Environment

This file is the dedicated environment specification for Paper Digest.
`requirements.txt` is the authoritative Python dependency source,
`.env.example` is the authoritative environment-variable schema, and
`README.md` plus `AGENTS.md` define setup and validation commands.

## Required runtime

- Python 3.10 or newer.
- A project-local virtual environment at `venv`.
- Every dependency and version constraint in `requirements.txt`.
- A private `.env` derived from `.env.example` with non-placeholder values for
  `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`,
  `EMAIL_TO`, and `KEYWORDS`.

Source URLs, RSS overrides, filters, maximum-entry settings, and the user agent
have application defaults or optional values documented in `.env.example`.
No special hardware or GPU is required.

Operational runs require outbound HTTP access to paper sources and SMTP access
to the configured mail server. Readiness checks do not access the network and
therefore cannot validate feed availability, credentials, or email delivery.
Cron or Windows Task Scheduler is an optional deployment integration, not a
manual-runtime prerequisite.

## Setup

From the project root on Linux/WSL:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with real SMTP credentials and keywords. Do not commit or print
the file.

## Read-only verification

```bash
venv/bin/python --version
venv/bin/python -m pip check
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -c 'import bs4, dateutil, dotenv, feedparser, lxml, paper_digest, pytest, requests'
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider
```

`python run.py` is not a readiness validator: it accesses external services,
sends email when matches exist, and updates the state file.
