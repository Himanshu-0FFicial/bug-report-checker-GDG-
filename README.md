# Bug Report Quality Checker 🐞

An Agent Skill and Python utility that automatically evaluates GitHub bug reports against a standard maintainer quality checklist. It identifies missing information and drafts a polite, targeted follow-up comment to streamline issue triage.

## The Problem
Maintainers waste countless hours on back-and-forth communication due to incomplete bug reports (e.g., missing reproduction steps, environment details, or expected behavior). Issues often go stale because reporters do not know what specific information is required to investigate the bug.

## The Solution
This tool automates the initial triage process by:
* Fetching a GitHub issue directly via URL (or reading raw text).
* Evaluating the content and generating a completeness score out of 8 based on a predefined checklist.
* Drafting a tailored, ready-to-post response comment that asks *only* for the missing items.
* Providing a `SKILL.md` specification so compatible AI Agents can execute this workflow autonomously.

## 1. Clone the repository
```bash
git clone [https://github.com/YOUR-USERNAME/bug-report-checker.git](https://github.com/YOUR-USERNAME/bug-report-checker.git)
cd bug-report-checker

