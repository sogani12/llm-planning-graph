from __future__ import annotations
import json
import os
import re
import time
from pathlib import Path
import httpx

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GH_HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_TOKEN:
    GH_HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    print("GitHub token found — using authenticated requests (5000 req/hr).")
else:
    print("No GITHUB_TOKEN set — using unauthenticated requests (60 req/hr). Capping at 5 repos.")
ALL_GITHUB_REPOS = [
    "astral-sh/uv",          # Python packaging redesign, lots of 'we decided' rationale
    "tokio-rs/tokio",        # async runtime with architecture RFCs
    "gleam-lang/gleam",      # language design heavily documented in issues
    "ghostty-org/ghostty",   # terminal emulator with public design threads
    "BurntSushi/ripgrep",    # design rationale documented in issues
    "denoland/deno",         # lots of design tradeoff discussions
    "rust-lang/rfcs",        # RFCs = nearly pure Objective/Requirement/Decision content
    "microsoft/typescript",  # design decisions in issues
]

GITHUB_REPOS = ALL_GITHUB_REPOS if GITHUB_TOKEN else ALL_GITHUB_REPOS[:5]
POSTMORTEM_REPO = "danluu/post-mortems"

SEARCH_KEYWORDS = "design OR architecture OR rfc OR proposal OR decision OR tradeoff"

def gh_get(client, url: str):
    while True:
        r = client.get(url, headers=GH_HEADERS, params=params, timeout=30)
        if r.status_code == 403 and "rate" in r.text.lower():
            reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 61))
            wait = max(5, reset - int(time.time()) + 1)
            print(f"    Rate limited — waiting {wait}s...")
            time.sleep(wait)
            continue
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return r.json()

def clean_markdown(text):
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`\n]+`", " ", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"^\s*[-*+>]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|[^\n]+\|", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def fetch_github_issues(client, repo):
    """Fetch design-related issues via title keyword search + top comments."""
    dest = RAW_DIR / "github" / repo.replace("/", "_")
    dest.mkdir(parents=True, exist_ok=True)
    per_page = 20 if GITHUB_TOKEN else 10
    saved_ids = set()
    count = 0
    try:
        results = gh_get(
            client,
            "https://api.github.com/search/issues",
            q=f"repo:{repo} is:issue in:title {SEARCH_KEYWORDS}",
            sort="interactions",
            order="desc",
            per_page=per_page,
        )
    except (httpx.HTTPStatusError, httpx.RequestError):
        print(f"  {repo}: 0 issues saved")
        return 0
    issues = results.get("items", []) if isinstance(results, dict) else []
    for issue in issues:
        iid = issue.get("number")
        if iid in saved_ids:
            continue
        saved_ids.add(iid)
        body = issue.get("body") or ""
        if len(body.strip()) < 80:
            continue
        text = f"# {issue['title']}\n\n{body}"
        if issue.get("comments", 0) > 0:
            try:
                comments = gh_get(
                    client,
                    f"https://api.github.com/repos/{repo}/issues/{iid}/comments",
                    per_page=5,
                )
                for c in (comments or [])[:5]:
                    cbody = c.get("body") or ""
                    if len(cbody.strip()) > 80:
                        text += "\n\n---\n\n" + cbody
            except (httpx.HTTPStatusError, httpx.RequestError):
                pass
        out = dest / f"issue_{iid}.txt"
        out.write_text(clean_markdown(text))
        count += 1
    print(f"  {repo}: {count} issues saved")
    return count

def fetch_readme_and_adrs(client, repo):
    """Fetch README + any ADR/RFC/DECISION files in the repo root."""
    dest = RAW_DIR / "github" / repo.replace("/", "_")
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    try:
        readme_data = gh_get(client, f"https://api.github.com/repos/{repo}/readme")
        if isinstance(readme_data, dict):
            import base64
            content = base64.b64decode(readme_data.get("content", "")).decode("utf-8", errors="ignore")
            if len(content) > 200:
                (dest / "README.txt").write_text(clean_markdown(content))
                count += 1
    except (httpx.HTTPStatusError, httpx.RequestError):
        pass
    try:
        contents = gh_get(client, f"https://api.github.com/repos/{repo}/contents/")
        if isinstance(contents, list):
            design_pattern = re.compile(r"(ADR|RFC|DECISION|DESIGN|ARCHITECTURE)", re.IGNORECASE)
            for item in contents:
                if item.get("type") == "file" and design_pattern.search(item["name"]):
                    try:
                        r = client.get(item["download_url"], timeout=20)
                        text = clean_markdown(r.text)
                        if len(text) > 200:
                            safe_name = Path(re.sub(r"[^\w.-]", "_", item["name"])).with_suffix(".txt").name
                            (dest / safe_name).write_text(text)
                            count += 1
                    except (httpx.HTTPStatusError, httpx.RequestError):
                        pass
    except (httpx.HTTPStatusError, httpx.RequestError):
        pass
    return count

def fetch_postmortems(client):
    dest = RAW_DIR / "postmortems"
    dest.mkdir(parents=True, exist_ok=True)
    try:
        import base64
        readme_data = gh_get(client, f"https://api.github.com/repos/{POSTMORTEM_REPO}/readme")
        if not isinstance(readme_data, dict):
            print("  post-mortems: unexpected response format")
            return 0
        content = base64.b64decode(readme_data.get("content", "")).decode("utf-8", errors="ignore")
        text = clean_markdown(content)
        if len(text) > 150:
            (dest / "postmortems_list.txt").write_text(text)
            print("  post-mortems: 1 file saved")
            return 1
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        print(f"  post-mortems: failed — {e}")
    return 0

def fetch_stackoverflow(client):
    """Fetch [software-design] questions + top answers from Stack Overflow API."""
    dest = RAW_DIR / "stackoverflow"
    dest.mkdir(parents=True, exist_ok=True)
    try:
        r = client.get(
            "https://api.stackexchange.com/2.3/questions",
            params={
                "tagged": "software-design",
                "site": "stackoverflow",
                "filter": "withbody",
                "sort": "votes",
                "pagesize": 30,
                "order": "desc",
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        print(f"  stackoverflow: failed — {e}")
        return 0
    questions = {
        q["question_id"]: {"title": q["title"], "body": q.get("body", "")}
        for q in data.get("items", [])
        if len(clean_markdown(q.get("body", ""))) >= 80
    }
    if not questions:
        print("  stackoverflow: 0 questions saved")
        return 0
    answers_by_qid = {}
    try:
        ids = ";".join(str(qid) for qid in questions)
        r = client.get(
            f"https://api.stackexchange.com/2.3/questions/{ids}/answers",
            params={
                "site": "stackoverflow",
                "filter": "withbody",
                "sort": "votes",
                "order": "desc",
                "pagesize": 3 * len(questions),
            },
            timeout=30,
        )
        r.raise_for_status()
        for a in r.json().get("items", []):
            qid = a.get("question_id")
            body = clean_markdown(a.get("body", ""))
            if qid in questions and len(body) >= 80:
                answers_by_qid.setdefault(qid, []).append(body)
    except (httpx.HTTPStatusError, httpx.RequestError):
        pass
    count = 0
    for qid, q in questions.items():
        text = f"{q['title']}\n\n{clean_markdown(q['body'])}"
        for answer in answers_by_qid.get(qid, [])[:3]:
            text += f"\n\n---\n\n{answer}"
        (dest / f"q_{qid}.txt").write_text(text)
        count += 1
    print(f"  stackoverflow: {count} questions saved (with answers)")
    return count

def main():
    total = 0
    with httpx.Client() as client:
        print(f"\nFetching GitHub issues ({len(GITHUB_REPOS)} repos)...")
        for repo in GITHUB_REPOS:
            total += fetch_github_issues(client, repo)
            total += fetch_readme_and_adrs(client, repo)
        print("\nFetching post-mortems (danluu/post-mortems)...")
        total += fetch_postmortems(client)
        print("\nFetching Stack Overflow questions...")
        total += fetch_stackoverflow(client)
    print(f"\n{'='*50}")
    print(f"Total documents saved: {total}")
    print(f"Location: {RAW_DIR}")

if __name__ == "__main__":
    main()
