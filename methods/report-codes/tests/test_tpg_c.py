#!/usr/bin/env python3
"""c/tpg.h against python/tpg.py, pixel for pixel, at many screen sizes, both modes, several cell sizes, and a refusal case."""
import os, subprocess, sys, tempfile, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
import numpy as np, tpg
fails = []
def check(n, ok, info=""):
    if not ok: fails.append(n)
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else "  " + str(info)))
def build(out):
    cmd = ["cc", "-O2", "-Wall", "-Wextra", "-o", out, os.path.join(ROOT, "tests", "tpg_harness.c")]
    if subprocess.run(cmd, capture_output=True).returncode == 0: return
    for sdk in sorted(glob.glob("/Library/Developer/CommandLineTools/SDKs/MacOSX*.sdk"), reverse=True):
        if subprocess.run(cmd, capture_output=True, env={**os.environ, "SDKROOT": sdk}).returncode == 0: return
    subprocess.run(cmd, check=True)
def main():
    exe = os.path.join(tempfile.mkdtemp(), "tpgh"); build(exe)
    cases = [(400, 360, 0, 4, 3000), (400, 360, 1, 4, 3000), (160, 144, 0, 4, 500), (160, 144, 1, 2, 100), (320, 240, 1, 4, 1500), (800, 480, 0, 4, 9000),
             (800, 480, 1, 4, 5000), (1280, 720, 1, 8, 20000), (1920, 1080, 0, 4, 100000), (1920, 1080, 1, 4, 30000), (720, 1280, 1, 8, 4000), (480, 272, 0, 4, 1)]
    for w, h, mode, cell, n in cases:
        name = "%dx%d %s cell%d %dB" % (w, h, "LR"[mode], cell, n)
        out = subprocess.run([exe, str(w), str(h), str(mode), str(cell), str(n)], capture_output=True, text=True).stdout.split("\n")
        rec = bytes((i * 131 + n) & 255 for i in range(n))
        try: ref = tpg.encode(rec, mode, (w, h), cell)
        except ValueError: check(name + " refused by both", out[0] == "REFUSED"); continue
        _, x0, y0, px = out[0].split(); x0, y0, px = int(x0), int(y0), int(px)
        got = np.array([[int(r[i:i + 4], 16) for i in range(0, len(r), 4)] for r in out[1:1 + px]], np.uint16)
        check(name, tpg.block(n, mode, (w, h), cell) == (x0, y0, px) and np.array_equal(got, ref[y0:y0 + px, x0:x0 + px]))
    o = subprocess.run([exe, "320", "240", "1", "4", str(tpg.capacity(1, (320, 240), 4) + 1)], capture_output=True, text=True).stdout.strip()
    check("too big refused", o == "REFUSED", o)
    print("PASSED" if not fails else "FAILED %s" % fails[:5]); return 1 if fails else 0
if __name__ == "__main__": raise SystemExit(main())
