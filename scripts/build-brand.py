"""Builds DoubleTake's app icon from design/tokens.json: resources/brand/doubletake.ico and icon-<size>.png.

    python scripts/build-brand.py

The geometry and colours are the tokens' (design/SPEC.md section 13); nothing here is typed twice. The wordmark,
banners and installer images of that section are added by D00 T01 section 9 of the plan.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SIZES = (16, 20, 24, 32, 40, 48, 64, 256)
SCALE = 8  # each size is drawn this many times larger and reduced, so edges are smooth


def ring_stroke(size, strokes):
    """The ring stroke, on the 256 grid, for an icon of `size` pixels: thicker as the icon gets smaller."""
    if size >= 48:
        return strokes["48"]
    if size >= 24:
        return strokes["24"]
    return strokes["16"]


def draw_icon(size, tokens):
    icon, color = tokens["icon"], tokens["color"]
    side = size * SCALE
    unit = side / icon["grid"]
    tile, rings = icon["tile"], icon["rings"]
    radius, cy = rings["r"] * unit, rings["cy"] * unit
    centres = [cx * unit for cx in rings["cx"]]

    def disc(cx):
        mask = Image.new("L", (side, side), 0)
        ImageDraw.Draw(mask).ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=255)
        return mask

    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (tile["x"] * unit, tile["y"] * unit, (tile["x"] + tile["w"]) * unit, (tile["y"] + tile["h"]) * unit),
        radius=tile["rx"] * unit, fill=color[tile["fill"]])
    overlap = ImageChops.multiply(disc(centres[0]), disc(centres[1]))
    image.paste(Image.new("RGBA", (side, side), color[icon["overlap"]["fill"]]), (0, 0), overlap)
    stroke = ring_stroke(size, icon["ringStroke"]) * unit
    for cx in centres:
        outer = radius + stroke / 2
        draw.ellipse((cx - outer, cy - outer, cx + outer, cy + outer), outline=color[rings["stroke"]],
                     width=round(stroke))
    return image.resize((size, size), Image.Resampling.LANCZOS)


def main():
    tokens = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
    out = ROOT / "resources" / "brand"
    out.mkdir(parents=True, exist_ok=True)
    images = {size: draw_icon(size, tokens) for size in SIZES}
    for size, image in images.items():
        image.save(out / f"icon-{size}.png")
    largest = images[max(SIZES)]
    largest.save(out / "doubletake.ico", format="ICO", sizes=[(s, s) for s in SIZES],
                 append_images=[images[s] for s in SIZES if s != max(SIZES)])
    print(f"wrote {out / 'doubletake.ico'} ({len(SIZES)} sizes) and {len(SIZES)} PNGs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
