# Contributing Guide

## Project Workflow

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

