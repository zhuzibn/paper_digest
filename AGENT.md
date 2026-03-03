# Project Guidelines & Documentation

All contributors (including AI Agents) must follow these protocols. All logs are maintained within this file under the relevant sections.

---

## Section 1: Source Code Changes (Changelog)

Every non-trivial modification must be appended to the bottom of this section using this template:

### [vX.X.X] | YYYY-MM-DD
- **Type:** (feat | fix | refactor | docs)
- **Description:** One-sentence summary.
- **Motivation:** Why was this change necessary?
- **Files Modified:** `path/to/file`
- **Test Strategy:** How was this verified?

---

## Section 2: Error & Solution Log

Every unique error encountered during development or deployment must be recorded here:

### [ERROR-ID] | Short Descriptive Title
- **Context:** Where/when did it happen?
- **Symptoms:** Error message or stack trace.
- **Root Cause:** Detailed explanation of the failure.
- **Resolution:** Step-by-step fix implemented.
- **Prevention:** How to avoid this in the future.

---

## Section 3: Workflow for Agents

1. **Analyze** the task or error.
2. **Execute** code changes.
3. **Verify** with tests.
4. **Append** documentation to Section 1 (for changes) or Section 2 (for errors) of **this file** before finalizing.

---

## Section 1: Source Code Changes

### [v0.1.0] | 2026-03-03
- **Type:** feat
- **Description:** Add `RSS_FEEDS` list config + generic RSS fetcher + dynamic email source stats
- **Motivation:** Track additional journals without per-feed env vars, allowing users to configure arbitrary RSS feeds in a single list
- **Files Modified:**
  - `paper_digest/config.py`
  - `paper_digest/fetchers/rss_feeds.py`
  - `paper_digest/runner.py`
  - `paper_digest/emailer.py`
  - `tests/test_fetchers/test_rss_feeds.py`
  - `tests/conftest.py`
  - `.env.example`
  - `README.md`
- **Test Strategy:** `pytest`

---

## Section 2: Error & Solution Log

### [ERR-001] | Pytest ModuleNotFoundError for paper_digest
- **Context:** Running `pytest` after creating new fetcher module during 2026-03-03 development session
- **Symptoms:** 
  ```
  ModuleNotFoundError: No module named 'paper_digest'
  ```
  Tests failed to import the main package when running from the project root.
- **Root Cause:** Python test runner could not locate the `paper_digest` package because the test directory lacked a `conftest.py` file to configure the Python path properly. Without this configuration, pytest's import resolution failed to find the sibling package.
- **Resolution:** Created `tests/conftest.py` with pytest configuration to add the project root to `sys.path`, enabling proper package resolution:
  ```python
  import sys
  from pathlib import Path
  
  # Add project root to path for imports
  root = Path(__file__).parent.parent
  sys.path.insert(0, str(root))
  ```
- **Prevention:** Always ensure `conftest.py` exists in the tests directory for projects using package imports. Consider using `pip install -e .` for development installs or configuring `PYTHONPATH` in the test environment.

---
