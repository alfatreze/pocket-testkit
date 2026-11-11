#!/usr/bin/env python3
"""docs/img/preview.png: the three carriers side by side, each at its minimum (160x144 screen) and maximum (800x480 screen) density, filled to capacity.
Same pixel size on every screen, so the block grows with the screen. Block crops, pixel-exact at 1x, bottom aligned, so the size difference between the two screens is real. Random payloads (a full code looks like noise).
   python3 examples/make_preview.py      needs numpy, Pillow, opencv-python"""
import os, random, sys, warnings
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
import tpg, qr_tier
warnings.simplefilter("ignore")
K, C, M, W = (0, 0, 0), (85, 255, 255), (255, 85, 255), (255, 255, 255)
SMALL, BIG = (160, 144), (800, 480)

def font(n):
    try: return ImageFont.load_default(size=n)
    except TypeError: return ImageFont.load_default()

def grid_tile(mode, size):
    cap = tpg.capacity(mode, size); rnd = np.random.default_rng(5); r = bytes(rnd.integers(0, 256, cap, dtype=np.uint8))
    x0, y0, px = tpg.block(cap, mode, size)
    img = Image.fromarray(tpg.to_rgb(tpg.encode(r, mode, size))).crop((x0, y0, x0 + px, y0 + px)); return img, cap

def qr_tile(size):
    s = min(size)
    v = max(v for v in range(1, 39) if (4 * v + 25) * 2 <= s)
    import segno.consts as Cn
    cap = (8 * sum(e.num_blocks * e.num_data for e in Cn.ECC[v][Cn.ERROR_LEVEL_L]) - (12 if v < 10 else 20)) // 8
    rnd = random.Random(v); text = "".join(rnd.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_") for _ in range(cap))
    scr = qr_tier.screen(text, W=size[0], H=size[1], density="max", allow_max=True)
    a = np.asarray(scr.convert("L")); ys, xs = np.nonzero(a > 0)
    return scr.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)), cap

def main():
    cols = [("ROBUST GRID", lambda sz: grid_tile(tpg.MODE_R, sz)), ("LOSSLESS GRID", lambda sz: grid_tile(tpg.MODE_L, sz)), ("QR CODE", qr_tile)]
    tiles = [[fn(SMALL), fn(BIG)] for _, fn in cols]                          # [(image, capacity)] min, max per carrier; pixel-exact, 1x
    gap_in, gap_out, pad, base_h = 28, 70, 40, 500
    width = pad * 2 + sum(t[0][0].width + gap_in + t[1][0].width for t in tiles) + gap_out * 2
    img = Image.new("RGB", (width, base_h + 200), K); d = ImageDraw.Draw(img)
    x = pad
    for (name, _), pair, size in zip(cols, tiles, (None, None, None)):
        x_start = x
        for (tile, cap), (label, sz) in zip(pair, (("MIN", SMALL), ("MAX", BIG))):
            y = 40 + base_h - tile.height                                       # bottom aligned: the size difference is the point
            img.paste(tile, (x, y)); d.rectangle((x - 2, y - 2, x + tile.width + 1, y + tile.height + 1), outline=(90, 96, 110))
            d.text((x, 40 + base_h + 14), label, fill=M, font=font(18))
            d.text((x, 40 + base_h + 38), "%dx%d" % sz, fill=C, font=font(18))
            d.text((x, 40 + base_h + 62), "%s B" % format(cap, ","), fill=C, font=font(18))
            x += tile.width + gap_in
        x_end = x - gap_in
        d.text((x_start, 40 + base_h + 100), name, fill=W, font=font(28))
        if name == "QR CODE": d.text((x_start, 40 + base_h + 138), "above 271 B: screenshots only, not a phone photo", fill=(140, 146, 160), font=font(16))
        x = x_end + gap_out
    for xx in range(img.width): img.putpixel((xx, 0), M if (xx // 4) % 2 else C); img.putpixel((xx, img.height - 1), C if (xx // 4) % 2 else M)
    out = os.path.join(ROOT, "docs", "img", "preview.png"); img.save(out); print(out, img.size)
if __name__ == "__main__": main()
