#!/usr/bin/env python3
"""Pixel logo in the four CGA colours (palette 1, high intensity). python3 docs/logo/make_logo.py  -> logo.png, banner.png in this folder.
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
    w, h = 34, 26
    im = Image.new("RGB", (w, h), K); px = im.load()
    def rect(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): px[x, y] = c
    rect(1, 1, 32, 24, W); rect(2, 2, 31, 23, K)                       # body outline
    for x, y in [(1, 1), (32, 1), (1, 24), (32, 24)]: px[x, y] = K       # rounded corners
    rect(10, 4, 23, 17, W); rect(11, 5, 22, 16, K)                     # screen frame
    rnd = random.Random(4)                                             # the code on the screen: 5x4 cells, one CGA colour each
    for cy in range(5):
        for cx in range(5):
            c = rnd.choice([C, M, W, C, M, K]); rect(12 + cx * 2, 6 + cy * 2, 13 + cx * 2, 7 + cy * 2, c)
    px[11, 4] = px[22, 4] = px[11, 17] = px[22, 17] = K
    rect(5, 8, 6, 14, C); rect(3, 10, 8, 11, C)   # d-pad (a plus)
    rect(26, 8, 27, 9, M); rect(29, 11, 30, 12, M)                     # buttons
    rect(13, 20, 14, 20, W); rect(17, 20, 18, 20, W); rect(21, 20, 22, 20, W)   # start/select style marks
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
