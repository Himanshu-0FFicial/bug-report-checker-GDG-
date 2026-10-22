---
name: "Bug Report Quality Checker"
description: "Evaluates GitHub issues or pasted bug reports against a quality checklist to determine what information is missing, drafts a follow-up comment, and optionally posts it upon human confirmation."
triggers:
  - "triage this issue"
  - "is this bug report complete?"
  - "check this issue"
  - "check bug report"
  - User pastes a GitHub issue URL contextually asking for review
---

# Instructions

You are an AI assistant helping open-source maintainers triage bug reports. When a user triggers this skill, execute the following two-phase workflow.

## Phase 1: Check and Draft (No Posting)
Execute `check_issue.py` WITHOUT the `--post` flag first.

**Command:**
- Standard: `python scripts/check_issue.py <URL_OR_FILEPATH>`
- LLM mode (if Gemma requested): `python scripts/check_issue.py <URL_OR_FILEPATH> --llm`

Present the output clearly to the user:
- Completeness Score (e.g., 6/8)
- Present items
- Missing items
- Suggested label (e.g., `needs-info`)
- The drafted comment

**Ask Permission:**
Explicitly ask: *"Would you like me to post this comment to GitHub?"*

## Phase 2: Post Comment (Requires Explicit Permission)
Only if the user explicitly responds **YES** or confirms they want the comment posted:

Execute the script again with the `--post` flag:
- Standard: `python scripts/check_issue.py <URL> --post`
- LLM mode: `python scripts/check_issue.py <URL> --llm --post`

Report the posting result to the user.