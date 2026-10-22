import argparse
import re
import sys
import requests

def check_issue_text(text):
    """
    Scans the issue text against a checklist of required information.
    """
    checks = {
        "Steps to reproduce": r"(steps to reproduce|repro steps|how to reproduce|steps:)",
        "Expected behavior": r"(expected behavior|expected|what should happen)",
        # Added "current behavior" to this regex
        "Actual behavior": r"(actual behavior|current behavior|what happened|actual|bug description)",
        "Environment/version": r"(environment|os|version|windows|mac|linux|ubuntu)",
        "Logs/stack trace": r"(logs|stack trace|traceback|error message|exception)",
        "Code block": r"(```|minimal reproducible example|mre|codepen|jsfiddle)",
        "Regression info": r"(regression|worked in|used to work|previous version)"
    }

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    title = lines[0] if lines else ""

    present = []
    missing = []

    bad_titles = ["bug", "help", "not working", "broken", "crash", "error"]
    if len(title.split()) > 3 and title.lower() not in bad_titles:
        present.append("Clear title")
    else:
        missing.append("Clear title")

    for item_name, pattern in checks.items():
        if re.search(pattern, text, re.IGNORECASE):
            present.append(item_name)
        else:
            missing.append(item_name)

    return present, missing

def get_issue_from_url(url):
    """
    Extracts owner, repo, and issue number from URL, then calls GitHub API.
    """
    match = re.search(r"github\.com/([^/]+)/([^/]+)/issues/(\d+)", url)
    if not match:
        print("Error: Invalid GitHub issue URL.")
        sys.exit(1)
        
    owner, repo, issue_number = match.groups()
    api_url = "https://" + f"api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    
    print(f"Fetching from GitHub: {owner}/{repo}#{issue_number}...\n")
    
    response = requests.get(api_url)
    
    if response.status_code != 200:
        print(f"Error fetching issue: GitHub returned status {response.status_code}")
        sys.exit(1)
        
    data = response.json()
    title = data.get("title", "")
    body = data.get("body", "") or ""
    
    return f"{title}\n\n{body}"

def draft_comment(missing_items):
    """
    Generates a polite follow-up comment asking for the missing items.
    """
    if not missing_items:
        return "Thanks for the detailed report! Everything looks good to go for triage."
    
    # Friendly translations for the checklist items
    prompts = {
        "Clear title": "A more descriptive title so we know exactly what this is about at a glance",
        "Steps to reproduce": "The exact steps you took before the issue occurred",
        "Expected behavior": "What you expected to happen",
        "Actual behavior": "What actually happened (or the current behavior)",
        "Environment/version": "Your OS and library versions",
        "Logs/stack trace": "Any error messages, logs, or stack traces",
        "Code block": "A minimal reproducible example or code snippet",
        "Regression info": "Whether this worked in a previous version"
    }
    
    draft = "Thanks for reporting this! To help us reproduce and fix it, could you share:\n"
    for i, item in enumerate(missing_items, 1):
        draft += f" {i}. {prompts.get(item, item)}\n"
    draft += "Once we have these, we can look into it."
    return draft

def main():
    parser = argparse.ArgumentParser(description="Check bug report quality.")
    parser.add_argument("input", help="Path to text file OR a GitHub issue URL")
    args = parser.parse_args()

    if args.input.startswith("http"):
        text = get_issue_from_url(args.input)
    else:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: Could not find file '{args.input}'")
            sys.exit(1)

    present, missing = check_issue_text(text)
    
    score = len(present)
    total = len(present) + len(missing)
    suggested_label = "needs-info" if missing else "ready-to-triage"

    print(f"Score: {score}/{total}")
    print(f"Present:  {', '.join(present) if present else 'None'}")
    print(f"Missing:  {', '.join(missing) if missing else 'None'}")
    print(f"Suggested label: {suggested_label}\n")
    
    print("--- Drafted Comment ---")
    print(draft_comment(missing))
    print("-----------------------")

if __name__ == "__main__":
    main()