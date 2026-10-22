# Bug Report Quality Checker

An Agent Skill and Python script that checks a GitHub bug report for missing information and drafts a polite follow-up comment asking only for what's missing. It can optionally use a local Gemma 4 model (via Ollama) to write the comment, and can post it to GitHub after you confirm.

Built at the Hacktoberfest Hack Day (Pune x Google Developer Group on Campus, Vishwakarma University).

## The problem

Maintainers get reports like "it doesn't work" with no steps, version, or logs. Triage turns into back-and-forth, and issues go stale because reporters don't know what to include.

## What it does

1. Takes a GitHub issue URL or a local text file
2. Scores the report against an 8-item checklist
3. Lists what is present and what is missing
4. Suggests a label: `needs-info` or `ready-to-triage`
5. Drafts a comment asking only for the missing items (template, or written by Gemma with `--llm`)
6. Optionally posts that comment with `--post`

### The checklist

| Item | Detected by (keywords, case-insensitive) |
|------|------------------------------------------|
| Clear title | First line has more than 3 words and isn't a generic title like "bug" or "help" |
| Steps to reproduce | "steps to reproduce", "repro steps", "how to reproduce", "steps:" |
| Expected behavior | "expected behavior", "expected", "what should happen" |
| Actual behavior | "actual behavior", "current behavior", "what happened", "actual" |
| Environment/version | "environment", "os", "version", Windows / Mac / Linux / Ubuntu |
| Logs/stack trace | "logs", "stack trace", "traceback", "error message", "exception" |
| Code block | a code fence, "minimal reproducible example", CodePen, JSFiddle |
| Regression info | "regression", "worked in", "used to work", "previous version" |

The checks are plain regular expressions, so the default mode needs no AI model.

## Example

```
$ python scripts/check_issue.py samples/bad_issue.txt

Score: 2/8
Present:  Clear title, Environment/version
Missing:  Steps to reproduce, Expected behavior, Actual behavior, Logs/stack trace, Code block, Regression info
Suggested label: needs-info

--- Drafted Comment ---
Thanks for reporting this! To help us reproduce and fix it, could you share:
 1. The exact steps you took
 2. What you expected to happen
 3. What actually happened
 4. Any error messages, logs, or stack traces
 5. A minimal reproducible example
 6. Whether this worked in a previous version
Once we have these, we can look into it.
-----------------------
```

## Installation

Requires Python 3.8+.

```bash
git clone https://github.com/Himanshu-0FFicial/bug-report-checker-GDG-.git
cd bug-report-checker-GDG-
pip install requests
```

Optional extras:
- **Gemma drafting:** install [Ollama](https://ollama.com), then run `ollama pull gemma4:e4b`
- **Posting comments:** the [GitHub CLI](https://cli.github.com) (`gh auth login`), or a `GITHUB_TOKEN` environment variable

## Usage

Run these from the repository root.

```bash
# Check a local text file
python scripts/check_issue.py samples/bad_issue.txt

# Check a public GitHub issue
python scripts/check_issue.py https://github.com/OWNER/REPO/issues/123

# Let local Gemma write the comment
python scripts/check_issue.py https://github.com/OWNER/REPO/issues/123 --llm

# Post the drafted comment to the issue
python scripts/check_issue.py https://github.com/OWNER/REPO/issues/123 --post
```

| Flag | What it does |
|------|--------------|
| `--llm` | Draft the comment with Gemma through Ollama instead of the fixed template |
| `--post` | Post the drafted comment to the GitHub issue (URL input only) |

### Gemma mode details

- Calls the local Ollama API at `http://localhost:11434` with the model `gemma4:e4b`
- Only the comment is written by the model. The checklist score always comes from the rules
- If Ollama isn't running or returns an error, the script falls back to the template comment
- The issue text stays on your machine

### Posting details

- `--post` tries the `gh` CLI first, then falls back to the GitHub REST API using `GITHUB_TOKEN` or `GH_TOKEN`
- **The script posts immediately when `--post` is passed.** It does not ask for confirmation itself. Confirmation happens in the Agent Skill workflow below
- Posting needs write access to the repository's issues

## Using it as an Agent Skill

`SKILL.md` teaches a compatible AI agent a two-phase workflow:

1. **Check and draft (no posting).** The agent runs the script without `--post` (with `--llm` if you ask for Gemma), shows the score, present and missing items, label, and drafted comment, then asks: "Would you like me to post this comment to GitHub?"
2. **Post only on explicit yes.** If you confirm, the agent runs the script again with `--post` and reports the result.

Heads up: with `--llm`, phase 2 runs the script again, and the model may word the comment differently from the version you approved. For exact control, use the template mode when posting.

## Project structure

```
.
├── SKILL.md                 # Agent Skill instructions (two-phase workflow)
├── README.md
├── requirements.txt
├── scripts/
│   └── check_issue.py       # fetch, check, draft, optionally post
└── samples/
    └── bad_issue.txt        # example of an incomplete report
```

## Limitations

- Keyword matching can be wrong in both directions. A short keyword like "os" can match inside ordinary words (so "Environment/version" may be marked present by mistake), and unusual wording can be missed
- A keyword doesn't prove the information is there. "Version:" with no value still counts
- Only issue URLs (`.../issues/<number>`) are supported, not pull requests
- Fetching is unauthenticated, so GitHub's rate limit (about 60 requests per hour) applies, and private repositories don't work
- `--llm` has no timeout, so a slow model load can make it appear stuck
- English-language reports only

## Future work

- Word-boundary regexes and content-aware checks
- Gemma double-checking the checklist, not just writing the comment
- A `--model` flag and a hosted-API backend
- Confirmation prompt built into `--post`
- Batch mode for all open issues in a repo
- A GitHub Action that runs when an issue is opened
- More sample issues and automated tests

## License

MIT. See [LICENSE](LICENSE).