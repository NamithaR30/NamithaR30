#!/usr/bin/env python3
"""Generate a compact red-accent GitHub contribution grid for the latest 30 days."""
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import re

USERNAME = "NamithaR30"
OUTPUT = Path("assets/activity-30-days.svg")
COLORS = ["#241014", "#4B101B", "#811525", "#C51E32", "#FF3048"]


class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        raw_date = attrs.get("data-date")
        if not raw_date:
            return
        raw_level = attrs.get("data-level")
        if raw_level is not None and raw_level.isdigit():
            level = max(0, min(4, int(raw_level)))
        else:
            label = " ".join(str(attrs.get(k, "")) for k in ("aria-label", "title")).lower()
            if "no contributions" in label:
                level = 0
            else:
                match = re.search(r"(\d+) contributions?", label)
                if not match:
                    return
                level = min(4, int(match.group(1)))
        try:
            self.days[date.fromisoformat(raw_date)] = level
        except ValueError:
            pass


def fetch_contributions(start, end):
    url = f"https://github.com/users/{USERNAME}/contributions?from={start.isoformat()}&to={end.isoformat()}"
    req = Request(url, headers={"User-Agent": "NamithaR30-profile-activity/1.0"})
    with urlopen(req, timeout=30) as response:
        page = response.read().decode("utf-8", errors="replace")
    parser = ContributionParser()
    parser.feed(page)
    if not parser.days:
        raise RuntimeError("Could not read GitHub contribution calendar data.")
    return parser.days


def build_svg(levels, start, end):
    cell, gap, width, height = 20, 9, 560, 166
    left, top = (width - (6 * cell + 5 * gap)) // 2, 62
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="560" height="166" viewBox="0 0 {width} {height}" role="img" aria-label="Last 30 days of GitHub contribution activity">',
        '<rect width="560" height="166" rx="12" fill="#090909"/>',
        '<text x="24" y="29" fill="#F4E9EA" font-family="Segoe UI,Arial,sans-serif" font-size="15" font-weight="600">LAST 30 DAYS</text>',
        f'<text x="536" y="29" text-anchor="end" fill="#B98B91" font-family="Segoe UI,Arial,sans-serif" font-size="12">{start.strftime("%d %b")} — {end.strftime("%d %b %Y")}</text>',
    ]
    for i in range(30):
        day = start + timedelta(days=i)
        row, col = divmod(i, 6)
        x, y = left + col * (cell + gap), top + row * (cell + gap)
        level = levels.get(day, 0)
        parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="5" fill="{COLORS[level]}"><title>{day.isoformat()}: contribution level {level} of 4</title></rect>')
    legend_y = 147
    parts.append(f'<text x="{left}" y="{legend_y}" fill="#B98B91" font-family="Segoe UI,Arial,sans-serif" font-size="10">LESS</text>')
    for i, color in enumerate(COLORS):
        parts.append(f'<rect x="{left + 42 + i*20}" y="{legend_y-10}" width="12" height="12" rx="3" fill="{color}"/>')
    parts.append(f'<text x="{left + 42 + 5*20}" y="{legend_y}" fill="#B98B91" font-family="Segoe UI,Arial,sans-serif" font-size="10">MORE</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=29)
    levels = fetch_contributions(start, end)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(levels, start, end), encoding="utf-8")
    print(f"Updated {OUTPUT} for {start} through {end}.")


if __name__ == "__main__":
    main()
