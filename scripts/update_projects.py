#!/usr/bin/env python3
"""Refresh the profile README's latest public repository cards."""
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen
import json
import textwrap

USERNAME = "NamithaR30"
PROFILE_REPO = "NamithaR30"
ROOT = Path(".")
README = ROOT / "README.md"
ASSETS = ROOT / "assets"
START = "<!-- AUTO-PROJECTS:START -->"
END = "<!-- AUTO-PROJECTS:END -->"
CARD_WIDTH = 520
CARD_HEIGHT = 178
RED = "#FF3048"


def fetch_repositories():
    url = f"https://api.github.com/users/{USERNAME}/repos?type=owner&sort=updated&direction=desc&per_page=100"
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "NamithaR30-profile-projects/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(request, timeout=30) as response:
        repositories = json.loads(response.read().decode("utf-8"))

    eligible = [
        repo for repo in repositories
        if not repo.get("fork")
        and not repo.get("archived")
        and not repo.get("private")
        and repo.get("name", "").lower() != PROFILE_REPO.lower()
    ]
    eligible.sort(key=lambda repo: repo.get("updated_at", ""), reverse=True)
    return eligible[:4]


def shorten(value, limit):
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[:limit - 1].rstrip() + "…"


def make_card(repo, slot):
    name = shorten(repo.get("name") or "Untitled project", 34)
    description = shorten(repo.get("description") or "Explore this project and its source code.", 72)
    language = repo.get("language") or "Software project"
    updated = repo.get("updated_at", "")
    try:
        updated_label = datetime.fromisoformat(updated.replace("Z", "+00:00")).strftime("%d %b %Y")
    except (TypeError, ValueError):
        updated_label = "Recently updated"

    words = textwrap.wrap(description, width=53)[:2]
    if not words:
        words = ["Explore this project and its source code."]
    desc_svg = "\n".join(
        f'<text x="24" y="{91 + i * 22}" fill="#E5DADD" font-family="Segoe UI,Arial,sans-serif" font-size="14">{escape(line)}</text>'
        for i, line in enumerate(words)
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" role="img" aria-label="{escape(name, quote=True)} repository card">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#100B0D"/><stop offset="1" stop-color="#090909"/></linearGradient>
</defs>
<rect x="1.5" y="1.5" width="517" height="175" rx="13" fill="url(#bg)" stroke="#C51E32" stroke-width="2"/>
<path d="M270 177 C350 149 420 167 520 109" fill="none" stroke="#7F1425" stroke-width="1.4" opacity=".45"/>
<path d="M350 177 C415 153 470 149 520 128" fill="none" stroke="#E3263D" stroke-width="1.2" opacity=".4"/>
<text x="24" y="43" fill="{RED}" font-family="Segoe UI,Arial,sans-serif" font-size="22" font-weight="700">⌘</text>
<text x="68" y="43" fill="#F5E9EA" font-family="Segoe UI,Arial,sans-serif" font-size="21" font-weight="700">{escape(name)}</text>
{desc_svg}
<text x="24" y="158" fill="#C99BA2" font-family="Segoe UI,Arial,sans-serif" font-size="12">{escape(shorten(language, 24))}  ·  Updated {escape(updated_label)}</text>
<text x="490" y="43" text-anchor="end" fill="{RED}" font-family="Segoe UI,Arial,sans-serif" font-size="18">↗</text>
</svg>
'''
    filename = f"latest-project-{slot}.svg"
    (ASSETS / filename).write_text(svg, encoding="utf-8")
    url = repo.get("html_url") or f"https://github.com/{USERNAME}/{repo.get('name', '')}"
    return (
        f'<td width="50%" valign="top"><a href="{escape(url, quote=True)}">'
        f'<img src="assets/{filename}" alt="{escape(name, quote=True)}" width="100%" />'
        f'</a></td>'
    )


def make_readme_block(repositories):
    cells = [make_card(repo, i + 1) for i, repo in enumerate(repositories)]
    if not cells:
        return f"{START}\n_No public projects found yet._\n{END}"

    rows = []
    for index in range(0, len(cells), 2):
        row_cells = cells[index:index + 2]
        if len(row_cells) == 1:
            row_cells.append('<td width="50%"></td>')
        rows.append("<tr>\n" + "\n".join(row_cells) + "\n</tr>")
    generated = (
        START + "\n"
        + '<div align="center">\n\n<table>\n'
        + "\n".join(rows)
        + "\n</table>\n\n"
        + '<sub>Automatically refreshed daily · Latest public repositories, excluding forks and archived projects</sub>\n\n'
        + '</div>\n'
        + END
    )
    return generated


def main():
    content = README.read_text(encoding="utf-8")
    if START not in content or END not in content:
        raise RuntimeError("README is missing AUTO-PROJECTS markers; refusing to overwrite manual content.")

    repositories = fetch_repositories()
    block = make_readme_block(repositories)
    before, remainder = content.split(START, 1)
    _, after = remainder.split(END, 1)
    updated = before + block + after
    README.write_text(updated, encoding="utf-8")
    print(f"Generated {min(len(repositories), 4)} latest public repository cards.")


if __name__ == "__main__":
    main()
