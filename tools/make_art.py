"""Draws the app icon and the launch (splash) screen for 아침 브리핑.

Run:  python3 tools/make_art.py
Writes every Android density into android/app/src/main/res and a preview into tools/preview/.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "android", "app", "src", "main", "res")
PREVIEW = os.path.join(ROOT, "tools", "preview")
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
KR = 1  # face index of the Korean family inside the .ttc

NAVY = (15, 24, 48)
NAVY_2 = (36, 52, 106)
INK = (244, 246, 251)
MUTED = (163, 173, 208)
ONAIR = (255, 74, 61)


def font(path, size):
    return ImageFont.truetype(path, size, index=KR)


def gradient(w, h):
    """Diagonal studio gradient with a soft light in the upper right."""
    img = Image.new("RGB", (w, h), NAVY)
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = min(1.0, max(0.0, (y / h) * 0.75 + (1 - x / w) * 0.25))
            t = t ** 0.9
            px[x, y] = tuple(int(NAVY_2[i] + (NAVY[i] - NAVY_2[i]) * min(1, t / 0.62)) for i in range(3))
    glow = Image.new("L", (w, h), 0)
    ImageDraw.Draw(glow).ellipse((w * 0.45, -h * 0.35, w * 1.45, h * 0.45), fill=46)
    glow = glow.filter(ImageFilter.GaussianBlur(min(w, h) * 0.12))
    img.paste(Image.new("RGB", (w, h), (255, 255, 255)), (0, 0), glow)
    return img


def lamp_at(cx, cy, width, height):
    """Where the red lamp sits for a mark centred on (cx, cy): lamp + bars together are centred."""
    r = height * 0.11
    shift = 1.8 * r                      # half of (lamp + gap) so the whole mark is optically centred
    return cx + shift - width / 2 - r * 2.6, cy, r, shift


def wave(draw, cx, cy, width, height, bars=17, color=INK, lamp=True):
    """The broadcast waveform: rounded bars under a sine envelope, red ON AIR lamp at the front."""
    lx, ly, r, shift = lamp_at(cx, cy, width, height)
    if lamp:
        cx += shift
    gap = width / bars
    bw = gap * 0.52
    for i in range(bars):
        p = i / (bars - 1)
        env = math.sin(math.pi * (0.08 + 0.84 * p)) ** 0.9
        wob = 0.62 + 0.38 * abs(math.sin(i * 1.7 + 0.6))
        h = max(bw, height * env * wob)
        x = cx - width / 2 + i * gap + (gap - bw) / 2
        draw.rounded_rectangle((x, cy - h / 2, x + bw, cy + h / 2), radius=bw / 2, fill=color)
    if lamp:
        draw.ellipse((lx - r, ly - r, lx + r, ly + r), fill=ONAIR)


def lamp_glow(img, cx, cy, r):
    g = Image.new("L", img.size, 0)
    ImageDraw.Draw(g).ellipse((cx - r * 3, cy - r * 3, cx + r * 3, cy + r * 3), fill=120)
    g = g.filter(ImageFilter.GaussianBlur(r * 1.6))
    img.paste(Image.new("RGB", img.size, ONAIR), (0, 0), g)


def splash(w, h):
    img = gradient(w, h)
    s = min(w, h)
    cx, cy = w / 2, h / 2 - s * 0.06
    ww, wh = s * 0.46, s * 0.17
    lx, ly, lr, _ = lamp_at(cx, cy, ww, wh)
    lamp_glow(img, lx, ly, lr)
    d = ImageDraw.Draw(img)
    wave(d, cx, cy, ww, wh)
    title = font(BOLD, int(s * 0.085))
    sub = font(REG, int(s * 0.034))
    t = "아침 브리핑"
    tw = d.textlength(t, font=title)
    d.text((cx - tw / 2, cy + wh * 0.85), t, font=title, fill=INK)
    st = "3시간마다 새로 읽어 주는 뉴스"
    sw = d.textlength(st, font=sub)
    d.text((cx - sw / 2, cy + wh * 0.85 + s * 0.125), st, font=sub, fill=MUTED)
    return img


def icon_full(size, round_mask=False):
    """Legacy launcher icon: rounded studio tile with the waveform."""
    big = size * 4
    img = gradient(big, big)
    d = ImageDraw.Draw(img)
    lx, ly, lr, _ = lamp_at(big / 2, big / 2, big * 0.5, big * 0.34)
    lamp_glow(img, lx, ly, lr)
    d = ImageDraw.Draw(img)
    wave(d, big / 2, big / 2, big * 0.5, big * 0.34, bars=9)
    mask = Image.new("L", (big, big), 0)
    if round_mask:
        ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    else:
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, big - 1, big - 1), radius=big * 0.22, fill=255)
    out = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out.resize((size, size), Image.LANCZOS)


def icon_foreground(size):
    """Adaptive-icon foreground (108dp canvas, art kept inside the 66dp safe zone)."""
    big = size * 4
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    safe = big * 66 / 108
    wave(d, big / 2, big / 2, safe * 0.7, safe * 0.48, bars=9)
    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(PREVIEW, exist_ok=True)
    # splash screens, every density/orientation the template ships
    for folder in sorted(os.listdir(RES)):
        path = os.path.join(RES, folder, "splash.png")
        if os.path.exists(path):
            w, h = Image.open(path).size
            splash(w, h).save(path, optimize=True)
    # launcher icons
    for folder in sorted(os.listdir(RES)):
        if not folder.startswith("mipmap-") or folder.endswith("v26"):
            continue
        base = os.path.join(RES, folder)
        n = Image.open(os.path.join(base, "ic_launcher.png")).size[0]
        icon_full(n).save(os.path.join(base, "ic_launcher.png"))
        icon_full(n, round_mask=True).save(os.path.join(base, "ic_launcher_round.png"))
        fg = Image.open(os.path.join(base, "ic_launcher_foreground.png")).size[0]
        icon_foreground(fg).save(os.path.join(base, "ic_launcher_foreground.png"))
    # Android 12+ system splash icon (inside a 160dp circle on a 240dp canvas, xxxhdpi = 960px)
    sp = Image.new("RGBA", (960, 960), (0, 0, 0, 0))
    wave(ImageDraw.Draw(sp), 480, 480, 360, 240, bars=9)
    sp.save(os.path.join(RES, "drawable-nodpi", "splash_icon.png"))
    # previews
    splash(1080, 1920).save(os.path.join(PREVIEW, "splash.png"))
    icon_full(512).save(os.path.join(PREVIEW, "icon.png"))


if __name__ == "__main__":
    main()
