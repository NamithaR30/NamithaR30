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
    """Read GitHub's contribution calendar cells (not SVG rect elements)."""

    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        raw_date = attrs.get("data-date")
        if not raw_date:
            return

        # GitHub renders calendar cells with data-date and data-level.
        raw_level = attrs.get("data-level")
        if raw_level is not None and raw_level.isdigit():
            level = max(0, min(4, int(raw_level)))
        else:
            # Fallback for markup variants that expose a count in a label.
            label = " ".join(
                str(attrs.get(key, "")) for key in ("aria-label", "title")
            ).lower()
            if "no contributions" in label:
                level = 0
            else:
                match = re.search(r"(\d+) contributions?", label)
                if not match:
                    return
                count = int(match.group(1))
                level = 0 if count == 0 else min(4, count)

        try:
            self.days[date.fromisoformat(raw_date)] = level
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
        raise RuntimeError(
            "Could not find GitHub contribution calendar cells (data-date/data-level)."
        )
    return parser.days


def build_svg(levels, start, end):
    # A 30-day window arranged as a compact, Monday-first calendar.
    offset = start.weekday()
    cell, gap = 17, 6
    left, top = 94, 48
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    width = left + 6 * (cell + gap) + 22
    height = top + 7 * (cell + gap) + 42

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contribution activity for the last 30 days">',
        '<rect width="100%" height="100%" rx="12" fill="#0D1117"/>',
        '<text x="20" y="25" fill="#D7E2EE" font-family="Segoe UI,Arial,sans-serif" font-size="14" font-weight="600">30-day contribution activity</text>',
        f'<text x="{width-20}" y="25" text-anchor="end" fill="#8295AA" font-family="Segoe UI,Arial,sans-serif" font-size="11">{start.strftime("%d %b")} – {end.strftime("%d %b %Y")}</text>',
    ]

    for row, label in enumerate(labels):
        if row in (0, 2, 4, 6):
            y = top + row * (cell + gap) + 13
            parts.append(
                f'<text x="20" y="{y}" fill="#8295AA" font-family="Segoe UI,Arial,sans-serif" font-size="10">{label}</text>'
            )

    for i in range(30):
        day = start + timedelta(days=i)
        col = (offset + i) // 7
        row = (offset + i) % 7
        x = left + col * (cell + gap)
        y = top + row * (cell + gap)
        level = levels.get(day, 0)
        color = COLORS[level]
        parts.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{color}">'
            f'<title>{day.isoformat()}: activity level {level} of 4</title></rect>'
        )

    legend_y, legend_x = top + 7 * (cell + gap) + 16, 54
    parts.append(
        f'<text x="20" y="{legend_y}" fill="#8295AA" font-family="Segoe UI,Arial,sans-serif" font-size="10">Less</text>'
    )
    for i, color in enumerate(COLORS):
        parts.append(
            f'<rect x="{legend_x + i*22}" y="{legend_y-10}" width="14" height="14" rx="3" fill="{color}"/>'
        )
    parts.append(
        f'<text x="{legend_x + 5*22 + 2}" y="{legend_y}" fill="#8295AA" font-family="Segoe UI,Arial,sans-serif" font-size="10">More</text>'
    )
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
