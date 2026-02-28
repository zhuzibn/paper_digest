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
