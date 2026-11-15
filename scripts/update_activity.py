#!/usr/bin/env python3
"""Generate a muted-blue GitHub contribution heatmap for the latest 30 days."""

from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import re

USERNAME = "NamithaR30"
OUTPUT = Path("assets/activity-30-days.svg")
COLORS = ["#161B22", "#26384C", "#3A5876", "#5F83A8", "#9BBDE0"]


class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attrs):
        if tag != "rect":
            return
        attrs = dict(attrs)
        raw_date = attrs.get("data-date")
        if not raw_date:
            return

        # GitHub's contribution calendar exposes data-date and an aria-label
        # (for example, "3 contributions on 2026-11-15").
        label = attrs.get("aria-label", "")
        match = re.search(r"(\d+) contributions?", label)
        count = int(match.group(1)) if match else 0
        if "no contributions" in label.lower():
            count = 0

        try:
            self.days[date.fromisoformat(raw_date)] = count
        except ValueError:
            pass


def fetch_contributions(start, end):
    url = (
        f"https://github.com/users/{USERNAME}/contributions"
        f"?from={start.isoformat()}&to={end.isoformat()}"
    )
    request = Request(url, headers={"User-Agent": "NamithaR30-profile-activity/1.0"})
    with urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8", errors="replace")
    parser = ContributionParser()
    parser.feed(page)
    if not parser.days:
        raise RuntimeError("Could not read contribution data from GitHub's public profile page.")
    return parser.days


def level_for(count, maximum):
    if count <= 0:
        return 0
    if maximum <= 1:
        return 1
    if count <= maximum * 0.25:
        return 1
    if count <= maximum * 0.50:
        return 2
    if count <= maximum * 0.75:
        return 3
    return 4


def build_svg(counts, start, end):
    offset = start.weekday()
    max_count = max(counts.values(), default=0)
    cell, gap = 17, 6
    left, top = 94, 48
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    width = left + 6 * (cell + gap) + 22
    height = top + 7 * (cell + gap) + 42

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contributions for the last 30 days">',
        '<rect width="100%" height="100%" rx="12" fill="#0D1117"/>',
        '<text x="20" y="25" fill="#D7E2EE" font-family="Segoe UI,Arial,sans-serif" font-size="14" font-weight="600">30-day contribution activity</text>',
        f'<text x="{width-20}" y="25" text-anchor="end" fill="#8295AA" font-family="Segoe UI,Arial,sans-serif" font-size="11">{start.strftime("%d %b")} – {end.strftime("%d %b %Y")}</text>',
    ]

    for row, label in enumerate(labels):
        if row in (0, 2, 4, 6):
            y = top + row * (cell + gap) + 13
            parts.append(f'<text x="20" y="{y}" fill="#8295AA" font-family="Segoe UI,Arial,sans-serif" font-size="10">{label}</text>')

    for i in range(30):
        day = start + timedelta(days=i)
        col = (offset + i) // 7
        row = (offset + i) % 7
        x = left + col * (cell + gap)
        y = top + row * (cell + gap)
        count = counts.get(day, 0)
        color = COLORS[level_for(count, max_count)]
        parts.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{color}">'
            f'<title>{day.isoformat()}: {count} contributions</title></rect>'
        )

    legend_y, legend_x = top + 7 * (cell + gap) + 16, 54
    parts.append(f'<text x="20" y="{legend_y}" fill="#8295AA" font-family="Segoe UI,Arial,sans-serif" font-size="10">Less</text>')
    for i, color in enumerate(COLORS):
        parts.append(f'<rect x="{legend_x + i*22}" y="{legend_y-10}" width="14" height="14" rx="3" fill="{color}"/>')
    parts.append(f'<text x="{legend_x + 5*22 + 2}" y="{legend_y}" fill="#8295AA" font-family="Segoe UI,Arial,sans-serif" font-size="10">More</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def main():
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=29)
    counts = fetch_contributions(start, end)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(counts, start, end), encoding="utf-8")
    print(f"Updated {OUTPUT} for {start} through {end}.")


if __name__ == "__main__":
    main()
