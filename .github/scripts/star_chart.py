#!/usr/bin/env python3
"""Draw the README's star history chart from the GitHub API.

Writes stars.svg (light) and stars-dark.svg into .github/star-chart/.
The workflow in .github/workflows/star-chart.yml runs it once a day and
pushes the two files to the star-chart-images branch, where the README
loads them; they aren't kept on main.
GitHub only lists stargazers to a signed-in caller, so a run by hand needs
a token too, for example from the GitHub CLI:

    GITHUB_TOKEN=$(gh auth token) python3 .github/scripts/star_chart.py owner/repo

Standard library only, so the workflow needs no setup step.
"""

import bisect
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://api.github.com"
OUT_DIR = Path(__file__).resolve().parent.parent / "star-chart"

W, H = 800, 400
# Plot area. The left margin fits the y labels, the right one the count
# printed at the end of the line.
X0, X1 = 56, W - 64
Y0, Y1 = 84, H - 44
# Points the curve passes through. Few enough that it flows instead of
# tracing every single star as a step.
SAMPLES = 28

FONT = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', "
        "Helvetica, Arial, sans-serif")
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

# GitHub's own page colors, so the chart sits on the README like part of it.
# The two line blues passed a contrast check against these backgrounds.
THEMES = {
    "stars.svg": {
        "surface": "#ffffff", "border": "#d1d9e0", "text": "#1f2328",
        "muted": "#59636e", "grid": "#eaeef2", "baseline": "#d1d9e0",
        "line": "#2a78d6",
        "star_top": "#ffd84d", "star_bottom": "#f5a300", "star_edge": "#d98c00",
    },
    "stars-dark.svg": {
        "surface": "#0d1117", "border": "#3d444d", "text": "#f0f6fc",
        "muted": "#9198a1", "grid": "#21262d", "baseline": "#3d444d",
        "line": "#3987e5",
        "star_top": "#ffe27a", "star_bottom": "#f2a51f", "star_edge": "#f2a51f",
    },
}


def star_path(cx, cy, r, inner=0.56, round_tip=0.34, round_dip=0.26):
    """A plump five-point star with every corner curved.

    Drawn here so no icon set has to be copied in. A wide inner radius and
    curved tips and dips make it look puffed up rather than spiky.
    """
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * inner
        a = math.pi * (i / 5 - 0.5)
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))

    def toward(p, q, k):
        return (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)

    d = []
    for i, p in enumerate(pts):
        k = round_tip if i % 2 == 0 else round_dip
        a, b = toward(p, pts[i - 1], k), toward(p, pts[(i + 1) % 10], k)
        d.append(f"{'M' if i == 0 else 'L'}{num(a[0])} {num(a[1])}"
                 f"Q{num(p[0])} {num(p[1])} {num(b[0])} {num(b[1])}")
    return "".join(d) + "Z"


def star_icon(cx, cy, r, t):
    """The gold star before the title: a top-lit gradient and a small shine."""
    return "".join([
        '<defs><linearGradient id="star-gold" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{t["star_top"]}"/>',
        f'<stop offset="1" stop-color="{t["star_bottom"]}"/>',
        "</linearGradient></defs>",
        f'<path d="{star_path(cx, cy, r)}" fill="url(#star-gold)" '
        f'stroke="{t["star_edge"]}" stroke-width="0.8" stroke-linejoin="round"/>',
        f'<ellipse cx="{num(cx - r * 0.3)}" cy="{num(cy - r * 0.28)}" '
        f'rx="{num(r * 0.24)}" ry="{num(r * 0.15)}" '
        f'transform="rotate(-35 {num(cx - r * 0.3)} {num(cy - r * 0.28)})" '
        'fill="#ffffff" fill-opacity="0.6"/>',
    ])


def get(url, token, accept):
    req = urllib.request.Request(url, headers={
        "Accept": accept,
        "User-Agent": "star-chart-script",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp), resp.headers.get("Link") or ""


def fetch(repo, token):
    """Return the repo's creation time and the sorted times of its stars."""
    info, _ = get(f"{API}/repos/{repo}", token, "application/vnd.github+json")
    created = parse_time(info["created_at"])
    # This media type adds starred_at to each stargazer; without it the API
    # lists the users only. Only the times are kept: no names end up in the repo.
    url = f"{API}/repos/{repo}/stargazers?per_page=100"
    times = []
    while url:
        page, link = get(url, token, "application/vnd.github.star+json")
        times += [parse_time(s["starred_at"]) for s in page]
        nxt = re.search(r'<([^>]+)>;\s*rel="next"', link)
        url = nxt.group(1) if nxt else None
    return created, sorted(times)


def parse_time(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def num(v):
    # Fixed decimals keep the SVG byte-identical for the same stars, so the
    # workflow commits only when the stars really changed.
    return f"{v:.1f}"


def sign(v):
    return (v > 0) - (v < 0)


def smooth_path(pts):
    """A smooth curve through the points that never overshoots them.

    Monotone cubic interpolation (the same rule as d3's curveMonotoneX): a
    flat stretch stays flat and the curve never dips below a count it
    already reached, which an ordinary spline would do around a burst.
    """
    n = len(pts)
    slopes = [(pts[i + 1][1] - pts[i][1]) / (pts[i + 1][0] - pts[i][0])
              for i in range(n - 1)]
    tangents = [slopes[0]]
    for i in range(1, n - 1):
        s0, s1 = slopes[i - 1], slopes[i]
        h0 = pts[i][0] - pts[i - 1][0]
        h1 = pts[i + 1][0] - pts[i][0]
        p = (s0 * h1 + s1 * h0) / (h0 + h1)
        tangents.append((sign(s0) + sign(s1)) * min(abs(s0), abs(s1), abs(p) / 2))
    tangents.append(slopes[-1])
    # The end tangents follow the neighbor, so the curve starts and ends smoothly.
    tangents[0] = (3 * slopes[0] - tangents[1]) / 2 if n > 2 else slopes[0]
    tangents[-1] = (3 * slopes[-1] - tangents[-2]) / 2 if n > 2 else slopes[-1]
    tangents[0] = sign(slopes[0]) * min(abs(tangents[0]), 3 * abs(slopes[0]))
    tangents[-1] = sign(slopes[-1]) * min(abs(tangents[-1]), 3 * abs(slopes[-1]))

    d = [f"M{num(pts[0][0])} {num(pts[0][1])}"]
    for i in range(n - 1):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        h = (xb - xa) / 3
        d.append(f"C{num(xa + h)} {num(ya + tangents[i] * h)} "
                 f"{num(xb - h)} {num(yb - tangents[i + 1] * h)} "
                 f"{num(xb)} {num(yb)}")
    return "".join(d)


def y_ticks(count):
    """A 1/2/5 step giving at most 5 steps, and the top of the axis."""
    top = max(count, 1)
    scale = 1
    while True:
        for base in (1, 2, 5):
            step = base * scale
            steps = -(-top // step)
            if steps <= 5:
                return step, steps * step
        scale *= 10


def y_label(v, compact):
    if not compact or v == 0:
        return f"{v:,}"
    k = v / 1000
    return f"{k:g}K"


def x_ticks(start, end):
    """Dates for the x axis: days, weeks, months or years, at most 7 ticks."""
    first_day = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)

    def days(step):
        # Counted from a Monday, so 7- and 14-day steps land on Mondays.
        out = []
        d = first_day
        while d <= end:
            n = (d - datetime(1970, 1, 5, tzinfo=timezone.utc)).days
            if d >= start and n % step == 0:
                out.append(d)
            d += timedelta(days=1)
        return out

    def months(step):
        out = []
        y, m = start.year, start.month
        while True:
            d = datetime(y, m, 1, tzinfo=timezone.utc)
            if d > end:
                return out
            if d >= start and (y * 12 + m - 1) % step == 0:
                out.append(d)
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)

    span = (end - start).days
    options = []
    if span <= 60:
        options += [("day", lambda n=n: days(n)) for n in (1, 2, 7, 14)]
    options += [("month", lambda n=n: months(n)) for n in (1, 2, 3, 6)]
    options += [("year", lambda n=n: months(12 * n)) for n in (1, 2, 5, 10, 20)]
    for kind, make in options:
        ticks = make()
        if len(ticks) <= 7:
            return kind, ticks
    return options[-1][0], options[-1][1]()


def x_label(kind, d, prev):
    if kind == "day":
        return f"{MONTHS[d.month - 1]} {d.day}"
    if kind == "year":
        return str(d.year)
    # Months: show the year on the first tick and on each January only.
    if prev is None or d.month == 1:
        return f"{MONTHS[d.month - 1]} {d.year}"
    return MONTHS[d.month - 1]


def render(repo, created, times, theme):
    t = THEMES[theme]
    count = len(times)
    start = min([created] + times)
    # The axis ends at the last star, not at "now", so the same stars always
    # give the same file. A week at least, so one star doesn't fill the width.
    end = max([start + timedelta(days=7)] + times)
    span = (end - start).total_seconds()

    def x(d):
        return X0 + (X1 - X0) * (d - start).total_seconds() / span

    step, top = y_ticks(count)

    def y(v):
        return Y1 - (Y1 - Y0) * v / top

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" font-family="{FONT}">',
        f"<title>Star history of {repo}: {count:,} star{'' if count == 1 else 's'}</title>",
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" '
        f'fill="{t["surface"]}" stroke="{t["border"]}"/>',
        star_icon(33, 31, 11, t),
        f'<text x="50" y="36" font-size="16" font-weight="600" '
        f'fill="{t["text"]}">Star history</text>',
        f'<text x="50" y="56" font-size="12" fill="{t["muted"]}">{repo}</text>',
    ]

    # Gridlines and y labels; the baseline at 0 is drawn a step darker.
    compact = top >= 10000
    for v in range(0, top + 1, step):
        color = t["baseline"] if v == 0 else t["grid"]
        out.append(f'<line x1="{X0}" y1="{num(y(v))}" x2="{X1}" y2="{num(y(v))}" '
                   f'stroke="{color}" stroke-width="1"/>')
        out.append(f'<text x="{X0 - 8}" y="{num(y(v) + 4)}" font-size="12" '
                   f'text-anchor="end" fill="{t["muted"]}" '
                   f'style="font-variant-numeric: tabular-nums">'
                   f"{y_label(v, compact)}</text>")

    kind, ticks = x_ticks(start, end)
    prev = None
    for d in ticks:
        out.append(f'<text x="{num(x(d))}" y="{Y1 + 22}" font-size="12" '
                   f'text-anchor="middle" fill="{t["muted"]}">'
                   f"{x_label(kind, d, prev)}</text>")
        prev = d

    # The count at evenly spaced moments, joined by a smooth curve. A fixed
    # number of samples keeps the file small however many stars there are.
    samples = []
    for j in range(SAMPLES + 1):
        moment = start + (end - start) * j / SAMPLES
        samples.append((x(moment), y(bisect.bisect_right(times, moment))))
    line = smooth_path(samples)
    out.append(
        '<defs><linearGradient id="area" gradientUnits="userSpaceOnUse" '
        f'x1="0" y1="{Y0}" x2="0" y2="{Y1}">'
        f'<stop offset="0" stop-color="{t["line"]}" stop-opacity="0.35"/>'
        f'<stop offset="1" stop-color="{t["line"]}" stop-opacity="0.03"/>'
        "</linearGradient></defs>")
    out.append(f'<path d="{line}V{num(y(0))}H{num(X0)}Z" fill="url(#area)"/>')
    out.append(f'<path d="{line}" fill="none" stroke="{t["line"]}" '
               f'stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')

    # The current count at the end of the line, on a soft halo. No ring in
    # the background color: the line runs into the dot, and a ring would cut
    # the dot off from it.
    ey = y(count)
    out.append(f'<circle cx="{X1}" cy="{num(ey)}" r="10" fill="{t["line"]}" '
               f'fill-opacity="0.18"/>')
    out.append(f'<circle cx="{X1}" cy="{num(ey)}" r="5" fill="{t["line"]}"/>')
    out.append(f'<text x="{X1 + 15}" y="{num(ey + 4)}" font-size="13" '
               f'font-weight="600" fill="{t["text"]}">{count:,}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    args = sys.argv[1:]
    repo = args[0] if args else os.environ.get("GITHUB_REPOSITORY")
    if not repo or "/" not in repo:
        sys.exit("usage: star_chart.py owner/repo (or set GITHUB_REPOSITORY)")
    try:
        created, times = fetch(repo, os.environ.get("GITHUB_TOKEN"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit("GitHub wants a login to list stargazers: set GITHUB_TOKEN, "
                     "for example GITHUB_TOKEN=$(gh auth token)")
        raise
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in THEMES:
        # newline="\n" so a run on Windows writes the same bytes as the workflow.
        with open(OUT_DIR / name, "w", encoding="utf-8", newline="\n") as f:
            f.write(render(repo, created, times, name))
    print(f"{repo}: {len(times)} stars, wrote {', '.join(THEMES)} to {OUT_DIR}")


if __name__ == "__main__":
    main()
