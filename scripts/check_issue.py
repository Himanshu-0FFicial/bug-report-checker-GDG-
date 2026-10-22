import argparse
import os
import re
import subprocess
import sys
import requests

def check_issue_text(text):
    checks = {
        "Steps to reproduce": r"(steps to reproduce|repro steps|how to reproduce|steps:)",
        "Expected behavior": r"(expected behavior|expected|what should happen)",
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

def draft_comment_template(missing_items):
    if not missing_items:
        return "Thanks for the detailed report! Everything looks good to go for triage."
    
    prompts = {
        "Clear title": "A more descriptive title",
        "Steps to reproduce": "The exact steps you took",
        "Expected behavior": "What you expected to happen",
        "Actual behavior": "What actually happened",
        "Environment/version": "Your OS and library versions",
        "Logs/stack trace": "Any error messages, logs, or stack traces",
        "Code block": "A minimal reproducible example",
        "Regression info": "Whether this worked in a previous version"
    }
    
    draft = "Thanks for reporting this! To help us reproduce and fix it, could you share:\n"
    for i, item in enumerate(missing_items, 1):
        draft += f" {i}. {prompts.get(item, item)}\n"
    draft += "Once we have these, we can look into it."
    return draft

def draft_comment_with_gemma(missing_items, text):
    if not missing_items:
        return "Thanks for the detailed report! Everything looks good to go for triage."
    
    print("Drafting custom comment with local Gemma...")
    prompt = (
        "You are a friendly open-source maintainer. "
        "A user submitted a bug report, but it is missing the following details:\n"
        f"{', '.join(missing_items)}.\n\n"
        "Write a short, polite GitHub comment (under 4 sentences) thanking them and asking ONLY for these missing items. "
        "Do not invent any other requests."
    )

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4:e4b",
                "prompt": prompt,
                "stream": False
            }
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            return draft_comment_template(missing_items)
    except requests.exceptions.ConnectionError:
        return draft_comment_template(missing_items)

def post_comment_to_github(url, comment_text):
    """Posts comment via GitHub CLI (gh) or fallback to REST API using GITHUB_TOKEN."""
    print("Posting comment to GitHub...")
    
    # Try GitHub CLI first
    try:
        result = subprocess.run(
            ["gh", "issue", "comment", url, "--body", comment_text],
            capture_output=True, text=True, check=True
        )
        print("Success: Comment posted via GitHub CLI.")
        return
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # Fallback to REST API using token
    match = re.search(r"github\.com/([^/]+)/([^/]+)/issues/(\d+)", url)
    if not match:
        print("Error: Invalid GitHub URL for posting.")
        sys.exit(1)
        
    owner, repo, issue_number = match.groups()
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    
    if not token:
        print("Error: To post comments, either log into `gh` CLI or set the GITHUB_TOKEN environment variable.")
        sys.exit(1)
        
    api_url = "https://" + f"api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    response = requests.post(api_url, headers=headers, json={"body": comment_text})
    if response.status_code == 201:
        print("Success: Comment posted via GitHub API.")
    else:
        print(f"Error posting comment: GitHub returned status {response.status_code}")

def main():
    parser = argparse.ArgumentParser(description="Check bug report quality.")
    parser.add_argument("input", help="Path to text file OR a GitHub issue URL")
    parser.add_argument("--llm", action="store_true", help="Use local Gemma (via Ollama) to draft the comment")
    parser.add_argument("--post", action="store_true", help="Post the drafted comment to GitHub")
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
    
    comment = draft_comment_with_gemma(missing, text) if args.llm else draft_comment_template(missing)

    print("--- Drafted Comment ---")
    print(comment)
    print("-----------------------")

    if args.post:
        if not args.input.startswith("http"):
            print("Error: Cannot post a comment for a local text file. Please provide a GitHub URL.")
            sys.exit(1)
        post_comment_to_github(args.input, comment)

if __name__ == "__main__":
    main()