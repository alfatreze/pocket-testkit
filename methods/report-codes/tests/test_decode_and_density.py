#!/usr/bin/env python3
"""The unified decoder names the right tier for each carrier, a bad picture fails loudly, and the density guard refuses what it should.
   pip install numpy pillow opencv-python segno"""
import os, sys, tempfile, io, warnings, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
import numpy as np
from PIL import Image
import tpg, qr_tier, decode
fails = []
def check(n, ok, info=""):
    if not ok: fails.append(n)
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else "  " + str(info)))
def save(img, path): img.save(path)
def main():
    rec = bytes((i * 7) & 0xFF for i in range(900)); d = tempfile.mkdtemp()
    for mode, tier in ((tpg.MODE_L, "L"), (tpg.MODE_R, "R")):
        pth = os.path.join(d, tier + ".png"); Image.fromarray(tpg.to_rgb(tpg.encode(rec, mode))).save(pth)
        t, p = decode.decode(pth); check("grid tier %s" % tier, t == tier and p == rec, (t, len(p)))
    pth = os.path.join(d, "q.png"); qr_tier.screen("PKT1 PASS run=17").save(pth)
    t, p = decode.decode(pth); check("QR tier", t == "Q" and p == b"PKT1 PASS run=17", (t, p))
    black = os.path.join(d, "b.png"); Image.new("RGB", (400, 360)).save(black)
    try: decode.decode(black); check("blank picture rejected", False)
    except ValueError: check("blank picture rejected", True)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "python", "decode.py"), black], capture_output=True); check("CLI exit 1 on blank", r.returncode == 1)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "python", "decode.py"), pth, "--json"], capture_output=True, text=True); check("CLI json", '"tier": "Q"' in r.stdout, r.stdout)
    # density guard
    small, mid, big = "x" * 100, "y" * 800, "z" * 2000
    warnings.simplefilter("ignore")
    check("photo level takes 100 B", qr_tier.screen(small) is not None)
    for txt, lvl, msg in ((mid, "photo", "mid refused at photo"), (big, "careful", "big refused at careful")):
        try: qr_tier.screen(txt, density=lvl); check(msg, False)
        except qr_tier.DensityError: check(msg, True)
    check("careful takes 800 B", qr_tier.screen(mid, density="careful") is not None)
    try: qr_tier.screen(big, density="max"); check("max needs confirmation", False)
    except qr_tier.DensityError as e: check("max needs confirmation", "allow_max" in str(e))
    check("max with allow_max", qr_tier.screen(big, density="max", allow_max=True) is not None)
    py = [sys.executable, os.path.join(ROOT, "python", "qr_tier.py"), big, os.path.join(d, "m.png"), "--density", "max"]
    check("CLI max refused without --yes-max", subprocess.run(py, capture_output=True, stdin=subprocess.DEVNULL).returncode == 2)
    check("CLI max accepted with --yes-max", subprocess.run(py + ["--yes-max"], capture_output=True, stdin=subprocess.DEVNULL).returncode == 0)
    # QR is resolution independent: the same text decodes on any screen size; a screen too small for the version is refused clearly
    import qr_decode, numpy as np
    for (w, h) in ((400, 360), (800, 480), (1920, 1080), (240, 160), (160, 144)):
        try:
            img = qr_tier.screen("PKT1 PASS run=17", W=w, H=h)
            check("QR on %dx%d" % (w, h), qr_decode.decode(np.asarray(img)) == "PKT1 PASS run=17")
        except Exception as e: check("QR on %dx%d" % (w, h), False, e)
    try: qr_tier.screen("x" * 900, W=160, H=144, density="careful"); check("QR too big for a tiny screen refused", False)
    except qr_tier.DensityError: check("QR too big for a tiny screen refused", True)
    print("PASSED" if not fails else "FAILED %s" % fails); return 1 if fails else 0
if __name__ == "__main__": raise SystemExit(main())
