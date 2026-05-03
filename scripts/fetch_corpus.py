"""
Fetch raw corpus for EDA.

Saves documents to data/raw/{tier}/{id}.txt.
Tiers: github/, postmortems/, stackoverflow/

Usage:
    python scripts/fetch_corpus.py

Optional: set GITHUB_TOKEN env var for 5000 req/hr (vs 60 unauthenticated).
Without a token, collection is capped at 5 repos to stay within rate limits.
"""

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

# Planning-heavy repos with explicit design discussions
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

# Cap at 5 without a token to stay within rate limits
GITHUB_REPOS = ALL_GITHUB_REPOS if GITHUB_TOKEN else ALL_GITHUB_REPOS[:5]

# danluu/post-mortems: curated collection of public post-mortems in markdown
POSTMORTEM_REPO = "danluu/post-mortems"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gh_get(client: httpx.Client, url: str, **params) -> dict | list:
    """GET from GitHub API with rate-limit backoff."""
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


def clean_markdown(text: str) -> str:
    """Strip markdown syntax, preserve prose content."""
    text = re.sub(r"```[\s\S]*?```", " ", text)                   # fenced code
    text = re.sub(r"`[^`\n]+`", " ", text)                        # inline code
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)                  # images
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)          # links → text
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)    # headers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)                # bold
    text = re.sub(r"\*([^*]+)\*", r"\1", text)                    # italic
    text = re.sub(r"^\s*[-*+>]\s+", "", text, flags=re.MULTILINE) # bullets/blockquotes
    text = re.sub(r"\|[^\n]+\|", " ", text)                       # tables
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

SEARCH_KEYWORDS = "design OR architecture OR rfc OR proposal OR decision OR tradeoff"


def fetch_github_issues(client: httpx.Client, repo: str) -> int:
    """Fetch design-related issues via title keyword search + top comments."""
    dest = RAW_DIR / "github" / repo.replace("/", "_")
    dest.mkdir(parents=True, exist_ok=True)

    per_page = 20 if GITHUB_TOKEN else 10
    saved_ids: set[int] = set()
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

        # Fetch top 5 comments for richer context
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


def fetch_readme_and_adrs(client: httpx.Client, repo: str) -> int:
    """Fetch README + any ADR/RFC/DECISION files in the repo root."""
    dest = RAW_DIR / "github" / repo.replace("/", "_")
    dest.mkdir(parents=True, exist_ok=True)
    count = 0

    # README
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

    # Root directory — look for design docs
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


def fetch_postmortems(client: httpx.Client) -> int:
    """Fetch danluu/post-mortems curated list (README is the content)."""
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


def fetch_stackoverflow(client: httpx.Client) -> int:
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

    # Fetch top 3 answers per question in one batched request
    answers_by_qid: dict[int, list[str]] = {}
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
        pass  # answers are bonus — proceed without them

    count = 0
    for qid, q in questions.items():
        text = f"{q['title']}\n\n{clean_markdown(q['body'])}"
        for answer in answers_by_qid.get(qid, [])[:3]:
            text += f"\n\n---\n\n{answer}"
        (dest / f"q_{qid}.txt").write_text(text)
        count += 1

    print(f"  stackoverflow: {count} questions saved (with answers)")
    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
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
