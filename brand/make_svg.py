#!/usr/bin/env python3
"""«Ö» logotipining vektor (SVG) nusxasi.

Harf konturlari şriftdan olinadi va ikkita kiçik kontur (umlaut nuqtalari)
alohida rangga ajratiladi — natijada SVG hеç qanday şriftga boğliq bölmaydi.
"""
from __future__ import annotations

from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTCollection

OUT = Path(__file__).parent
FONT = "/System/Library/Fonts/Avenir Next.ttc"
FACE = 2            # Avenir Next Demi Bold

INK_BG, LETTER, MARK = "#0E4D3F", "#F5F2EA", "#E9B949"
TIGHTEN = 0.02      # umlautni harfga yaqinlaştiriş ulusi (rasmlar bilan bir xil)


def contours(glyph_set, name):
    """Glifni alohida konturlarga ajratadi."""
    rec = RecordingPen()
    glyph_set[name].draw(rec)
    out, cur = [], []
    for op, args in rec.value:
        if op == "moveTo" and cur:
            out.append(cur)
            cur = []
        cur.append((op, args))
    if cur:
        out.append(cur)
    return out


def bbox(contour):
    xs, ys = [], []
    for _, args in contour:
        for pt in args:
            if isinstance(pt, tuple):
                xs.append(pt[0]); ys.append(pt[1])
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)


def to_path(contour, dy=0.0):
    pen = SVGPathPen(None)
    for op, args in contour:
        shifted = tuple((p[0], p[1] + dy) if isinstance(p, tuple) else p for p in args)
        getattr(pen, op)(*shifted)
    pen.closePath()
    return pen.getCommands()


def main() -> None:
    font = TTCollection(FONT).fonts[FACE]
    gs = font.getGlyphSet()
    upem = font["head"].unitsPerEm
    name = font.getBestCmap()[ord("Ö")]

    parts = contours(gs, name)
    boxes = [bbox(c) for c in parts]
    top = max(b[3] for b in boxes)
    # umlaut nuqtalari — eng yuqorida turgan kiçik konturlar
    dots = [i for i, b in enumerate(boxes)
            if b[1] > top * 0.55 and (b[2] - b[0]) < upem * 0.25]
    base = [i for i in range(len(parts)) if i not in dots]
    if len(dots) != 2:
        raise SystemExit(f"umlaut nuqtalari topilmadi (topilgani: {len(dots)})")

    shift = -upem * TIGHTEN
    base_d = " ".join(to_path(parts[i]) for i in base)
    dots_d = " ".join(to_path(parts[i], shift) for i in dots)

    xs = [b[0] for b in boxes] + [b[2] for b in boxes]
    ys = [b[1] + (shift if i in dots else 0) for i, b in enumerate(boxes)]
    ys += [b[3] + (shift if i in dots else 0) for i, b in enumerate(boxes)]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0, y1 - y0

    pad = max(w, h) * 0.35
    side = max(w, h) + pad * 2
    ox = x0 - (side - w) / 2
    oy = y0 - (side - h) / 2

    def svg(bg: str | None, letter: str, mark: str, label: str) -> str:
        rect = (f'  <rect width="{side:.0f}" height="{side:.0f}" fill="{bg}"/>\n'
                if bg else "")
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side:.0f} {side:.0f}" role="img" aria-label="Alifbo28">
  <title>Alifbo28 — {label}</title>
{rect}  <g transform="translate({-ox:.0f} {oy + side:.0f}) scale(1 -1)">
    <path fill="{letter}" fill-rule="evenodd" d="{base_d}"/>
    <path fill="{mark}" d="{dots_d}"/>
  </g>
</svg>
'''

    (OUT / "logo.svg").write_text(svg(INK_BG, LETTER, MARK, "asosiy"), encoding="utf-8")
    (OUT / "logo-shaffof.svg").write_text(svg(None, LETTER, MARK, "şaffof fon"), encoding="utf-8")
    (OUT / "logo-oq-fon.svg").write_text(svg("#FFFFFF", "#132A25", "#B07D1B", "oq fon"),
                                         encoding="utf-8")
    for f in ("logo.svg", "logo-shaffof.svg", "logo-oq-fon.svg"):
        print(f"  {f:22} {(OUT / f).stat().st_size} bayt")


if __name__ == "__main__":
    main()
