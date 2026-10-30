# Changelog

## 2026-10-29

- Add **Save and finish review**: after confirming saved decisions, the browser
  closes when allowed and the server reports this session's choices and exits.
  The waiting paper-tracker skill can verify choices and refresh its Markdown
  summary without another chat message; pending items and failed-save retries
  keep their existing behavior. Cancellation emits no success signal.

## 2026-10-28

- Replace email delivery with persistent local paper review and explicit
  accept/skip decisions. Preserve legacy seen-link exclusions and migrate
  version 2 ledgers on write without losing paper IDs or decision history;
  SMTP settings are no longer required. Back up state before upgrading.
- Deduplicate DOI, arXiv, and normalized URL identities, retain pending papers
  after they leave feeds, and report independent source outcomes. Failed or
  partial checks return a nonzero exit status while retaining valid candidates
  and the previous successful-check timestamp.
- Add `review --web` to review all pending papers in a local browser window
  with Leave pending, Accept, and Skip controls and an explicit Save decisions
  button. Reuse existing locking and decision history, preserve unselected
  papers, reject conflicting stale decisions, and report partial saves.
- The window uses bundled assets and Python's standard library. No additional
  dependencies or paper searches are required; `--no-browser` prints the local
  URL for manual or agent-assisted opening.
