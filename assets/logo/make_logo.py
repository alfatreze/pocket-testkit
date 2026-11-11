#!/usr/bin/env python3
"""Pixel logo in the four CGA colours (palette 1, high intensity). python3 assets/logo/make_logo.py  -> logo.png, banner.png in this folder.
A handheld whose screen shows the colour grid; the banner adds the name in a 4x5 pixel font. Needs Pillow."""
import os, random
from PIL import Image
K, C, M, W = (0, 0, 0), (85, 255, 255), (255, 85, 255), (255, 255, 255)
HERE = os.path.dirname(os.path.abspath(__file__))

FONT = {
"P": ["1110", "1001", "1110", "1000", "1000"], "O": ["0110", "1001", "1001", "1001", "0110"],
"C": ["0111", "1000", "1000", "1000", "0111"], "K": ["1001", "1010", "1100", "1010", "1001"],
"E": ["1111", "1000", "1110", "1000", "1111"], "T": ["1111", "0100", "0100", "0100", "0100"],
"S": ["0111", "1000", "0110", "0001", "1110"], "I": ["1110", "0100", "0100", "0100", "1110"]}

def icon():
    """An Analogue Pocket in pixels: wide body with generous corners and shoulder bumps, a near-square screen (10:9, as the real one),
    d-pad low on the left, two angled face buttons low on the right, select/start pills under the screen."""
    w, h = 50, 32
    im = Image.new("RGB", (w, h), K); px = im.load()
    def rect(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): px[x, y] = c
    def rounded(x0, y0, x1, y1, r, outline, fill=None):                 # a rounded rectangle drawn as a 1 px outline (corner radius r)
        def inside(x, y):
            dx = max(x0 + r - x, x - (x1 - r), 0); dy = max(y0 + r - y, y - (y1 - r), 0)
            return x0 <= x <= x1 and y0 <= y <= y1 and dx * dx + dy * dy <= r * r + r
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if inside(x, y):
                    edge = not all(inside(x + i, y + j) for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    if edge: px[x, y] = outline
                    elif fill is not None: px[x, y] = fill
    rect(5, 1, 11, 2, W); rect(38, 1, 44, 2, W)                          # L / R shoulder bumps
    rounded(1, 3, 48, 30, 5, W, K)                                      # body
    rounded(15, 6, 34, 23, 2, W, K)                                     # screen glass (20 x 18)
    rnd = random.Random(4)                                              # the code on the screen: 8 x 7 cells of 2 px, one CGA colour each
    for cy in range(7):
        for cx in range(8):
            rect(17 + cx * 2, 8 + cy * 2, 18 + cx * 2, 9 + cy * 2, rnd.choice([C, M, W, C, M, K]))
    rect(7, 15, 9, 23, C); rect(4, 18, 12, 20, C)                       # d-pad (a plus)
    for cx, cy in ((40, 16), (36, 20)):                                 # A and B, a diagonal pair of round buttons (4 x 4, corners cut)
        rect(cx, cy, cx + 3, cy + 3, M)
        for x, y in ((cx, cy), (cx + 3, cy), (cx, cy + 3), (cx + 3, cy + 3)): px[x, y] = K
    rect(19, 26, 23, 27, W); rect(26, 26, 30, 27, W)                    # select / start
    return im

def text(lines, colours, gap=1):
    rows = []
    for t, col in zip(lines, colours):
        w = len(t) * 5 - 1; row = Image.new("RGB", (w, 5), K); p = row.load()
        for i, ch in enumerate(t):
            for y, r in enumerate(FONT[ch]):
                for x, b in enumerate(r):
                    if b == "1": p[i * 5 + x, y] = col
        rows.append(row)
    W_ = max(r.width for r in rows); out = Image.new("RGB", (W_, sum(r.height + gap for r in rows) - gap), K); y = 0
    for r in rows: out.paste(r, (0, y)); y += r.height + gap
    return out

def save(im, name, scale):
    im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(os.path.join(HERE, name))

def main():
    ic = icon(); save(ic, "logo.png", 12)
    tx = text(["POCKET", "TESTKIT"], [W, C], 2)
    b = Image.new("RGB", (4 + ic.width + 4 + tx.width + 4, ic.height + 6), K)
    b.paste(ic, (4, 3)); b.paste(tx, (4 + ic.width + 4, 3 + (ic.height - tx.height) // 2))
    for x in range(b.width): b.putpixel((x, 0), M if (x // 2) % 2 else C); b.putpixel((x, b.height - 1), C if (x // 2) % 2 else M)   # CGA checker rule
    save(b, "banner.png", 8)

if __name__ == "__main__": main()
