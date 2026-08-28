#!/usr/bin/env python3
"""
Static Data Covenant harvester (RAR CONSTITUTION.md Article XXIV).

Runs in CI (or by hand, as the "CI harvester") and paginates
api.github.com/users/kody-w/repos, writing a trimmed, committed snapshot at
repos-snapshot.json. index.html reads that committed file instead of calling
api.github.com from the visitor's browser.

Only the fields index.html actually uses are kept (name, description,
html_url, full_name) — same key names as the GitHub API, so page parsing is
unchanged; the payload is just much smaller than the raw API response.

Usage:
    python3 scripts/harvest-repos.py

Env:
    GITHUB_TOKEN   optional; if set, used for higher API rate limits.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(ROOT, "repos-snapshot.json")
KEEP_FIELDS = ("name", "full_name", "description", "html_url")


def fetch_all_repos(token=None):
    repos = []
    page = 1
    while page <= 10:  # safety cap; kody-w currently has ~5 pages at per_page=100
        url = f"https://api.github.com/users/kody-w/repos?per_page=100&page={page}&sort=full_name"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                batch = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"HTTP error on page {page}: {e.code}", file=sys.stderr)
            raise
        if not isinstance(batch, list):
            raise RuntimeError(f"unexpected response on page {page}: {batch}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def main():
    token = os.environ.get("GITHUB_TOKEN")
    repos = fetch_all_repos(token)
    trimmed = [{k: r.get(k) for k in KEEP_FIELDS} for r in repos]
    snapshot = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "https://api.github.com/users/kody-w/repos (harvested by CI, not the browser)",
        "repos": trimmed,
    }
    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)
        f.write("\n")
    print(f"wrote {SNAPSHOT_PATH} ({len(trimmed)} repos)")


if __name__ == "__main__":
    main()
