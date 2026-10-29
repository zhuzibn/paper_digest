# Paper Digest

A Python tool for automatically fetching and digesting research papers from multiple sources (arXiv, Nature Communications, APS Physical Review Letters, Nature journal), with local review and accept/skip tracking for papers matching your research keywords.

## Features

- 📄 **Multi-source fetching**: Retrieves papers from arXiv, Nature Communications, APS PRL, and Nature journal
- 🔍 **Keyword filtering**: Filters papers based on customizable research keywords
- 💾 **State tracking**: Deduplicates DOI/arXiv identifiers and URLs, preserving metadata for later review
- ✅ **Paper selections**: Records explicit accept/skip decisions for each paper
- ⏰ **Automated scheduling**: Supports cron (Linux/macOS) and Task Scheduler (Windows)
- 🧪 **Tested**: Includes comprehensive unit and integration tests
- 📊 **Source statistics**: Fetch logs show per-source matches; local status shows outcomes

## Prerequisites

- Python 3.10 or higher
- macOS, Linux, or Windows

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
# Paper Sources
ARXIV_URL=https://arxiv.org/list/cond-mat/new
NATURE_URL=https://www.nature.com/ncomms.rss

# RSS Sources - Built-in sources only (preferred)
RSS_FEEDS=nature=https://www.nature.com/ncomms.rss;aps-prl=https://feeds.aps.org/rss/recent/prl.xml;nature-journal=https://www.nature.com/nature/current_issue/rss
APS_PRL_SECTION_FILTER=Condensed Matter and Materials
NATURE_JOURNAL_CATEGORY_ALLOWLIST=
RSS_MAX_ENTRIES=200

# Legacy fallback variables (deprecated, use RSS_FEEDS above)
# APS_PRL_RSS_URL=https://feeds.aps.org/rss/recent/prl.xml
# NATURE_JOURNAL_RSS_URL=https://www.nature.com/nature/current_issue/rss

# Keywords (comma-separated)
KEYWORDS=spintronics,spin-orbit torque,antiferromagnet

# User Agent
USER_AGENT=Mozilla/5.0 (compatible; PaperDigest/1.0)
```

### RSS Configuration

The application supports additional RSS feeds through the `RSS_FEEDS` environment variable.

**Format:** `RSS_FEEDS` uses a semicolon-separated format: `id=url;id=url;id=url` (newline-separated is also acceptable).

**Semantics:**
- **Unset (line commented or removed):** No additional RSS feeds are fetched beyond the built-in sources (arXiv, Nature Communications, APS PRL, Nature journal)
- **Empty string (`RSS_FEEDS=`):** Same as unset - only built-in sources are used
- **Set with values:** Uses the specified feeds as overrides for built-in sources and adds additional feeds
- **Built-in sources are always active:** Omitting a built-in ID from `RSS_FEEDS` does NOT disable that source
- **Precedence:** RSS_FEEDS value for a built-in ID > legacy env var (e.g., `APS_PRL_RSS_URL`) > default

**Built-in override IDs supported in `RSS_FEEDS`:**
- `nature` - Nature Communications (default: `https://www.nature.com/ncomms.rss`)
- `aps-prl` - APS Physical Review Letters (default: `https://feeds.aps.org/rss/recent/prl.xml`)
- `nature-journal` - Nature journal (default: `https://www.nature.com/nature/current_issue/rss`)

**Example with built-in sources only:**
```env
RSS_FEEDS=nature=https://www.nature.com/ncomms.rss;aps-prl=https://feeds.aps.org/rss/recent/prl.xml;nature-journal=https://www.nature.com/nature/current_issue/rss
```

**Example with full feed list (built-ins + additional):**
```env
# nature -> Nature Communications
# aps-prl -> APS Physical Review Letters
# nature-journal -> Nature journal
# aps-prb -> APS Physical Review B
# aps-prapplied -> APS Physical Review Applied
# aps-prx -> APS Physical Review X
# aps-rmp -> APS Reviews of Modern Physics
# science -> Science
# science-advances -> Science Advances
# nano-letters -> Nano Letters
# acs-nano -> ACS Nano
# aip-apl -> AIP Applied Physics Letters
RSS_FEEDS=nature=https://www.nature.com/ncomms.rss;aps-prl=https://feeds.aps.org/rss/recent/prl.xml;nature-journal=https://www.nature.com/nature/current_issue/rss;aps-prb=https://feeds.aps.org/rss/recent/prb.xml;aps-prapplied=https://feeds.aps.org/rss/recent/prapplied.xml;aps-prx=https://feeds.aps.org/rss/recent/prx.xml;aps-rmp=https://feeds.aps.org/rss/recent/rmp.xml;science=https://www.science.org/action/showFeed?type=axatoc&feed=rss&jc=science;science-advances=https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv;nano-letters=https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=nalefd;acs-nano=https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=ancac3;aip-apl=https://pubs.aip.org/rss/site_1000017/1000011.xml
```

## Usage

### Manual Execution

```bash
python run.py
```

The tool will:
1. Fetch papers from all configured sources (arXiv, Nature Communications, APS PRL, Nature journal)
2. Filter by your keywords
3. Deduplicate discoveries against stored papers and legacy history
4. Save matching metadata and each source's fetch outcome for local review

Exit status is `0` when all source checks and state writes succeed, and `1` when
any source fails, coverage is partial, or state persistence fails. Healthy sources
still contribute papers when another source fails. Run `python run.py review`
to read pending papers and `python run.py status` to inspect source outcomes.

### Review and Accept/Skip

These commands use local metadata only and do not fetch sources:

```bash
python run.py review                       # Undecided papers
python run.py review --web                 # Interactive browser window
python run.py review --web --no-browser    # Print the local URL for manual opening
python run.py review --status accepted
python run.py review --status skipped
python run.py review --status all
python run.py status                       # Source outcomes and selection counts
python run.py decide PAPER_ID accept
python run.py decide PAPER_ID skip
```

Replace `PAPER_ID` with the exact `p-...` Review ID shown in the review listing. IDs remain stable after discovery, even when later metadata adds
a DOI. Every paper starts `pending`; leaving it unanswered keeps it pending.
Only an explicit `decide` command or **Save decisions** in the review window
changes a selection. A later explicit decision can correct an
earlier one, with timestamped history retained. Accept/skip records your selection
without triggering downloads. No PDFs, Markdown archives, or article bodies are saved.

### Browser Review Window

Run `venv/bin/python run.py review --web` on WSL/Linux (or
`venv\Scripts\python.exe run.py review --web` on Windows). This opens all currently
pending papers in one scrollable browser window, with titles, source links,
authors, dates, matched keywords, and exact review IDs. No sources are fetched.
The window uses Python's standard library and bundled HTML/CSS/JavaScript;
no additional packages, external fonts, or hosted service are needed.

Choose **Leave pending**, **Accept**, or **Skip** beside each paper, then click
**Save decisions**. Unselected papers stay pending, and choosing Leave pending
clears an unsaved choice. Draft choices live only in that tab: closing or
reloading it discards them. Saved rows show their confirmed status and are
disabled; use `decide` for later corrections. The page reports partial saves
if a write fails, and retries do not duplicate already matching decisions.

Keep the terminal process running while using the window; press **Ctrl+C** to
stop it. The server listens only on `127.0.0.1`, uses a randomly assigned port
and a session token, and prints the complete URL. If WSL cannot open your browser,
paste that URL into your Windows browser, or use `--no-browser` when launching
through an agent. This URL is usable only while that server is running.

The session includes the pending papers present at startup and keeps its row
numbers stable after saves. Restart it to include later discoveries. A changed
decision in another tab or CLI is never silently overwritten: reload to inspect
the current state. Each read/save briefly acquires the existing state lock;
the lock is not held while you read papers. Missing or empty state reports that
there are no pending papers, without creating a ledger.

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
│   ├── identity.py        # DOI, arXiv and URL identity matching
│   ├── storage.py         # State persistence
│   ├── review_web.py      # Local browser review server
│   ├── web/               # Bundled review HTML, CSS and JavaScript
│   ├── fetchers/          # Paper fetchers
│   │   ├── __init__.py
│   │   ├── arxiv.py       # arXiv fetcher
│   │   ├── nature.py      # Nature Communications fetcher
│   │   ├── aps_prl_rss.py # APS PRL RSS fetcher
│   │   ├── nature_journal_rss.py # Nature journal RSS fetcher
│   │   ├── rss.py         # RSS base fetcher
│   │   ├── rss_feeds.py   # Additional RSS feeds, checked independently
│   │   └── common.py      # Common utilities
│   └── runner.py          # Main orchestration logic
├── tests/                 # Test suite
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_storage.py
│   ├── test_runner.py
│   ├── test_integration.py
│   └── test_fetchers/
│       └── ...
├── state/                 # State data (auto-created)
│   └── seen_papers.json   # Metadata, selections and source checks
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

The version 3 ledger at `state/seen_papers.json` stores discovered papers,
source checks, and explicit review decisions. Metadata remains available after
papers disappear from their source feeds, without a review display limit.
Fetching or rediscovering a paper never changes its accept/skip decision.

Existing `{"seen_links": [...]}` files remain legacy exclusions. Their URLs are
normalized for matching; they do not become invented decisions or new review
records. Version 2 ledgers migrate on the next write, preserving all paper IDs,
metadata, aliases, decisions, and source history while removing obsolete delivery
fields. Previously emailed and unsent papers alike remain available for review.

Back up state before upgrading. After migration, use the updated program: older
versions cannot preserve the new ledger fields. Corrupt or unsupported state
stops the operation and is preserved for recovery instead of resetting history.
Email notification support and SMTP configuration have been removed; existing
`SMTP_*` and `EMAIL_*` variables are ignored and are no longer required.

Matching uses explicit DOI metadata, DOI resolver and recognized APS/Nature
article URLs, version-independent arXiv identifiers, and normalized URL aliases.
URL normalization removes fragments and common tracking parameters while
retaining identifying query parameters. Titles alone do not establish identity.
A preprint and journal article merge only when supplied metadata connects them;
missing identifiers can still leave duplicates. Conflicting existing identities
stop the run for reconciliation instead of overwriting decisions.

Writes use atomic replacement, and a local `.lock` file prevents concurrent
digest/review commands. Run only one computer at a time and let OneDrive finish
synchronizing before switching. The local lock is not a distributed lock. If a
crash leaves a lock, inspect its PID and verify no process is active before
manually removing it. Do not delete the ledger unless you intend to reset history.

### Fetch Coverage and Dates

Each source, including each additional RSS feed, has its own last attempt,
last successful check, outcome, error, and matching-paper count. Successful
timestamps use the run's start time. Failed or partial checks retain the previous
successful timestamp; changing a source URL starts that endpoint's history anew.
Malformed feeds, dropped invalid entries, `RSS_MAX_ENTRIES` truncation, and
detected arXiv pagination are reported as incomplete. Valid parsed candidates
from partial results can still be saved for review.

The current sources expose snapshots, not historical date-window searches. Every
run rechecks the available snapshot, including old, same-day, delayed, and
undated entries; the successful-check timestamp is diagnostic, **not a publication
date cutoff**. This deliberately preserves overlap without dropping late items.
No historical backfill or pagination is performed. Feed retention, index delays,
entry limits, and time between runs can leave gaps; a successful check does not
claim exhaustive publication-date coverage. Increase `RSS_MAX_ENTRIES` if that
cap causes partial checks (`RSS_MAX_ENTRIES` must be positive).

## Troubleshooting

### Common Issues

1. **No papers found**: Verify your keywords are correct and the source URLs are accessible.
2. **Cron not running**: On macOS, check that cron is enabled: `launchctl list | grep cron`. On Linux: `systemctl status cron`.
3. **RSS feeds not updating**: Check that the RSS URLs are correct and accessible. Some feeds may have rate limits.

### Logs

When using cron or Task Scheduler, redirect output to a log file for troubleshooting:
```bash
python run.py >> /path/to/paper_digest/cron.log 2>&1
```

## Contributing

Contributions are welcome! Areas for improvement:

- Additional paper sources (other journals, preprint servers)
- Web interface for paper management
- Advanced filtering options

## License

This project is provided as-is for research purposes.

---

**Version**: 0.1.0
**Python**: 3.10+
