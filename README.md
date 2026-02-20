# Paper Digest

A Python tool for automatically fetching and digesting research papers from arXiv and Nature Communications, with email notifications for papers matching your research keywords.

## Features

- 📄 **Multi-source fetching**: Retrieves papers from arXiv and Nature Communications
- 🔍 **Keyword filtering**: Filters papers based on customizable research keywords
- 📧 **Email notifications**: Sends digest emails with relevant papers
- 💾 **State tracking**: Maintains history of seen papers to avoid duplicates
- ⏰ **Automated scheduling**: Supports cron (Linux/macOS) and Task Scheduler (Windows)
- 🧪 **Tested**: Includes comprehensive unit and integration tests

## Installation

### Prerequisites

- Python 3.10 or higher
- SMTP email account (for sending notifications)

### Setup

1. **Clone the repository** (or navigate to the project directory)

2. **Create a virtual environment**:

   ```bash
   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:

   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env with your settings
   nano .env  # or your preferred editor
   ```

   Required settings in `.env`:

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
   NATURE_URL=https://www.nature.com/subjects/physical-sciences/ncomms

   # Keywords (comma-separated)
   KEYWORDS=spintronics,spin-orbit torque,antiferromagnet
   ```

   **Note for Gmail users**: Use an App Password instead of your regular password. Enable 2-factor authentication and generate an App Password at [Google Account Security](https://myaccount.google.com/security).

## Usage

### Manual Execution

```bash
python run.py
```

The tool will:
1. Fetch papers from configured sources
2. Filter by your keywords
3. Check against previously seen papers
4. Send an email with new matching papers
5. Update the state file

### Automated Scheduling

#### Linux/macOS (Cron)

1. Edit your crontab:

   ```bash
   crontab -e
   ```

2. Add a daily entry (example runs at 8 AM):

   ```
   0 8 * * * /path/to/paper_digest/venv/bin/python /path/to/paper_digest/run.py >> /path/to/paper_digest/cron.log 2>&1
   ```

3. Verify cron is running:

   ```bash
   # macOS
   launchctl list | grep cron

   # Linux
   systemctl status cron
   ```

#### Windows (Task Scheduler)

1. Open **Task Scheduler** from the Start menu
2. Create a **Basic Task** named "PaperDigest"
3. Set trigger to **Daily** (or your preferred schedule)
4. Configure action:
   - **Program/script**: `C:\path\to\paper_digest\venv\Scripts\python.exe`
   - **Add arguments**: `C:\path\to\paper_digest\run.py`
   - **Start in**: `C:\path\to\paper_digest`
5. Finish and enable the task

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
│   │   └── nature.py      # Nature Communications fetcher
│   ├── emailer.py         # Email notifications
│   └── runner.py          # Main orchestration logic
├── tests/                 # Test suite
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_storage.py
│   ├── test_emailer.py
│   ├── test_fetchers/
│   │   └── ...
│   └── test_integration.py
├── state/                 # State data (auto-created)
│   └── seen_papers.json   # Track processed papers
├── run.py                 # Entry point
├── requirements.txt        # Python dependencies
├── SETUP.md              # Detailed setup guide
└── README.md             # This file
```

## Development

### Running Tests

```bash
pytest
```

### Project Layout

- **`fetchers/`**: Source-specific paper fetching logic
- **`models.py`**: Data structures for papers
- **`storage.py`**: JSON-based state persistence
- **`emailer.py`**: SMTP email composition and sending
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
- **Nature Communications**: Default is physical sciences. Modify as needed.

### State Management

The state file (`state/seen_papers.json`) automatically tracks processed papers:
- Created on first run
- Updated after each execution
- Prevents duplicate notifications
- **Do not delete** unless you want to reset paper history

## Contributing

Contributions are welcome! Areas for improvement:

- Additional paper sources (APS, etc.)
- Customizable email templates
- Web interface for paper management
- Advanced filtering options

## License

This project is provided as-is for research purposes.

## Support

For detailed setup instructions, see [SETUP.md](SETUP.md).

---

**Version**: 0.1.0
**Python**: 3.10+
