import json
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ROW_H = 60
HEADER_H = 56
PAD_BOTTOM = 16
WIDTH = 760

CI_DOT = {
    "SUCCESS": "🟢 ",
    "FAILURE": "🔴 ",
    "ERROR": "🔴 ",
    "PENDING": "🟡 ",
    "EXPECTED": "🟡 ",
}


def truncate(text, limit=60):
    text = text or ""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def relative_time(iso_str):
    if not iso_str:
        return "n/a"
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    seconds = (datetime.now(timezone.utc) - dt).total_seconds()
    if seconds < 3600:
        return f"{max(int(seconds // 60), 1)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    days = int(seconds // 86400)
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def ci_dot(rollup):
    state = (rollup or {}).get("state")
    return CI_DOT.get(state, "")


def render(repos):
    height = HEADER_H + ROW_H * len(repos) + PAD_BOTTOM
    rows = []
    y = HEADER_H + 24
    for r in repos:
        name = escape(r["name"])
        url = escape(r["url"])
        desc = escape(truncate(r.get("description")))
        stars = r.get("stargazerCount", 0)
        forks = r.get("forkCount", 0)
        commit = ((r.get("defaultBranchRef") or {}).get("target")) or {}
        commits = (commit.get("history") or {}).get("totalCount", 0)
        updated = relative_time(commit.get("committedDate"))
        dot = ci_dot(commit.get("statusCheckRollup"))

        rows.append(f"""
  <a xlink:href="{url}" target="_blank">
    <text x="24" y="{y}" class="name">{dot}{name}</text>
  </a>
  <text x="24" y="{y + 18}" class="desc">{desc}</text>
  <text x="{WIDTH - 24}" y="{y}" text-anchor="end" class="stat">⭐ {stars}   🍴 {forks}</text>
  <text x="{WIDTH - 24}" y="{y + 18}" text-anchor="end" class="stat">🔨 {commits}   🕒 {updated}</text>""")
        y += ROW_H

    rows_svg = "".join(rows)

    return f"""<svg width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" font-family="'Segoe UI', Ubuntu, Sans-Serif">
  <style>
    .bg {{ fill: #161b22; }}
    .title {{ fill: #58a6ff; font-size: 16px; font-weight: 600; }}
    .name {{ fill: #c9d1d9; font-size: 14px; font-weight: 600; }}
    .desc {{ fill: #8b949e; font-size: 12px; }}
    .stat {{ fill: #c9d1d9; font-size: 13px; }}
    .divider {{ stroke: #30363d; stroke-width: 1; }}
  </style>
  <rect class="bg" x="0" y="0" width="{WIDTH}" height="{height}" rx="12" />
  <text x="24" y="34" class="title">🛠️ Things I maintain</text>
  <line class="divider" x1="24" y1="48" x2="{WIDTH - 24}" y2="48" />{rows_svg}
</svg>
"""


def demo():
    sample = [
        {
            "name": "cargo-pretty",
            "url": "https://github.com/romancitodev/cargo-pretty",
            "description": "A cargo build wrapper with a live, animated status view",
            "stargazerCount": 217,
            "forkCount": 3,
            "defaultBranchRef": {
                "target": {
                    "committedDate": "2026-09-12T01:37:54Z",
                    "history": {"totalCount": 33},
                    "statusCheckRollup": {"state": "FAILURE"},
                }
            },
        },
        {
            "name": "no-description-repo",
            "url": "https://github.com/romancitodev/no-description-repo",
            "description": None,
            "stargazerCount": 0,
            "forkCount": 0,
            "defaultBranchRef": None,
        },
    ]
    svg = render(sample)
    assert svg.count("<a xlink:href=") == len(sample)
    assert "🔴 cargo-pretty" in svg
    assert "🍴 0" in svg
    assert "n/a" in svg
    assert "&" not in svg.replace("&amp;", "").replace("&lt;", "").replace("&gt;", "")
    print("demo ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
        sys.exit(0)

    with open(sys.argv[1], encoding="utf-8-sig") as f:
        repos = json.load(f)

    sys.stdout.write(render(repos))
