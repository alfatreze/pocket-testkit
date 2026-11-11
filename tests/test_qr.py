#!/usr/bin/env python3
"""The Pocket firmware's QR encoder (c/qr/qrcode.h), built natively, against segno: symbol equal module for module for every
version 1..38 (mask 0; all eight with --full), automatic mask at a few versions, a payload one byte too big refused,
and (OpenCV installed) a rendered image decodes.   pip install segno numpy pillow opencv-python"""
import os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python"))
import segno, segno.consts as C
import qr_tier
CAP = {v: (8 * sum(e.num_blocks * e.num_data for e in C.ECC[v][C.ERROR_LEVEL_L]) - (12 if v < 10 else 20)) // 8 for v in range(1, 39)}
fails = []
def check(name, ok, info=""):
    if not ok: fails.append(name)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else "  " + info))
def payload(v): return bytes((i * 131 + v * 17 + 7) & 0xFF for i in range(CAP[v]))
def ref(p, v, m):
    q = segno.make(p, mode="byte", error="l", version=v, mask=m, boost_error=False, micro=False)
    return [list(r) for r in q.matrix]
def main():
    masks = range(8) if "--full" in sys.argv else (0,)
    for v in range(1, 39):
        p = payload(v)
        for m in masks:
            ver, mm, mat = qr_tier.encode_matrix(p, v, v, m)
            check("v%d mask%d" % (v, m), ver == v and mat.tolist() == ref(p, v, m))
        if v in (1, 7, 11, 20, 30, 38):
            ver, mm, mat = qr_tier.encode_matrix(p, 1, 38)
            check("v%d auto (mask %d)" % (v, mm), mat.tolist() == ref(p, ver, mm))
    try: qr_tier.encode_matrix(bytes(CAP[38] + 1)); check("too big refused", False)
    except ValueError: check("too big refused", True)
    try:
        import cv2, numpy as np
        for text in ("PKT1 PASS run=17 b=0.7.1", "x" * 150, "y" * 1000):
            img = np.asarray(qr_tier.screen(text).convert("RGB"))
            import qr_decode
            got = qr_decode.decode(img)
            check("opencv decodes %d chars" % len(text), got == text, repr(got))
    except ImportError: print("note: OpenCV missing, decode check skipped")
    print("PASSED" if not fails else "FAILED %s" % fails[:5]); return 1 if fails else 0
if __name__ == "__main__": raise SystemExit(main())
