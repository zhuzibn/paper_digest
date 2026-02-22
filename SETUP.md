# Paper Digest Setup Guide

This guide covers manual setup and automated scheduling for Paper Digest.

## Prerequisites

- **Python 3.10 or higher**
- macOS, Linux, or Windows

## Virtual Environment Setup

### macOS / Linux

```bash
# Navigate to project directory
cd paper_digest

# Create virtual environment
python3 -m venv venv

# Activate (run each time before manually running)
source venv/bin/activate
```

### Windows

```powershell
# Navigate to project directory
cd paper_digest

# Create virtual environment
python -m venv venv

# Activate (run each time before manually running)
venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure Environment Variables

1. Copy the example environment file:

   ```bash
   # macOS / Linux
   cp .env.example .env

   # Windows
   copy .env.example .env
   ```

2. Edit `.env` and fill in your SMTP settings:

   ```env
   SMTP_HOST=smtp.example.com
   SMTP_PORT=587
   SMTP_USER=your.email@example.com
   SMTP_PASSWORD=your_smtp_password
   EMAIL_FROM=your.email@example.com
   EMAIL_TO=recipient@example.com
   ```

3. Adjust other settings as needed (keywords, URLs).

### RSS Configuration

The following environment variables control RSS feed behavior:

```env
# APS Physical Review Letters
APS_PRL_RSS_URL=https://feeds.aps.org/rss/recent/prl.xml
APS_PRL_SECTION_FILTER=Condensed Matter and Materials

# Nature
NATURE_JOURNAL_RSS_URL=https://www.nature.com/nature/current_issue/rss
NATURE_JOURNAL_CATEGORY_ALLOWLIST=

# General
RSS_MAX_ENTRIES=200
```

- `APS_PRL_RSS_URL`: RSS feed URL for APS journals (default: `https://feeds.aps.org/rss/recent/prl.xml`)
- `APS_PRL_SECTION_FILTER`: Filter papers by section (default: `Condensed Matter and Materials`)
- `NATURE_JOURNAL_RSS_URL`: RSS feed URL for Nature (default: `https://www.nature.com/nature/current_issue/rss`)
- `NATURE_JOURNAL_CATEGORY_ALLOWLIST`: Comma-separated list to filter Nature content types. Empty (default) disables filtering.
- `RSS_MAX_ENTRIES`: Maximum number of entries to fetch per feed (default: `200`)

> **Note:** Nature journal RSS may include mixed content types (research articles, news, comments). Use `NATURE_JOURNAL_CATEGORY_ALLOWLIST` to narrow to specific types (e.g., `research,letter`).

### Gmail App Password Note

If using Gmail, enable 2-factor authentication, then generate an **App Password**:
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Search "App Passwords" → Create new
4. Use the 16-character app password in `SMTP_PASSWORD`

## Manual Run

```bash
python3 run.py
```

The state file `state/seen_papers.json` is created automatically on first run.

---

## Automated Scheduling

### macOS / Linux (Cron)

1. Open crontab editor:

   ```bash
   crontab -e
   ```

2. Add an entry. Example runs daily at 8 AM:

   ```
   0 8 * * * /full/path/to/paper_digest/venv/bin/python3 /full/path/to/paper_digest/run.py >> /full/path/to/paper_digest/cron.log 2>&1
   ```

   Replace `/full/path/to/paper_digest` with your actual path.

   The log redirection (`>> ... 2>&1`) captures both stdout and stderr.

3. Verify the cron service is running:

   ```bash
   # macOS
   launchctl list | grep cron

   # Linux
   systemctl status cron
   ```

### Windows Task Scheduler

1. Open **Task Scheduler** (search in Start menu).

2. Create Basic Task:
   - Name: `PaperDigest`
   - Trigger: Daily (or your preferred schedule)

3. Configure Action:
   - **Program/script**: `C:\path\to\paper_digest\venv\Scripts\python.exe`
   - **Add arguments**: `C:\path\to\paper_digest\run.py`
   - **Start in**: `C:\path\to\paper_digest`

   Replace paths with your actual locations.

4. Finish and enable the task.

---

## Notes

- The state file (`state/seen_papers.json`) tracks processed papers and is created automatically on first run. Do not delete it unless you want to reset the paper history.
- Test your setup manually first with `python3 run.py` before relying on cron/scheduled execution.
