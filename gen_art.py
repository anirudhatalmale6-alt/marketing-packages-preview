#!/usr/bin/env python3
"""
Generates the placeholder artwork for each package as plain SVG.

Everything is drawn here, so the site makes zero external image requests and
every file is a couple of KB. Swap these out for real photography later by
dropping a .jpg in site/assets/img/ with the same name and changing the <img src>.
"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site", "assets", "img")
os.makedirs(OUT, exist_ok=True)

# One palette per site theme. The artwork has to agree with the stylesheet —
# paper-coloured SVGs on the dark theme read as broken white boxes.
PALETTES = {
    "paper": {
        "PAPER": "#efeade", "INK": "#141310", "SIGNAL": "#e8431f",
        "DEEP": "#16302f", "MINT": "#a8d8c8", "RULE": "#d8d1c2",
        "GROUND": "#141310", "MARK": "#efeade", "GRAIN": 0.10,
    },
    "studio": {
        "PAPER": "#15171c", "INK": "#f3f4f1", "SIGNAL": "#c8f44f",
        "DEEP": "#0d0e11", "MINT": "#8fe3c4", "RULE": "#272b32",
        "GROUND": "#0a0b0e", "MARK": "#f3f4f1", "GRAIN": 0.05,
    },
}

# module-level names the drawing functions read; set by build()
PAPER = INK = SIGNAL = DEEP = MINT = RULE = GROUND = MARK = ""
GRAIN_OPACITY = 0.10


def use_palette(name):
    global PAPER, INK, SIGNAL, DEEP, MINT, RULE, GROUND, MARK, GRAIN_OPACITY
    pal = PALETTES[name]
    PAPER, INK, SIGNAL = pal["PAPER"], pal["INK"], pal["SIGNAL"]
    DEEP, MINT, RULE = pal["DEEP"], pal["MINT"], pal["RULE"]
    GROUND, MARK = pal["GROUND"], pal["MARK"]
    GRAIN_OPACITY = pal["GRAIN"]


use_palette("paper")

GRAIN = (
    '<filter id="g"><feTurbulence type="fractalNoise" baseFrequency="0.85" '
    'numOctaves="3" result="n"/><feColorMatrix in="n" type="saturate" values="0"/>'
    "</filter>"
)


def frame(w, h, body, extra_defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img">'
        f"<defs>{GRAIN}{extra_defs}</defs>"
        f'<rect width="{w}" height="{h}" fill="{PAPER}"/>'
        f"{body}"
        f'<rect width="{w}" height="{h}" filter="url(#g)" opacity="{GRAIN_OPACITY}"/>'
        "</svg>"
    )


# --- six distinct generative styles ---------------------------------------

def style_rings(w, h, rnd):
    """Concentric arcs radiating from an off-centre focus."""
    cx, cy = w * 0.68, h * 0.78
    out = []
    n = 16
    for i in range(n):
        r = (i + 1) * (max(w, h) / n) * 0.78
        col = SIGNAL if i % 5 == 2 else INK
        wid = 9 if i % 5 == 2 else 1.4
        op = 0.9 if i % 5 == 2 else 0.5
        out.append(
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="none" '
            f'stroke="{col}" stroke-width="{wid}" opacity="{op}"/>'
        )
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{w*0.055:.0f}" fill="{DEEP}"/>')
    return "".join(out)


def style_bars(w, h, rnd):
    """A skyline of bars — the obvious 'growth' read, done with restraint."""
    out = [f'<rect width="{w}" height="{h*0.32:.0f}" fill="{DEEP}"/>']
    n = 22
    gap = w / n
    for i in range(n):
        t = i / (n - 1)
        hh = h * (0.14 + 0.72 * (t ** 1.6)) * rnd.uniform(0.72, 1.0)
        x = i * gap + gap * 0.18
        col = SIGNAL if i >= n - 4 else INK
        op = 1 if i >= n - 4 else 0.12 + 0.55 * t
        out.append(
            f'<rect x="{x:.1f}" y="{h-hh:.1f}" width="{gap*0.64:.1f}" '
            f'height="{hh:.1f}" fill="{col}" opacity="{op:.2f}"/>'
        )
    return "".join(out)


def style_dots(w, h, rnd):
    """Halftone field cut by one hard diagonal."""
    out = []
    cols, rows = 26, 16
    for r in range(rows):
        for c in range(cols):
            x = (c + 0.5) * w / cols
            y = (r + 0.5) * h / rows
            d = (c / cols + r / rows) / 2
            rad = 1.6 + 9 * (d ** 2)
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{INK}" opacity="0.5"/>')

    out.append(
        f'<path d="M{-w*0.1:.0f} {h*0.86:.0f} L{w*1.1:.0f} {h*0.1:.0f} '
        f'L{w*1.1:.0f} {h*0.26:.0f} L{-w*0.1:.0f} {h*1.02:.0f} Z" fill="{SIGNAL}"/>'
    )
    out.append(f'<circle cx="{w*0.22:.0f}" cy="{h*0.26:.0f}" r="{h*0.1:.0f}" fill="{MINT}"/>')
    return "".join(out)


def style_blobs(w, h, rnd):
    """Overlapping translucent discs — layered audiences."""
    defs = []
    out = [f'<rect width="{w}" height="{h}" fill="{DEEP}"/>']
    # all four discs stay in the warm half of the palette — a desaturated
    # overlay here reads as muddy grey once the screen blend lands on the dark
    # ground, which is exactly what we are avoiding
    spots = [
        (0.30, 0.42, 0.30, MINT, 0.90),
        (0.58, 0.62, 0.26, SIGNAL, 0.92),
        (0.74, 0.32, 0.20, MINT, 0.55),
        (0.44, 0.74, 0.15, SIGNAL, 0.60),
    ]
    for fx, fy, fr, col, op in spots:
        out.append(
            f'<circle cx="{w*fx:.0f}" cy="{h*fy:.0f}" r="{min(w,h)*fr:.0f}" '
            f'fill="{col}" opacity="{op}" style="mix-blend-mode:screen"/>'
        )
    for i in range(9):
        y = h * (0.08 + i * 0.105)
        out.append(
            f'<line x1="0" y1="{y:.0f}" x2="{w}" y2="{y:.0f}" '
            f'stroke="{MARK}" stroke-width="1" opacity="0.14"/>'
        )
    return "".join(out), "".join(defs)


def style_squares(w, h, rnd):
    """Nested rotating squares — structure, systems, process."""
    cx, cy = w * 0.5, h * 0.52
    out = []
    # the outer rings sat at 0.72 opacity in 1px, which all but vanished at
    # card size — weight and darken them so the figure holds at 300px wide
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{min(w,h)*0.46:.0f}" fill="{PAPER}"/>')
    for i in range(11):
        s = min(w, h) * (0.92 - i * 0.078)
        rot = i * 7.5
        col = SIGNAL if i == 3 else (DEEP if i == 7 else INK)
        wid = 8 if i in (3, 7) else 2.2
        out.append(
            f'<rect x="{cx-s/2:.1f}" y="{cy-s/2:.1f}" width="{s:.1f}" height="{s:.1f}" '
            f'fill="none" stroke="{col}" stroke-width="{wid}" opacity="0.92" '
            f'transform="rotate({rot:.1f} {cx:.1f} {cy:.1f})"/>'
        )
    return "".join(out)


def style_burst(w, h, rnd):
    """Rays from a low-left origin — reach, distribution, broadcast."""
    cx, cy = w * 0.08, h * 1.02
    out = [f'<rect width="{w}" height="{h}" fill="{GROUND}"/>']
    for i in range(46):
        a = math.radians(-88 + i * 1.92)
        L = max(w, h) * 1.7
        x2 = cx + math.cos(a) * L
        y2 = cy + math.sin(a) * L
        col = SIGNAL if i % 7 == 3 else (MINT if i % 11 == 5 else MARK)
        op = 0.9 if i % 7 == 3 else rnd.uniform(0.08, 0.3)
        out.append(
            f'<line x1="{cx:.0f}" y1="{cy:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
            f'stroke="{col}" stroke-width="{2.6 if i%7==3 else 1.4}" opacity="{op:.2f}"/>'
        )
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{h*0.14:.0f}" fill="{SIGNAL}"/>')
    return "".join(out)


STYLES = [style_rings, style_bars, style_dots, style_blobs, style_squares, style_burst]


def render(slug, index, w, h):
    rnd = random.Random(1000 + index * 17)
    fn = STYLES[index % len(STYLES)]
    res = fn(w, h, rnd)
    if isinstance(res, tuple):
        body, defs = res
    else:
        body, defs = res, ""
    return frame(w, h, body, defs)


def build(packages, outdir=None, palette="paper"):
    outdir = outdir or OUT
    os.makedirs(outdir, exist_ok=True)
    use_palette(palette)
    for i, p in enumerate(packages):
        with open(os.path.join(outdir, f"{p['slug']}-card.svg"), "w") as f:
            f.write(render(p["slug"], i, 1200, 750))
        with open(os.path.join(outdir, f"{p['slug']}-wide.svg"), "w") as f:
            f.write(render(p["slug"], i, 1600, 760))
    print(f"  artwork: {len(packages)*2} svg ({palette}) -> {outdir}")


if __name__ == "__main__":
    import json
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "packages.json")) as f:
        build(json.load(f)["packages"])
