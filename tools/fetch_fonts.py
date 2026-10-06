#!/usr/bin/env python3
"""
Downloads the three webfonts the site uses, subsets them to the characters we
actually render, and writes site/assets/css/fonts.css.

Why self-host instead of linking Google Fonts:
  · no third-party request on first paint, so text appears sooner
  · nothing leaves the visitor's browser to another domain (GDPR-friendly)
  · the fonts cannot disappear or change under us

Run only when the font list changes:  python3 tools/fetch_fonts.py
The output (woff2 + fonts.css) is committed, so a normal build never needs network.
"""
import os
import re
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTDIR = os.path.join(ROOT, "site", "assets", "fonts")
CSSOUT = os.path.join(ROOT, "site", "assets", "css", "fonts.css")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Everything the site can render: ASCII, latin-1 accents, smart punctuation,
# and the four symbols used as bullets and arrows.
UNICODES = ",".join([
    "U+0020-007E", "U+00A0-00FF", "U+0131", "U+0152-0153",
    "U+2013-2014", "U+2018-201A", "U+201C-201E", "U+2020", "U+2022",
    "U+2026", "U+2039-203A", "U+20AC", "U+2122", "U+2191-2193",
    "U+2212", "U+2713", "U+2736", "U+00D7",
])

FAMILIES = [
    {
        "key": "bricolage",
        "family": "Bricolage Grotesque",
        "query": "Bricolage+Grotesque:opsz,wght@12..96,400..800",
        "faces": [("normal", "400 800")],
        # headings dominate this family, so freeze optical size at a display value
        "pin": {"opsz": 72, "wdth": 100},
    },
    {
        "key": "newsreader",
        "family": "Newsreader",
        "query": "Newsreader:ital,opsz,wght@0,6..72,300..600;1,6..72,300..500",
        "faces": [("italic", "300 500"), ("normal", "300 600")],
        "pin": {"opsz": 16},
    },
    {
        "key": "jbmono",
        "family": "JetBrains Mono",
        "query": "JetBrains+Mono:wght@400;500",
        "faces": [("normal", "400 500")],
        "pin": {},
    },
    # --- studio theme ---------------------------------------------------
    {
        "key": "gabarito",
        "family": "Gabarito",
        "query": "Gabarito:wght@400..900",
        "faces": [("normal", "400 900")],
        "pin": {},
    },
    {
        "key": "instrument",
        "family": "Instrument Sans",
        "query": "Instrument+Sans:ital,wght@0,400..700;1,400..700",
        "faces": [("normal", "400 700"), ("italic", "400 700")],
        "pin": {},
    },
]

LATIN_RANGE = "U+0000-00FF"  # the block Google labels "latin"


def fetch(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60
    ).read()


def shrink(src_path, out_path, pin):
    """Pin the axes we never vary, drop the glyphs we never render, re-pack as woff2.

    Order matters: instancing first removes the variation deltas for the pinned
    axes, so the subsetter has less to carry.
    """
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    from fontTools import subset

    font = TTFont(src_path)

    if pin and "fvar" in font:
        axes = {a.axisTag for a in font["fvar"].axes}
        usable = {k: v for k, v in pin.items() if k in axes}
        if usable:
            font = instancer.instantiateVariableFont(font, usable, inplace=False, updateFontNames=False)

    # fontTools' gvar subsetter indexes `variations` by every retained glyph, and
    # Google's builds omit entries for glyphs with no deltas (.notdef among them),
    # which blows up on a lazy lookup. Materialise the table with empty fallbacks.
    if "gvar" in font:
        gvar = font["gvar"]
        materialised = {}
        for glyph in font.getGlyphOrder():
            try:
                materialised[glyph] = gvar.variations[glyph]
            except KeyError:
                materialised[glyph] = []
        gvar.variations = materialised

    opts = subset.Options()
    opts.layout_features = ["kern", "liga", "calt", "ccmp", "locl", "mark", "mkmk", "frac"]
    opts.hinting = False
    opts.desubroutinize = True
    opts.name_IDs = [1, 2, 3, 4, 5, 6, 16, 17]
    opts.notdef_outline = True
    opts.drop_tables += ["DSIG"]
    opts.flavor = "woff2"

    subsetter = subset.Subsetter(options=opts)
    subsetter.populate(unicodes=subset.parse_unicodes(UNICODES))
    subsetter.subset(font)

    font.flavor = "woff2"
    font.save(out_path)
    font.close()


def main():
    os.makedirs(FONTDIR, exist_ok=True)
    for stale in os.listdir(FONTDIR):
        if stale.endswith(".woff2"):
            os.remove(os.path.join(FONTDIR, stale))

    css_blocks = []
    for fam in FAMILIES:
        url = f"https://fonts.googleapis.com/css2?family={fam['query']}&display=swap"
        css = fetch(url).decode()

        # Google emits one @font-face per (style, unicode subset). We want the
        # "latin" subset of each style — our own subsetting handles the rest.
        faces = re.findall(r"@font-face\s*\{(.+?)\}", css, re.S)
        wanted = {}
        for block in faces:
            if LATIN_RANGE not in block:
                continue
            style = "italic" if re.search(r"font-style:\s*italic", block) else "normal"
            m = re.search(r"url\((https://[^)]+\.woff2)\)", block)
            if m and style not in wanted:
                wanted[style] = m.group(1)

        for style, weight in fam["faces"]:
            src = wanted.get(style)
            if not src:
                sys.exit(f"could not find the latin {style} face for {fam['family']}")

            raw = os.path.join(FONTDIR, f".{fam['key']}-{style}.src.woff2")
            with open(raw, "wb") as fh:
                fh.write(fetch(src))

            out = os.path.join(FONTDIR, f"{fam['key']}-{style}.woff2")
            shrink(raw, out, fam["pin"])
            os.remove(raw)

            kb = os.path.getsize(out) / 1024
            print(f"  {fam['family']:22} {style:7} {kb:6.1f} KB")

            css_blocks.append(
                "@font-face {\n"
                f"  font-family: '{fam['family']}';\n"
                f"  font-style: {style};\n"
                f"  font-weight: {weight};\n"
                "  font-display: swap;\n"
                f"  src: url(../fonts/{fam['key']}-{style}.woff2) format('woff2');\n"
                "}"
            )

    with open(CSSOUT, "w") as fh:
        fh.write(
            "/* Self-hosted, subset webfonts. Generated by tools/fetch_fonts.py.\n"
            "   Latin + smart punctuation only. No runtime third-party requests. */\n"
            + "\n".join(css_blocks)
            + "\n"
        )
    total = sum(
        os.path.getsize(os.path.join(FONTDIR, f))
        for f in os.listdir(FONTDIR)
        if f.endswith(".woff2")
    )
    print(f"  total {total/1024:.1f} KB -> {CSSOUT}")


if __name__ == "__main__":
    main()
