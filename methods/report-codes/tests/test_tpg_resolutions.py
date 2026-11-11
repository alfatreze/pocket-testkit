#!/usr/bin/env python3
"""TPG works at any screen size: round trips (both modes, many sizes and cell sizes, non-square, tiny, huge), the 400x360 output is
byte-identical to the original format (golden hashes), robust survives JPEG and a resize when told the native size, damage is detected."""
import hashlib, io, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
import numpy as np
from PIL import Image
import tpg
fails = []
def check(n, ok, info=""):
    if not ok: fails.append(n)
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else "  " + str(info)))
def rec(n, k=0): return bytes((i * 131 + n + k) & 255 for i in range(n))
def main():
    gold = json.load(open(os.path.join(ROOT, "tests", "golden_400x360.json"))); bad = []
    for key, h in gold.items():
        n, m = map(int, key.split("/"))
        try: got = hashlib.sha256(tpg.encode(rec(n), m).tobytes()).hexdigest()
        except ValueError: got = None
        if got != h: bad.append(key)
    check("400x360 output identical to the original format (%d cases)" % len(gold), not bad, bad)
    SIZES = [(160, 144), (240, 160), (320, 240), (400, 360), (480, 272), (640, 480), (800, 480), (1280, 720), (1920, 1080), (3840, 2160), (144, 160), (720, 1280), (96, 96)]
    for (w, h) in SIZES:
        for mode in (tpg.MODE_L, tpg.MODE_R):
            for cell in ((4,) if mode == tpg.MODE_L else (4, 8) if min(w, h) >= 256 else (2, 4)):
                if mode == tpg.MODE_R and min(w, h) // cell < tpg.MIN_CELLS: continue
                cap = tpg.capacity(mode, (w, h), cell)
                for n in sorted({1, 100, min(2000, cap), cap}):
                    name = "%dx%d %s cell%d %dB" % (w, h, "LR"[mode], cell, n)
                    try:
                        img = tpg.to_rgb(tpg.encode(rec(n), mode, (w, h), cell)); assert img.shape == (h, w, 3)
                        got = tpg.decode(img); check(name, got == rec(n))
                    except Exception as e: check(name, False, e)
    # an oversized payload is refused with a clear message
    try: tpg.encode(rec(tpg.capacity(tpg.MODE_R, (320, 240)) + 1), tpg.MODE_R, (320, 240)); check("too big refused", False)
    except ValueError as e: check("too big refused", "capacity" in str(e))
    # robust: JPEG q80 and a resize with the native size told, at a few screens
    for (w, h, cell) in ((1280, 720, 8), (640, 480, 4), (400, 360, 4), (1920, 1080, 8)):
        r = rec(1500, 3); img = Image.fromarray(tpg.to_rgb(tpg.encode(r, tpg.MODE_R, (w, h), cell)))
        b = io.BytesIO(); img.save(b, "JPEG", quality=80); b.seek(0)
        check("robust JPEG q80 %dx%d cell%d" % (w, h, cell), tpg.decode(np.asarray(Image.open(b).convert("RGB"))) == r)
        half = img.resize((w // 2, h // 2), Image.LANCZOS)
        try: ok = tpg.decode(np.asarray(half), native=(w, h)) == r
        except ValueError: ok = False
        check("robust half-size copy with native=%dx%d cell%d" % (w, h, cell), ok)
    # damage is loud
    img = tpg.to_rgb(tpg.encode(rec(3000), tpg.MODE_L, (800, 480)))
    img[240, 400] ^= 0xFF; img[200:260, 380:420] = 0
    try: tpg.decode(img); check("damaged lossless detected", False)
    except ValueError: check("damaged lossless detected", True)
    try: tpg.decode(np.zeros((480, 800, 3), np.uint8)); check("blank rejected", False)
    except ValueError: check("blank rejected", True)
    print("PASSED" if not fails else "FAILED %d: %s" % (len(fails), fails[:5])); return 1 if fails else 0
if __name__ == "__main__": raise SystemExit(main())
