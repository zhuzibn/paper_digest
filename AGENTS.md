# AGENTS.md - Paper Digest Codebase Guidelines

## Overview
This document provides comprehensive guidelines for agentic coding agents working in the Paper Digest repository. It covers build/test commands, code style conventions, and development workflows.

## Project Structure
```
paper_digest/
├── paper_digest/           # Main application package
│   ├── __init__.py        # Package initialization  
│   ├── config.py          # Configuration management using dataclasses
│   ├── models.py          # Data models (Paper class with TypedDict)
│   ├── storage.py         # JSON-based state persistence
│   ├── fetchers/          # Paper source fetchers
│   │   ├── __init__.py
│   │   ├── arxiv.py       # arXiv fetcher implementation
│   │   ├── nature.py      # Nature Communications fetcher  
│   │   ├── aps_prl_rss.py # APS PRL RSS fetcher
│   │   ├── nature_journal_rss.py # Nature journal RSS fetcher
│   │   ├── rss.py         # Base RSS fetcher utilities
│   │   └── common.py      # Shared utilities (keyword matching, date parsing)
│   ├── emailer.py         # Email notification system with HTML/text multipart
│   └── runner.py          # Main orchestration logic
├── tests/                 # Comprehensive test suite
│   ├── test_config.py
│   ├── test_models.py  
│   ├── test_storage.py
│   ├── test_emailer.py
│   ├── test_runner.py
│   ├── test_integration.py
│   └── test_fetchers/     # Source-specific fetcher tests
│       ├── test_arxiv.py
│       ├── test_nature.py
│       ├── test_aps_prl_rss.py
│       ├── test_nature_journal_rss.py
│       ├── test_rss.py
│       └── test_common.py
├── state/                 # Runtime state directory (excluded from git)
│   └── seen_papers.json   # Tracks processed papers to prevent duplicates
├── run.py                 # Entry point script
├── requirements.txt       # Core dependencies
├── .env.example          # Environment configuration template
├── README.md             # Comprehensive documentation
└── CONTRIBUTING.md       # Change tracking and contribution guidelines
```

## Build & Test Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv                    # Linux/macOS
python -m venv venv                     # Windows

# Activate virtual environment  
source venv/bin/activate                # Linux/macOS  
venv\Scripts\activate                   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running Tests
The project uses **pytest** as the test runner with version 9.0.2+.

**Run all tests:**
```bash
pytest
```

**Run specific test file:**
```bash
pytest tests/test_emailer.py
```

**Run specific test function:**
```bash
pytest tests/test_emailer.py::test_send_digest_sends_multipart_email_with_expected_content
```

**Run tests matching keyword pattern:**
```bash
pytest -k "emailer"                     # Runs all tests with 'emailer' in name
pytest -k "test_send_digest"            # Runs tests matching this substring
pytest -k "not integration"             # Excludes integration tests
```

**Verbose output:**
```bash
pytest -v                               # Verbose mode
pytest -vv                              # Extra verbose mode
```

**Debugging tests:**
```bash
pytest --pdb                            # Start debugger on failures
pytest -s                               # Show print statements (disable output capture)
```

### Manual Execution
```bash
python run.py                           # Execute main application
```

### Cron/Task Scheduler Setup
For automated execution, use absolute paths:

**Linux/macOS Cron:**
```
0 8 * * * /full/path/to/paper_digest/venv/bin/python3 /full/path/to/paper_digest/run.py >> /full/path/to/paper_digest/cron.log 2>&1
```

**Windows Task Scheduler:**
- Program: `C:\path\to\paper_digest\venv\Scripts\python.exe`
- Arguments: `C:\path\to\paper_digest\run.py`
- Start in: `C:\path\to\paper_digest`

## Code Style Guidelines

### Python Version & Type Safety
- **Python 3.10+** required
- **Type annotations mandatory** for all function signatures and class attributes
- Use **TypedDict** for dictionary type definitions (see `models.py`)
- Use **dataclasses** for configuration and data models
- Enable **pyright** type checking (configured via inline comments in files)

### Imports Organization
Follow this exact import order:
1. **Standard library imports** (`import os`, `from pathlib import Path`)
2. **Third-party imports** (`from dotenv import load_dotenv`, `import requests`)
3. **Local application imports** (`from paper_digest.config import Config`)

**Import formatting:**
- One import per line
- Group imports with single blank line between groups
- Use explicit imports over wildcard imports
- Relative imports only within the same package

### Naming Conventions
- **Variables & functions**: `snake_case` (e.g., `fetch_papers`, `paper_list`)
- **Classes**: `PascalCase` (e.g., `ArxivFetcher`, `PaperStorage`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `BASE_DIR`, `STATE_FILE`)
- **Private methods**: `_private_method()` with leading underscore

### Formatting & Structure
- **Indentation**: 4 spaces (no tabs)
- **Line length**: Aim for <88 characters (black-compatible)
- **Blank lines**: 
  - Two blank lines between top-level functions/classes
  - Single blank line between methods in classes
  - Single blank line after import groups
- **String quotes**: Use double quotes consistently (`"string"`)

### Error Handling
- **Always use try/except blocks** for external operations (HTTP requests, file I/O)
- **Log exceptions** with `logger.exception()` for debugging
- **Return empty collections** instead of raising exceptions for non-critical failures
- **Use specific exception types** rather than bare `except:` clauses
- **Never suppress errors silently** without logging

### Docstrings & Comments
- **Functions require docstrings** describing purpose, parameters, and return values
- **Complex logic requires inline comments** explaining the "why"
- **Type annotations serve as documentation** - keep them accurate and complete
- **No unnecessary comments** that just repeat the code

### Testing Patterns
- **Test files mirror source structure** (`test_fetchers/` matches `fetchers/`)
- **Use helper functions** for test setup (`_config()`, `_paper()` patterns)
- **Mock external dependencies** using `unittest.mock.patch`
- **Assert both positive and negative cases** (empty inputs, error conditions)
- **Include regression tests** for bug fixes
- **Integration tests validate end-to-end workflow**

### Logging
- **Use module-level loggers**: `logger = logging.getLogger(__name__)`
- **Log at appropriate levels**: `info()` for normal operation, `warning()` for recoverable issues, `exception()` for errors
- **Include context in log messages** (URLs, identifiers, error details)

## Configuration Management
- **Environment variables** loaded via `python-dotenv` from `.env` file
- **Config class** uses dataclass with defaults and validation
- **Required vs optional fields**: Required fields have no defaults, optional fields use `field(default_factory=list)` or literal defaults
- **Validation in `from_env()`**: Parse and normalize environment variables, provide sensible defaults

## State Management
- **State directory**: `state/` excluded from git (in `.gitignore`)
- **JSON persistence**: Simple JSON file storage (`seen_papers.json`)
- **Thread safety**: Not required (single-threaded application)
- **Error handling**: Fail gracefully if state file is corrupted/malformed

## Dependencies
Required packages from `requirements.txt`:
- `requests>=2.31.0` - HTTP client
- `beautifulsoup4>=4.12.0` - HTML parsing  
- `lxml>=4.9.0` - XML/HTML parser backend
- `python-dotenv>=1.0.0` - Environment variable loading
- `python-dateutil>=2.8.0` - Date parsing utilities
- `feedparser>=6.0.0` - RSS/Atom feed parsing
- `pytest>=7.4.0` - Testing framework
- `pytest-mock>=3.12.0` - Mocking utilities

## Performance Considerations
- **HTTP timeouts**: Always specify reasonable timeouts (30 seconds typical)
- **Memory efficiency**: Process papers incrementally when possible
- **Rate limiting**: Respect source website terms of service
- **Caching**: Leverage built-in state tracking to avoid reprocessing

## Security Guidelines  
- **Environment variables**: Never hardcode credentials (SMTP passwords, API keys)
- **Input validation**: Sanitize all external inputs (URLs, user data)
- **HTTPS only**: Ensure all external requests use HTTPS
- **Dependency updates**: Keep dependencies current to address security vulnerabilities

## Troubleshooting Common Issues
1. **No email received**: Verify SMTP credentials and email provider settings
2. **No papers found**: Check keywords, source URLs, and network connectivity  
3. **Cron not running**: Verify absolute paths and cron service status
4. **RSS feed errors**: Confirm feed URLs are accessible and not rate-limited
5. **Test failures**: Ensure virtual environment is activated and dependencies installed

## Agent-Specific Instructions
When making changes as an agentic coding agent:
1. **Always run relevant tests** before claiming completion
2. **Follow existing patterns** exactly (import order, naming, error handling)
5. **Verify type safety** - ensure pyright/linting passes
6. **Test edge cases** - empty inputs, network failures, malformed data

# document errors and solutions

This document tracks all changes and resolutions to ensure project maintainability.

---

## Section 1: Source Code Changes

### 2026-02-28: Enhanced Email Notifications with Source Statistics

**Files Modified:**

- `paper_digest/emailer.py`
- `tests/test_emailer.py`

**Description:**
Added source count statistics to email notifications. The email body (both text and HTML formats) now displays:

- List of checked sources (arXiv, Nature Communications, PRL, Nature journal)
- Total number of related papers found
- Count of papers from each source

**Implementation Details:**

- Added `_source_counts()` method to count papers by source
- Updated `_build_text_body()` to include source statistics at the top
- Updated `_build_html_body()` to include formatted source statistics
- Added corresponding test assertions to verify new content in emails

**Why this change:**
Users need visibility into which sources are being checked and how many papers were found from each source to better understand the search coverage.

---

## Section 2: Error Logs

*No errors encountered yet.*

---

## Last Updated

2026-02-28


---

## Section 1: Source Code Changes

### 2026-02-28: Merge SETUP.md into README.md and update documentation

**Files Modified:**

- `README.md`
- `SETUP.md` (deleted)
- `CONTRIBUTING.md`

**Description:**
Merged detailed setup instructions from SETUP.md into the main README.md file and updated the documentation to reflect the current codebase state. Updated source information to include all four fetchers (arXiv, Nature Communications, APS PRL, Nature journal) and RSS configuration options.

**Implementation Details:**

- Consolidated all setup, installation, and configuration instructions into README.md
- Added detailed RSS configuration section with environment variable descriptions
- Updated features list to include source statistics
- Updated project structure to reflect actual file organization
- Added troubleshooting section
- Removed SETUP.md reference and deleted the file

**Why this change:**
Simplify documentation by maintaining a single, comprehensive README file instead of splitting content across multiple files. The README now serves as both overview and detailed setup guide.



---

## Section 1: Source Code Changes

### 2026-03-04: RSS_FEEDS Configuration with Built-in Override Support

**Files Modified:**

- `paper_digest/config.py`
- `.env.example`
- `README.md`
- `tests/test_config.py`

**Description:**
Enhanced RSS configuration to support built-in source overrides and additional feed configuration through the `RSS_FEEDS` environment variable.

**Implementation Details:**

- Added support for built-in override IDs in `RSS_FEEDS`: `nature`, `aps-prl`, `nature-journal`
- `rss_feeds` field populated by parsing `RSS_FEEDS` environment variable; built-in override IDs (`nature`, `aps-prl`, `nature-journal`) are excluded from the parsed list
- Built-in source precedence: `RSS_FEEDS` value > legacy env var (e.g., `APS_PRL_RSS_URL`) > default
- Updated `.env.example` with `RSS_FEEDS` examples and deprecated legacy variables
- Updated `README.md` RSS configuration section with built-in ID documentation
- Added tests in `test_config.py` covering:
  - `test_from_env_rss_feeds_overrides_builtin_urls` - verifies RSS_FEEDS values override built-in source URLs
  - `test_from_env_rss_feeds_excludes_builtin_ids_from_additional_feeds` - verifies built-in IDs excluded from rss_feeds list
  - `test_from_env_rss_feeds_invalid_builtin_override_falls_back_to_default` - verifies invalid URLs fall back to defaults



**Why this change:**
Provides flexible RSS feed configuration while maintaining built-in sources. Users can override default feed URLs or add additional feeds through a single environment variable.

**Prevention:**
Run tests to avoid regression: `pytest tests/test_config.py::test_from_env_rss_feeds_overrides_builtin_urls`, `pytest tests/test_config.py::test_from_env_rss_feeds_excludes_builtin_ids_from_additional_feeds`, `pytest tests/test_config.py::test_from_env_rss_feeds_invalid_builtin_override_falls_back_to_default`

---

## Last Updated

2026-03-04
