#!/usr/bin/env python3
"""Render the home-screen icons. iOS masks them itself, so they are full-bleed."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "icons"
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

BG = (179, 69, 47)
INK = (250, 245, 238)


def render(size, glyph_ratio):
    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, int(size * glyph_ratio))
    box = draw.textbbox((0, 0), "拼", font=font)
    draw.text(
        ((size - (box[2] - box[0])) / 2 - box[0], (size - (box[3] - box[1])) / 2 - box[1]),
        "拼",
        font=font,
        fill=INK,
    )
    return img


for size in (180, 192, 512):
    render(size, 0.62).save(OUT / f"icon-{size}.png")
# Maskable icons get cropped to a circle, so keep the glyph well inside.
render(512, 0.44).save(OUT / "icon-maskable-512.png")
print("\n".join(f"{p.name} {p.stat().st_size}B" for p in sorted(OUT.glob("*.png"))))
