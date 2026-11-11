#!/usr/bin/env python3
"""Pictures made by the Python reference for the Rust crate's tests: rust/tests/fixtures/ + manifest.tsv (file, tier, native WxH or -, expected file).
   python3 tests/make_rust_fixtures.py   (needs numpy pillow opencv-python segno)"""
import io, os, sys, warnings
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python")); sys.path.insert(0, os.path.join(ROOT, "examples"))
import numpy as np
from PIL import Image
import tpg, qr_tier
warnings.simplefilter("ignore")
OUT = os.path.join(ROOT, "rust", "tests", "fixtures"); os.makedirs(OUT, exist_ok=True)
rows = []
def rec(n): return bytes((i * 131 + n) & 255 for i in range(n))
def add(name, img, tier, expected, native="-", **kw):
    img.save(os.path.join(OUT, name), **kw); e = name.rsplit(".", 1)[0] + ".expected"; open(os.path.join(OUT, e), "wb").write(expected); rows.append((name, tier, native, e))
def grid(name, size, mode, cell, n, native="-", post=None, **kw):
    r = rec(n); img = Image.fromarray(tpg.to_rgb(tpg.encode(r, mode, size, cell)))
    if post: img = post(img)
    add(name, img, "LR"[mode], r, native, **kw)
grid("grid_400x360_L.png", (400, 360), 0, 4, 2352)
grid("grid_400x360_R.png", (400, 360), 1, 4, 2352)
grid("grid_160x144_L.png", (160, 144), 0, 4, 500)
grid("grid_160x144_R_cell2.png", (160, 144), 1, 2, 90)
grid("grid_800x480_R.png", (800, 480), 1, 4, 5000)
grid("grid_1280x720_R_cell8.png", (1280, 720), 1, 8, 4000)
grid("grid_1920x1080_L.png", (1920, 1080), 0, 4, 3000)
grid("grid_720x1280_R_cell8.png", (720, 1280), 1, 8, 1500)
grid("grid_400x360_R_q80.jpg", (400, 360), 1, 4, 2352, quality=80)
grid("grid_1280x720_R_half.png", (1280, 720), 1, 8, 2000, native="1280x720", post=lambda im: im.resize((640, 360), Image.LANCZOS))
for name, (w, h), text in (("qr_400x360.png", (400, 360), "PKT1 PASS run=17 b=0.7.1"), ("qr_1920x1080.png", (1920, 1080), "PKT1 PASS run=17 b=0.7.1"), ("qr_160x144.png", (160, 144), "PKT1 OK")):
    add(name, qr_tier.screen(text, W=w, H=h), "Q", text.encode())
dense = "".join("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"[(i * 7 + i // 5) % 64] for i in range(1000))
add("qr_dense_max.png", qr_tier.screen(dense, density="max", allow_max=True), "Q", dense.encode())
open(os.path.join(OUT, "manifest.tsv"), "w").write("".join("\t".join(r) + "\n" for r in rows)); print(len(rows), "fixtures")
