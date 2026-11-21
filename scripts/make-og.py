#!/usr/bin/env python3
"""Generate the 1200x630 social card in the site's XP-olive style.

Run from the repository root:  python3 scripts/make-og.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "og.png"
HEADSHOT = ROOT / "assets" / "img" / "headshot.jpg"
FONT_BOLD = "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/liberation/LiberationSans-Regular.ttf"

W, H = 1200, 630
FACE = (236, 233, 216)
FRAME = (92, 116, 64)
FRAME_DARK = (47, 74, 34)
TEXT = (26, 26, 26)
MUTED = (74, 74, 58)
LINK = (31, 78, 121)


def vgrad(width, height, stops):
    """Vertical gradient from a list of (offset, rgb)."""
    strip = Image.new("RGB", (1, height))
    px = strip.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        for i in range(len(stops) - 1):
            o0, c0 = stops[i]
            o1, c1 = stops[i + 1]
            if o0 <= t <= o1:
                f = (t - o0) / (o1 - o0) if o1 > o0 else 0
                px[0, y] = tuple(round(a + (b - a) * f) for a, b in zip(c0, c1))
                break
        else:
            px[0, y] = stops[-1][1]
    return strip.resize((width, height), Image.Resampling.BILINEAR)


def top_rounded_mask(size, radius):
    w, h = size
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    d.rectangle((0, h // 2, w, h), fill=255)
    return mask


def main():
    bg = vgrad(W, H, [(0, (195, 209, 174)), (0.5, (164, 183, 139)), (1, (95, 114, 68))])
    img = bg.convert("RGB")

    # Soft desktop highlight
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((-260, 250, W + 260, H + 420), fill=60)
    img = Image.composite(Image.new("RGB", (W, H), (211, 221, 192)), img, glow.point(lambda v: int(v * 0.55)))

    d = ImageDraw.Draw(img)

    # Window
    wx, wy, ww, wh = 66, 54, 1068, 512
    d.rounded_rectangle((wx + 10, wy + 12, wx + ww + 10, wy + wh + 12), radius=16, fill=(52, 64, 36))
    d.rounded_rectangle((wx, wy, wx + ww, wy + wh), radius=16, fill=FRAME, outline=FRAME_DARK, width=3)
    inner = (wx + 5, wy + 5, wx + ww - 5, wy + wh - 5)
    d.rounded_rectangle(inner, radius=11, fill=FACE)

    # Title bar
    tb = 62
    titlebar = vgrad(ww - 10, tb, [
        (0, (163, 182, 129)), (0.09, (147, 168, 114)), (0.34, (111, 133, 80)),
        (0.52, (93, 114, 68)), (0.62, (85, 106, 62)), (1, (64, 84, 42)),
    ])
    mask = top_rounded_mask((ww - 10, tb), 11)
    img.paste(titlebar, (wx + 5, wy + 5), mask)
    d.rectangle((wx + 5, wy + 5 + tb, wx + ww - 5, wy + 5 + tb), fill=(47, 74, 34))

    # Title bar icon: tiny monitor
    ix, iy = wx + 26, wy + 24
    d.rounded_rectangle((ix, iy, ix + 30, iy + 22), radius=3, fill=FACE, outline=(79, 101, 54), width=2)
    d.rectangle((ix + 4, iy + 4, ix + 26, iy + 16), fill=(125, 144, 96))
    d.rectangle((ix + 12, iy + 24, ix + 18, iy + 28), fill=(185, 180, 161))
    d.rectangle((ix + 5, iy + 28, ix + 25, iy + 32), fill=FACE, outline=(107, 122, 85), width=1)

    f_title = ImageFont.truetype(FONT_BOLD, 24)
    d.text((wx + 74, wy + 24), "Alex Ferriroli - Software & Systems Engineer", font=f_title, fill=(255, 255, 255))

    # Task pane
    tx, ty, tw, th = wx + 26, wy + 92, 252, 380
    pane = vgrad(tw, th, [(0, (247, 245, 234)), (1, (233, 230, 214))])
    img.paste(pane, (tx, ty))
    d.rectangle((tx, ty, tx + tw, ty + th), outline=(185, 180, 161), width=1)
    d.rectangle((tx, ty, tx + tw, ty + 34), fill=(95, 116, 68))
    d.text((tx + 12, ty + 8), "Places", font=ImageFont.truetype(FONT_BOLD, 15), fill=(255, 255, 255))

    f_nav = ImageFont.truetype(FONT_REG, 18)
    for i, label in enumerate(["CV", "About", "Contact", "GitHub"]):
        ny = ty + 54 + i * 34
        d.rectangle((tx + 16, ny + 4, tx + 30, ny + 18), fill=(231, 201, 119), outline=(138, 116, 52))
        d.text((tx + 42, ny), label, font=f_nav, fill=LINK)

    # Right hand content
    cx = tx + tw + 46
    f_h1 = ImageFont.truetype(FONT_BOLD, 56)
    f_role = ImageFont.truetype(FONT_REG, 26)
    f_body = ImageFont.truetype(FONT_REG, 20)
    d.text((cx, wy + 108), "Alex Ferriroli", font=f_h1, fill=TEXT)
    d.text((cx, wy + 180), "Software & Systems Engineer", font=f_role, fill=MUTED)
    d.text((cx, wy + 232), "alex@ferriroli.com", font=f_body, fill=LINK)
    d.text((cx, wy + 266), "London & South Norfolk", font=f_body, fill=MUTED)

    # Photo, album style
    phx, phy, phw = wx + ww - 246, wy + 112, 198
    head = Image.open(HEADSHOT).convert("RGB")
    phh = round(head.height * phw / head.width)
    head = head.resize((phw, phh), Image.Resampling.LANCZOS)
    d.rectangle((phx - 8, phy - 8, phx + phw + 8, phy + phh + 30), fill=(255, 255, 255), outline=(138, 133, 115))
    img.paste(head, (phx, phy))
    d.text((phx + phw // 2, phy + phh + 8), "Alex Ferriroli", font=ImageFont.truetype(FONT_REG, 14), fill=MUTED, anchor="ma")

    # Status bar
    sy = wy + wh - 42
    d.line((wx + 12, sy, wx + ww - 12, sy), fill=(169, 164, 143))
    f_small = ImageFont.truetype(FONT_REG, 15)
    cells = ["alex@ferriroli.com", "London & South Norfolk", "github.com/gizmoguy100"]
    x = wx + 18
    for cell in cells:
        tw_cell = d.textlength(cell, font=f_small)
        d.rectangle((x, sy + 8, x + tw_cell + 16, sy + 32), fill=(242, 240, 228), outline=(185, 180, 161))
        d.text((x + 8, sy + 12), cell, font=f_small, fill=MUTED)
        x += tw_cell + 24

    img.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
