#!/usr/bin/env python3
"""Alifbo28 brend tasvirlarini yaratadi.

Ğoya: yangi alifboda ösgan narsa — DIAKRITIK BELGI. Şu sababli asos harf
sokin rangda, belgining özi esa yorqin rangda beriladi. Harfning qaysi
piksellari belgiga tegişli ekanini «Ö» va «O» niqoblarini ayirib topamiz —
şunda hеç narsa qölda joylaştirilmaydi.

Işga tuşiriş:  python brand/make_logo.py
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).parent
SS = 4                      # supersampling — silliq çekkalar uçun

# ─── palitra ──────────────────────────────────────────────────────────────
INK_BG    = (14, 77, 63)        # #0E4D3F  çuqur köki-yaşil — asosiy fon
LETTER    = (245, 242, 234)     # #F5F2EA  iliq oq — asos harf
MARK      = (233, 185, 73)      # #E9B949  oltin — diakritik belgi

PAPER     = (245, 242, 234)     # #F5F2EA  oçiq fon
PAPER_INK = (19, 42, 37)        # #132A25  matn
PAPER_ACC = (14, 107, 88)       # #0E6B58  yaşil urğu
PAPER_GLD = (176, 125, 27)      # #B07D1B  oçiq fonda öqiladigan oltin
MUTED     = (122, 132, 126)     # #7A847E

FONT = "/System/Library/Fonts/Avenir Next.ttc"
IDX = {"bold": 0, "demi": 2, "medium": 5, "regular": 7}


def face(style: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size, index=IDX[style])


def split_glyph(char: str, base: str, style: str, size: int):
    """Harfni «asos» va «diakritik belgi» niqoblariga ajratadi.

    Asos harf tögri joyga tuşişi uçun ikkala niqobning bbox i böyiça
    tekislanadi (yuqoridagi belgi uçun pastki qirra, pastdagisi uçun
    yuqorigi qirra mos keltiriladi). Söngra asos turgan joy belgidan
    butunlay öçiriladi — aks holda antialias qirralari boşqa rangda
    yaltirab qolardi.
    """
    from PIL import ImageChops

    f = face(style, size)

    def mask_of(text: str) -> Image.Image:
        m = f.getmask(text, mode="L")
        return Image.frombytes("L", m.size, bytes(m))

    full, plain = mask_of(char), mask_of(base)
    fb, pb = full.getbbox(), plain.getbbox()
    if fb is None or pb is None:
        return full, full, Image.new("L", full.size, 0)

    above = char in "ÖöĞğ"
    dx = fb[0] - pb[0]
    dy = (fb[3] - pb[3]) if above else (fb[1] - pb[1])

    canvas = Image.new("L", full.size, 0)
    canvas.paste(plain, (dx, dy))

    mark = ImageChops.subtract(full, canvas)
    # Asos harf hududini QAT'IY öçiramiz: ikki niqob subpiksel darajada
    # farq qilgani uçun oddiy ayirma qirralarda ingiçka qoldiq qoldiradi.
    hard = canvas.point(lambda v: 255 if v > 6 else 0).filter(ImageFilter.MaxFilter(3))
    mark.paste(0, mask=hard)
    return full, canvas, mark


def arrow(d: ImageDraw.ImageDraw, x: float, y: float, w: float, color,
          weight: float = 0.13) -> float:
    """Gorizontal strelka çizadi va egallagan enini qaytaradi.

    Avenir Next da «→» (U+2192) yöq — şu sababli şakl sifatida çizamiz.
    """
    t = max(w * weight, 1)
    head = w * 0.42
    d.line([(x, y), (x + w - head * 0.6, y)], fill=color, width=int(t))
    d.polygon([(x + w, y), (x + w - head, y - head * 0.52),
               (x + w - head, y + head * 0.52)], fill=color)
    return w


def run(d: ImageDraw.ImageDraw, x: float, y: float, parts, font, colors):
    """[matn, None (strelka), matn] ketma-ketligini çizadi; umumiy enini qaytaradi."""
    gap = font.size * 0.34
    total = 0.0
    for part in parts:
        total += (d.textlength(part, font=font) if part else font.size * 0.9) + gap
    total -= gap
    cx = x
    for part in parts:
        if part is None:
            aw = font.size * 0.9
            arrow(d, cx, y + font.size * 0.42, aw, colors[1])
            cx += aw + gap
        else:
            d.text((cx, y), part, font=font, fill=colors[0])
            cx += d.textlength(part, font=font) + gap
    return total


def tinted(mask: Image.Image, color) -> Image.Image:
    layer = Image.new("RGBA", mask.size, color + (0,))
    layer.putalpha(mask)
    return layer


def logo_layer(glyph: int, letter, mark_color, tighten: float = 0.02) -> Image.Image:
    """«Ö» logotip belgisi — asos oq, umlaut esa urğu rangida.

    `tighten` — umlautni harfga biroz yaqinlaştiradi: matn uçun möljallangan
    standart boşliq logotipda katta körinadi.
    """
    full, plain, mark = split_glyph("Ö", "O", "demi", glyph)
    shifted = Image.new("L", mark.size, 0)
    shifted.paste(mark, (0, int(glyph * tighten)))

    layer = Image.new("RGBA", full.size, (0, 0, 0, 0))
    layer.alpha_composite(tinted(plain, letter))
    layer.alpha_composite(tinted(shifted, mark_color))
    return layer.crop(layer.getbbox())


# ─── 1. avatar ────────────────────────────────────────────────────────────
def avatar(size: int = 512, ring: bool = False) -> Image.Image:
    S = size * SS
    img = Image.new("RGBA", (S, S), INK_BG + (255,))
    layer = logo_layer(int(S * 0.74), LETTER, MARK)
    x = (S - layer.width) // 2
    y = int((S - layer.height) / 2 - S * 0.008)      # doirada optik markaz
    img.alpha_composite(layer, (x, y))
    return img.resize((size, size), Image.LANCZOS)


# ─── 2. törtlik: Ö Ğ Ş Ç ──────────────────────────────────────────────────
def letters(w: int = 1080, h: int = 1080) -> Image.Image:
    W, H = w * SS, h * SS
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(img)

    title = face("demi", int(W * 0.042))
    t = "Yangi özbek alifbosi"
    d.text(((W - d.textlength(t, font=title)) / 2, H * 0.058), t, font=title, fill=PAPER_INK)

    pairs = [("Ö", "O", ["Oʻ", None, "Ö"]), ("Ğ", "G", ["Gʻ", None, "Ğ"]),
             ("Ş", "S", ["Sh", None, "Ş"]), ("Ç", "C", ["Ch", None, "Ç"])]

    grid_top, grid_bot = H * 0.17, H * 0.88
    col_w, row_h = W / 2, (grid_bot - grid_top) / 2
    glyph = int(row_h * 0.52)
    small = face("medium", int(W * 0.030))

    for i, (new, base, parts) in enumerate(pairs):
        cx = col_w * (0.5 + i % 2)
        cy = grid_top + row_h * (i // 2)

        full, plain, mark = split_glyph(new, base, "demi", glyph)
        layer = Image.new("RGBA", full.size, (0, 0, 0, 0))
        layer.alpha_composite(tinted(plain, PAPER_INK))
        layer.alpha_composite(tinted(mark, PAPER_GLD))
        layer = layer.crop(layer.getbbox())
        img.alpha_composite(layer, (int(cx - layer.width / 2),
                                    int(cy + row_h * 0.32 - layer.height / 2)))

        width = run(ImageDraw.Draw(Image.new("RGBA", (1, 1))), 0, 0, parts, small,
                    (MUTED, MUTED))
        run(d, cx - width / 2, cy + row_h * 0.66, parts, small, (MUTED, PAPER_GLD))

    sub = face("medium", int(W * 0.026))
    s2 = "28 harf · @Alifbo28Bot"
    d.text(((W - d.textlength(s2, font=sub)) / 2, H * 0.925), s2, font=sub, fill=PAPER_ACC)

    return img.resize((w, h), Image.LANCZOS)


# ─── 3. keng muqova ───────────────────────────────────────────────────────
def cover(w: int = 1280, h: int = 720) -> Image.Image:
    S = SS
    W, H = w * S, h * S
    img = Image.new("RGBA", (W, H), INK_BG + (255,))
    d = ImageDraw.Draw(img)

    # çap tomonda katta Ö
    layer = logo_layer(int(H * 0.62), LETTER, MARK)
    img.alpha_composite(layer, (int(W * 0.10), int((H - layer.height) / 2)))

    # öng tomonda matn
    x = int(W * 0.42)
    name = face("demi", int(H * 0.115))
    d.text((x, H * 0.24), "Alifbo28", font=name, fill=LETTER)

    tag = face("medium", int(H * 0.048))
    d.text((x, H * 0.40), "Yangi özbek alifbosiga ötkazgiç", font=tag, fill=(168, 196, 186))

    mono = face("medium", int(H * 0.052))
    cx = float(x)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for old, new in (("Oʻ", "Ö"), ("Gʻ", "Ğ"), ("Sh", "Ş"), ("Ch", "Ç")):
        parts = [old, None, new]
        width = run(probe, 0, 0, parts, mono, (MARK, MARK))
        run(d, cx, H * 0.52, parts, mono, (MARK, MARK))
        cx += width + mono.size * 1.05

    bot = face("demi", int(H * 0.050))
    d.text((x, H * 0.66), "@Alifbo28Bot", font=bot, fill=LETTER)

    return img.resize((w, h), Image.LANCZOS)


def main() -> None:
    a = avatar(512)
    a.save(OUT / "avatar-512.png")
    a.resize((256, 256), Image.LANCZOS).save(OUT / "avatar-256.png")
    a.resize((128, 128), Image.LANCZOS).save(OUT / "avatar-128.png")
    a.resize((40, 40), Image.LANCZOS).save(OUT / "avatar-40-tekshiruv.png")
    letters().save(OUT / "harflar-1080.png")
    cover().save(OUT / "muqova-1280x720.png")
    for p in sorted(OUT.glob("*.png")):
        print(f"  {p.name:28} {p.stat().st_size // 1024:>4} KB")


if __name__ == "__main__":
    main()
