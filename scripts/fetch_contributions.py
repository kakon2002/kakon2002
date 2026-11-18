"""Fetch the public contribution calendar for a GitHub user and save it as JSON.

Usage: python scripts/fetch_contributions.py [username]
Writes data/contributions.json. Uses only the standard library.
"""
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "kakon2002"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"


def fetch(user):
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "readme-cards"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse(html):
    # <td ... data-date="2026-01-02" id="contribution-day-component-..." ...>
    cells = {}
    for tag in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", html):
        date = re.search(r'data-date="([\d-]+)"', tag)
        cid = re.search(r'id="([^"]+)"', tag)
        if date and cid:
            cells[cid.group(1)] = date.group(1)
    counts = {}
    for cid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        if cid in cells:
            m = re.match(r"\s*(\d+|No) contribution", text)
            counts[cells[cid]] = 0 if not m or m.group(1) == "No" else int(m.group(1))
    days = [{"date": d, "count": counts.get(d, 0)} for d in sorted(cells.values())]
    return days


def main():
    days = parse(fetch(USER))
    if not days:
        print("No contribution data parsed; keeping previous file.")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "user": USER,
        "updated": dt.date.today().isoformat(),
        "days": days,
    }, indent=0))
    print(f"Saved {len(days)} days, {sum(d['count'] for d in days)} contributions.")


if __name__ == "__main__":
    main()
