"""Render the animated SVG cards used in the profile README.

Usage:
    python scripts/render_readme_cards.py           # animated cards
    STATIC=1 python scripts/render_readme_cards.py  # final frames only (for previews)

Reads data/contributions.json and profile.json, writes cards/*.svg.
GitHub strips scripts and styles from README HTML, but SVGs shown through <img>
still run their own <style> keyframes and SMIL animations, so all motion lives
inside each SVG. Fonts are embedded as base64 WOFF because <img> SVGs cannot
load external resources.
"""
import base64
import datetime as dt
import json
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
FONTS = ROOT / "fonts"
ASSETS = ROOT / "assets"
STATIC = os.environ.get("STATIC") == "1"

INK = "#1b1f24"
MUTED = "#5b6470"
LINE = "#e3e6ea"
CARD = "#ffffff"
ACCENT = "#2f5d8a"
ACCENT_SOFT = "#eaf1f7"
LEVELS = ["#ebedf0", "#c6d8ea", "#8fb2d3", "#5383b3", "#2f5d8a"]

FONT_FILES = {
    "sans": ("Inter", 400, "inter-latin-400-normal.woff"),
    "sans-bold": ("Inter", 600, "inter-latin-600-normal.woff"),
    "serif": ("SourceSerif", 600, "source-serif-4-latin-600-normal.woff"),
}


def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()


def font_css(*keys):
    rules = []
    for k in keys:
        family, weight, file = FONT_FILES[k]
        rules.append(
            f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64(FONTS / file)}) format('woff');}}"
        )
    return "".join(rules)


BASE_CSS = """
.sans{font-family:'Inter',Segoe UI,Helvetica,Arial,sans-serif}
.serif{font-family:'SourceSerif',Georgia,serif;font-weight:600}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes swing{0%{opacity:0;transform:translateY(26px) scale(.96)}70%{opacity:1;transform:translateY(-3px) scale(1.01)}100%{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}100%{opacity:1;transform:scale(1)}}
@keyframes slide{from{opacity:0;transform:translateX(-12px)}to{opacity:1;transform:none}}
.a{opacity:0;animation-fill-mode:forwards;animation-timing-function:cubic-bezier(.2,.7,.2,1)}
.bar{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:grow .9s cubic-bezier(.2,.7,.2,1) forwards}
.sq{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .35s ease-out forwards}
@media (prefers-reduced-motion: reduce){
  .a,.sq{animation:none!important;opacity:1!important;transform:none!important}
  .bar{animation:none!important;transform:none!important}
  .frame{display:none}
  .final{visibility:visible!important}
}
"""

STATIC_CSS = """
.a,.sq{opacity:1!important;transform:none!important;animation:none!important}
.bar{transform:none!important;animation:none!important}
.frame{display:none}
.final{visibility:visible!important}
"""


def svg(w, h, body, fonts, title):
    css = font_css(*fonts) + BASE_CSS + (STATIC_CSS if STATIC else "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title><style>{css}</style>{body}</svg>"
    )


def anim(name, delay, dur=0.7):
    return f'style="animation-name:{name};animation-duration:{dur}s;animation-delay:{delay:.2f}s"'


def card_bg(w, h, r=14):
    return (
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{r}" '
        f'fill="{CARD}" stroke="{LINE}"/>'
    )


def count_up(x, y, value, start, cls, size, fill, anchor="start", frames=18, dur=1.2):
    """Number count-up with SMIL <set> frames, since CSS cannot change text."""
    if STATIC or value <= 0:
        return (f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" fill="{fill}" '
                f'text-anchor="{anchor}">{value}</text>')
    out = []
    step = dur / frames
    for i in range(1, frames + 1):
        t = i / frames
        v = round(value * (1 - (1 - t) ** 3))
        begin = start + (i - 1) * step
        last = i == frames
        klass = f"{cls} final" if last else f"{cls} frame"
        timing = f'begin="{begin:.2f}s" fill="freeze"' if last else f'begin="{begin:.2f}s" dur="{step:.3f}s"'
        out.append(
            f'<text x="{x}" y="{y}" class="{klass}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" visibility="hidden">{v}'
            f'<set attributeName="visibility" to="visible" {timing}/></text>'
        )
    return "".join(out)


# ---------------------------------------------------------------- hero
def hero(p):
    w, h = 880, 230
    cover = b64(ASSETS / "cover.jpg")
    photo = b64(ASSETS / "photo.jpg")
    chips, cx = [], 214
    for i, c in enumerate(p["chips"]):
        cw = 24 + len(c) * 6.7
        chips.append(
            f'<g class="a" {anim("rise", 0.9 + i * 0.12)}>'
            f'<rect x="{cx:.0f}" y="168" width="{cw:.0f}" height="26" rx="13" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.45)"/>'
            f'<text x="{cx + cw/2:.0f}" y="185.5" class="sans" font-size="12.5" fill="#fff" text-anchor="middle">{escape(c)}</text></g>'
        )
        cx += cw + 8
    shine = "" if STATIC else (
        '<animateTransform attributeName="gradientTransform" type="translate" '
        'values="-1 0;1 0;1 0" keyTimes="0;0.45;1" dur="5s" begin="0.6s" repeatCount="indefinite"/>'
    )
    body = f"""
<defs>
  <clipPath id="r"><rect width="{w}" height="{h}" rx="16"/></clipPath>
  <clipPath id="c"><circle cx="110" cy="115" r="66"/></clipPath>
  <linearGradient id="shade" x1="0" x2="1">
    <stop offset="0" stop-color="#0d1622" stop-opacity=".88"/>
    <stop offset=".6" stop-color="#0d1622" stop-opacity=".55"/>
    <stop offset="1" stop-color="#0d1622" stop-opacity=".1"/>
  </linearGradient>
  <linearGradient id="shine" gradientUnits="objectBoundingBox" x1="0" x2="1">
    <stop offset="0" stop-color="#ffffff"/><stop offset=".42" stop-color="#ffffff"/>
    <stop offset=".5" stop-color="{"#ffffff" if STATIC else "#bcd6f0"}"/><stop offset=".58" stop-color="#ffffff"/>
    <stop offset="1" stop-color="#ffffff"/>{shine}
  </linearGradient>
</defs>
<g clip-path="url(#r)">
  <image href="data:image/jpeg;base64,{cover}" xlink:href="data:image/jpeg;base64,{cover}" x="0" y="0" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/>
  <rect width="{w}" height="{h}" fill="url(#shade)"/>
</g>
<g class="a" {anim("swing", 0.1, 0.9)}>
  <circle cx="110" cy="115" r="70" fill="#fff"/>
  <image href="data:image/jpeg;base64,{photo}" xlink:href="data:image/jpeg;base64,{photo}" x="44" y="49" width="132" height="132" clip-path="url(#c)" preserveAspectRatio="xMidYMid slice"/>
</g>
<text x="214" y="88" class="serif a" font-size="36" fill="url(#shine)" {anim("rise", 0.3)}>{escape(p["name"])}</text>
<text x="214" y="120" class="sans a" font-size="16" fill="#e8eef5" font-weight="600" {anim("rise", 0.5)}>{escape(p["role"])}</text>
<text x="214" y="146" class="sans a" font-size="13.5" fill="#cfd8e3" {anim("rise", 0.7)}>{escape(p["tagline"])}</text>
{"".join(chips)}
"""
    return svg(w, h, body, ["sans", "sans-bold", "serif"], f'{p["name"]}, {p["role"]}')


# ---------------------------------------------------------------- tiles
def tile(title, kicker, lines, delay, big=None, big_label=None, footer=None):
    w, h = 286, 190
    parts = [card_bg(w, h)]
    parts.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="5" rx="2" fill="{ACCENT}"/>')
    parts.append(f'<text x="22" y="38" class="sans a" font-size="11.5" fill="{MUTED}" letter-spacing="1.4" {anim("fade", delay)}>{escape(kicker.upper())}</text>')
    parts.append(f'<text x="22" y="66" class="serif a" font-size="22" fill="{INK}" {anim("rise", delay + 0.1)}>{escape(title)}</text>')
    y = 96
    if big is not None:
        parts.append(f'<g class="a" {anim("fade", delay + 0.2)}>' + count_up(22, 124, big, delay + 0.3, "serif", 44, ACCENT) + "</g>")
        parts.append(f'<text x="{22 + 26 * len(str(big))}" y="124" class="sans a" font-size="13" fill="{MUTED}" {anim("fade", delay + 0.5)}>{escape(big_label)}</text>')
        y = 152
    for i, ln in enumerate(lines):
        parts.append(
            f'<g class="a" {anim("slide", delay + 0.35 + i * 0.12)}>'
            f'<circle cx="26" cy="{y - 4}" r="3" fill="{ACCENT}"/>'
            f'<text x="36" y="{y}" class="sans" font-size="13" fill="{INK}">{escape(ln)}</text></g>'
        )
        y += 22
    if footer:
        parts.append(f'<text x="22" y="172" class="sans a" font-size="13" font-weight="600" fill="{ACCENT}" {anim("fade", delay + 0.9)}>{escape(footer)} →</text>')
    body = f'<g class="a" {anim("swing", delay, 0.8)}>' + "".join(parts) + "</g>"
    return svg(w, h, body, ["sans", "sans-bold", "serif"], title)


# ---------------------------------------------------------------- activity
def monthly(days):
    months = {}
    for d in days:
        key = d["date"][:7]
        months[key] = months.get(key, 0) + d["count"]
    last = sorted(months)[-12:]
    return [(k, months[k]) for k in last]


def activity(days):
    w, h = 880, 250
    data = monthly(days)
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    best = max((c for _, c in data), default=0) or 1
    parts = [card_bg(w, h)]
    parts.append(f'<text x="28" y="40" class="sans a" font-size="11.5" fill="{MUTED}" letter-spacing="1.4" {anim("fade", 0.1)}>GITHUB ACTIVITY · LAST 12 MONTHS</text>')
    parts.append(count_up(28, 92, total, 0.3, "serif", 46, INK))
    parts.append(f'<text x="28" y="116" class="sans a" font-size="13" fill="{MUTED}" {anim("fade", 0.6)}>contributions</text>')
    parts.append(count_up(28, 172, active, 0.5, "serif", 30, ACCENT))
    parts.append(f'<text x="28" y="194" class="sans a" font-size="13" fill="{MUTED}" {anim("fade", 0.8)}>active days</text>')
    x0, base, chart_h, bw, gap = 210, 200, 140, 40, 15
    for i in range(4):
        y = base - chart_h * i / 3
        parts.append(f'<line x1="{x0 - 6}" x2="{w - 26}" y1="{y:.1f}" y2="{y:.1f}" stroke="{LINE}" stroke-dasharray="{"" if i == 0 else "3 4"}"/>')
    for i, (key, c) in enumerate(data):
        x = x0 + i * (bw + gap)
        bh = max(2, chart_h * c / best) if c else 2
        fill = ACCENT if c == best and c > 0 else ("#8fb2d3" if c else LINE)
        parts.append(f'<rect class="bar" x="{x}" y="{base - bh:.1f}" width="{bw}" height="{bh:.1f}" rx="5" fill="{fill}" style="animation-delay:{0.4 + i * 0.07:.2f}s"/>')
        if c:
            parts.append(f'<text x="{x + bw/2}" y="{base - bh - 7:.1f}" class="sans a" font-size="11.5" font-weight="600" fill="{INK}" text-anchor="middle" {anim("fade", 1.1 + i * 0.07)}>{c}</text>')
        label = dt.date(int(key[:4]), int(key[5:]), 1).strftime("%b")
        parts.append(f'<text x="{x + bw/2}" y="{base + 20}" class="sans a" font-size="11.5" fill="{MUTED}" text-anchor="middle" {anim("fade", 0.3 + i * 0.05)}>{label}</text>')
    return svg(w, h, "".join(parts), ["sans", "sans-bold", "serif"], f"{total} GitHub contributions in the last year")


# ---------------------------------------------------------------- contribution graph
def graph(days):
    size, gap = 12, 3
    first = dt.date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    weeks = (len(days) + offset + 6) // 7
    w = 56 + weeks * (size + gap) + 20
    h = 64 + 7 * (size + gap) + 46
    w = max(w, 880)
    parts = [card_bg(w, h)]
    parts.append(f'<text x="28" y="32" class="sans a" font-size="11.5" fill="{MUTED}" letter-spacing="1.4" {anim("fade", 0.1)}>CONTRIBUTION GRAPH</text>')
    x0, y0 = 56, 66
    for lbl, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        parts.append(f'<text x="26" y="{y0 + row * (size + gap) + 10}" class="sans" font-size="10" fill="{MUTED}">{lbl}</text>')
    seen = set()
    for idx, d in enumerate(days):
        pos = idx + offset
        col, row = divmod(pos, 7)
        c = d["count"]
        lvl = 0 if c == 0 else 1 if c < 3 else 2 if c < 6 else 3 if c < 12 else 4
        x, y = x0 + col * (size + gap), y0 + row * (size + gap)
        date = dt.date.fromisoformat(d["date"])
        if date.day <= 7 and row == 0 and (date.year, date.month) not in seen:
            seen.add((date.year, date.month))
            parts.append(f'<text x="{x}" y="{y0 - 8}" class="sans" font-size="10" fill="{MUTED}">{date.strftime("%b")}</text>')
        parts.append(f'<rect class="sq" x="{x}" y="{y}" width="{size}" height="{size}" rx="3" fill="{LEVELS[lvl]}" style="animation-delay:{0.2 + col * 0.03 + row * 0.01:.2f}s"><title>{d["date"]}: {c}</title></rect>')
    ly = y0 + 7 * (size + gap) + 18
    lx = w - 28 - 5 * (size + gap) - 70
    parts.append(f'<text x="{lx}" y="{ly + 10}" class="sans" font-size="10" fill="{MUTED}">Less</text>')
    for i, col in enumerate(LEVELS):
        parts.append(f'<rect x="{lx + 30 + i * (size + gap)}" y="{ly}" width="{size}" height="{size}" rx="3" fill="{col}"/>')
    parts.append(f'<text x="{lx + 30 + 5 * (size + gap) + 4}" y="{ly + 10}" class="sans" font-size="10" fill="{MUTED}">More</text>')
    return svg(w, h, "".join(parts), ["sans"], "Contribution graph")


# ---------------------------------------------------------------- publications
def wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > n:
            lines.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}".strip()
    lines.append(cur)
    return lines


def publications(pubs):
    w = 880
    parts, y = [], 52
    rows = []
    for i, p in enumerate(pubs):
        tl = wrap(p["title"], 92)
        block_h = 20 * len(tl) + 46
        rows.append((p, tl, y, block_h))
        y += block_h + 12
    h = y + 10
    parts.append(card_bg(w, h))
    parts.append(f'<text x="28" y="34" class="sans a" font-size="11.5" fill="{MUTED}" letter-spacing="1.4" {anim("fade", 0.1)}>SELECTED PUBLICATIONS</text>')
    for i, (p, tl, top, bh) in enumerate(rows):
        d = 0.25 + i * 0.25
        g = [f'<rect x="20" y="{top}" width="{w - 40}" height="{bh}" rx="10" fill="{ACCENT_SOFT if p.get("first") else "#f6f7f8"}"/>',
             f'<rect x="20" y="{top}" width="4" height="{bh}" rx="2" fill="{ACCENT}"/>']
        ty = top + 26
        for ln in tl:
            g.append(f'<text x="40" y="{ty}" class="sans" font-size="14.5" font-weight="600" fill="{INK}">{escape(ln)}</text>')
            ty += 20
        meta = f'{p["venue"]} · {p["year"]}'
        g.append(f'<text x="40" y="{ty + 6}" class="sans" font-size="12.5" fill="{MUTED}">{escape(meta)}</text>')
        if p.get("first"):
            g.append(f'<rect x="{w - 140}" y="{top + 12}" width="100" height="22" rx="11" fill="{CARD}" stroke="{ACCENT}"/>'
                     f'<text x="{w - 90}" y="{top + 27}" class="sans" font-size="11.5" font-weight="600" fill="{ACCENT}" text-anchor="middle">First author</text>')
        parts.append(f'<g class="a" {anim("rise", d)}>' + "".join(g) + "</g>")
    return svg(w, h, "".join(parts), ["sans", "sans-bold"], "Selected publications")


def main():
    profile = json.loads((ROOT / "profile.json").read_text())
    days = json.loads((ROOT / "data" / "contributions.json").read_text())["days"]
    days = days[-371:]
    CARDS.mkdir(exist_ok=True)
    pubs = profile["publications"]
    out = {
        "hero.svg": hero(profile),
        "tile-research.svg": tile("Research", "Focus", profile["focus"], 0.2),
        "tile-publications.svg": tile("Publications", "Peer reviewed", [], 0.35,
                                      big=len(pubs), big_label="published papers",
                                      footer=f'{sum(1 for p in pubs if p.get("first"))} as first author'),
        "tile-portfolio.svg": tile("Portfolio", "Website", profile["links_preview"], 0.5,
                                   footer="kakon2002.github.io"),
        "activity.svg": activity(days),
        "graph.svg": graph(days),
        "publications.svg": publications(pubs),
    }
    for name, content in out.items():
        (CARDS / name).write_text(content)
        print(f"wrote cards/{name} ({len(content) // 1024} KB)")


if __name__ == "__main__":
    main()
