# Paper Digest

A Python tool for automatically fetching and digesting research papers from multiple sources (arXiv, Nature Communications, APS Physical Review Letters, Nature journal), with email notifications for papers matching your research keywords.

## Features

- 📄 **Multi-source fetching**: Retrieves papers from arXiv, Nature Communications, APS PRL, and Nature journal
- 🔍 **Keyword filtering**: Filters papers based on customizable research keywords
- 📧 **Email notifications**: Sends digest emails with source statistics and relevant papers
- 💾 **State tracking**: Maintains history of seen papers to avoid duplicates
- ⏰ **Automated scheduling**: Supports cron (Linux/macOS) and Task Scheduler (Windows)
- 🧪 **Tested**: Includes comprehensive unit and integration tests
- 📊 **Source statistics**: Email digest shows how many papers were found from each source

## Prerequisites

- Python 3.10 or higher
- macOS, Linux, or Windows
- SMTP email account (for sending notifications)

## Installation

### 1. Create Virtual Environment

**macOS / Linux:**

```bash
cd paper_digest
python3 -m venv venv
source venv/bin/activate  # Run this each time before manually running
```

**Windows:**

```powershell
cd paper_digest
python -m venv venv
venv\Scripts\activate  # Run this each time before manually running
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file:

```bash
# macOS / Linux
cp .env.example .env

# Windows
copy .env.example .env
```

Edit `.env` and fill in your settings:

```env
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your.email@gmail.com
EMAIL_TO=recipient@example.com

# Paper Sources
ARXIV_URL=https://arxiv.org/list/cond-mat/new
NATURE_URL=https://www.nature.com/ncomms.rss

# RSS Sources
APS_PRL_RSS_URL=https://feeds.aps.org/rss/recent/prl.xml
APS_PRL_SECTION_FILTER=Condensed Matter and Materials
NATURE_JOURNAL_RSS_URL=https://www.nature.com/nature/current_issue/rss
NATURE_JOURNAL_CATEGORY_ALLOWLIST=
RSS_MAX_ENTRIES=200

# Keywords (comma-separated)
KEYWORDS=spintronics,spin-orbit torque,antiferromagnet

# User Agent
USER_AGENT=Mozilla/5.0 (compatible; PaperDigest/1.0)
```

### 4. Gmail App Password (if using Gmail)

If using Gmail, you must use an App Password instead of your regular password:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Search for **App Passwords** and create a new one
4. Use the 16-character app password in `SMTP_PASSWORD`

### RSS Configuration

The following environment variables control RSS feed behavior:

- `APS_PRL_RSS_URL`: RSS feed URL for APS journals (default: `https://feeds.aps.org/rss/recent/prl.xml`)
- `APS_PRL_SECTION_FILTER`: Filter papers by section (default: `Condensed Matter and Materials`)
- `NATURE_JOURNAL_RSS_URL`: RSS feed URL for Nature (default: `https://www.nature.com/nature/current_issue/rss`)
- `NATURE_JOURNAL_CATEGORY_ALLOWLIST`: Comma-separated list to filter Nature content types. Empty (default) disables filtering.
- `RSS_MAX_ENTRIES`: Maximum number of entries to fetch per feed (default: `200`)

> **Note:** Nature journal RSS may include mixed content types (research articles, news, comments). Use `NATURE_JOURNAL_CATEGORY_ALLOWLIST` to narrow to specific types (e.g., `research,letter`).

## Usage

### Manual Execution

```bash
python run.py
```

The tool will:
1. Fetch papers from all configured sources (arXiv, Nature Communications, APS PRL, Nature journal)
2. Filter by your keywords
3. Check against previously seen papers
4. Send an email with new matching papers, including source statistics
5. Update the state file

### Automated Scheduling

#### Linux/macOS (Cron)

1. Open crontab editor:

   ```bash
   crontab -e
   ```

2. Add an entry. Example runs daily at 8 AM:

   ```
   0 8 * * * /full/path/to/paper_digest/venv/bin/python3 /full/path/to/paper_digest/run.py >> /full/path/to/paper_digest/cron.log 2>&1
   ```

   Replace `/full/path/to/paper_digest` with your actual path. The log redirection captures both stdout and stderr.

3. Verify the cron service is running:

   ```bash
   # macOS
   launchctl list | grep cron

   # Linux
   systemctl status cron
   ```

#### Windows Task Scheduler

1. Open **Task Scheduler** from the Start menu

2. Create a **Basic Task**:
   - Name: `PaperDigest`
   - Trigger: Daily (or your preferred schedule)

3. Configure Action:
   - **Program/script**: `C:\path\to\paper_digest\venv\Scripts\python.exe`
   - **Add arguments**: `C:\path\to\paper_digest\run.py`
   - **Start in**: `C:\path\to\paper_digest`

   Replace paths with your actual locations.

4. Finish and enable the task.

## Project Structure

```
paper_digest/
├── paper_digest/           # Main package
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration management
│   ├── models.py          # Data models
│   ├── storage.py         # State persistence
│   ├── fetchers/          # Paper fetchers
│   │   ├── __init__.py
│   │   ├── arxiv.py       # arXiv fetcher
│   │   ├── nature.py      # Nature Communications fetcher
│   │   ├── aps_prl_rss.py # APS PRL RSS fetcher
│   │   ├── nature_journal_rss.py # Nature journal RSS fetcher
│   │   ├── rss.py         # RSS base fetcher
│   │   └── common.py      # Common utilities
│   ├── emailer.py         # Email notifications
│   └── runner.py          # Main orchestration logic
├── tests/                 # Test suite
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_storage.py
│   ├── test_emailer.py
│   ├── test_runner.py
│   ├── test_integration.py
│   └── test_fetchers/
│       └── ...
├── state/                 # State data (auto-created)
│   └── seen_papers.json   # Track processed papers
├── run.py                 # Entry point
├── requirements.txt       # Python dependencies
├── .env.example          # Environment configuration template
└── README.md             # This file
```

## Development

### Running Tests

```bash
pytest
```

### Project Layout

- **`fetchers/`**: Source-specific paper fetching logic (arXiv, Nature Communications, APS PRL, Nature journal)
- **`models.py`**: Data structures for papers
- **`storage.py`**: JSON-based state persistence
- **`emailer.py`**: SMTP email composition and sending with source statistics
- **`runner.py`**: Main workflow orchestration
- **`tests/`**: Unit and integration tests

## Configuration

### Keywords

Specify research keywords in `.env` as a comma-separated list:

```env
KEYWORDS=keyword1,keyword2,keyword3
```

Matching is case-insensitive and searches paper titles and abstracts.

### Paper Sources

Configure source URLs in `.env`:

- **arXiv**: Default is condensed matter (`cond-mat/new`). Change to your preferred category.
- **Nature Communications**: Default is the RSS feed (`https://www.nature.com/ncomms.rss`). Modify as needed.
- **APS PRL**: RSS feed with optional section filtering.
- **Nature Journal**: RSS feed with optional category filtering.

### State Management

The state file (`state/seen_papers.json`) automatically tracks processed papers:
- Created on first run
- Updated after each execution
- Prevents duplicate notifications
- **Do not delete** unless you want to reset the paper history

### Email Notifications

Each digest email includes:
- List of all checked sources
- Total number of related papers found
- Count of papers from each source
- Full details of matching papers

## Troubleshooting

### Common Issues

1. **No email received**: Check your SMTP credentials and ensure your email provider allows SMTP access.
2. **No papers found**: Verify your keywords are correct and the source URLs are accessible.
3. **Cron not running**: On macOS, check that cron is enabled: `launchctl list | grep cron`. On Linux: `systemctl status cron`.
4. **RSS feeds not updating**: Check that the RSS URLs are correct and accessible. Some feeds may have rate limits.

### Logs

When using cron or Task Scheduler, redirect output to a log file for troubleshooting:
```bash
python run.py >> /path/to/paper_digest/cron.log 2>&1
```

## Contributing

Contributions are welcome! Areas for improvement:

- Additional paper sources (other journals, preprint servers)
- Customizable email templates
- Web interface for paper management
- Advanced filtering options
- Push notifications (mobile, desktop)

## License

This project is provided as-is for research purposes.

---

**Version**: 0.1.0
**Python**: 3.10+
