#!/usr/bin/env python3
"""pocket_meta on a synthetic Pocket-style file (PNG + trailer in the documented layout), and: decoders still read a grid PNG that carries it.
Real screenshots are not stored here; run `python3 python/pocket_meta.py <your screenshot>` on one to check the layout on your Pocket."""
import io, os, struct, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
import numpy as np
from PIL import Image
import pocket_meta, decode, tpg
fails = []
def check(n, ok, info=""):
    if not ok: fails.append(n)
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else "  " + str(info)))
def pad(s, n): return s.encode().ljust(n, b"\0")
def trailer(png_len, fields, thumb=(121, 109), full=(400, 360)):
    a = MAGIC + struct.pack("<HH", *thumb) + bytes(thumb[0] * thumb[1] * 4)
    b = MAGIC + struct.pack("<HH", *full) + bytes(full[0] * full[1] * 4)
    foot = bytearray(600); foot[:4] = pocket_meta.MAGIC_FOOT
    foot[4:28] = struct.pack("<IIIIII", png_len, png_len + len(a), len(b), 0, 10, 123)
    for (name, off, n) in pocket_meta.FIELDS: foot[off:off + n] = pad(fields[name], n)
    return a + b + bytes(foot)
MAGIC = pocket_meta.MAGIC_IMG
def main():
    fields = dict(author="someone", core="MY_CORE_01", version="1.2.3", file="game.rom", platform_id="my_core_01", platform_name="MY CORE 01")
    buf = io.BytesIO(); Image.fromarray(tpg.to_rgb(tpg.encode(bytes(range(200)), tpg.MODE_R))).save(buf, "PNG"); png = buf.getvalue()
    full = png + trailer(len(png), fields)
    m = pocket_meta.read(full)
    check("fields read", m and all(m[k] == v for k, v in fields.items()), m)
    check("lengths consistent", m and m["consistent"] and m["thumbnail"] == (121, 109) and m["image2"] == (400, 360))
    check("a plain PNG has no trailer", pocket_meta.read(png) is None)
    check("a truncated trailer is refused, not guessed", pocket_meta.read(full[:-50]) is None)
    m2 = pocket_meta.read(png + trailer(len(png) + 5, fields)); check("a re-saved/edited file is flagged inconsistent", m2 and not m2["consistent"])
    d = tempfile.mkdtemp(); p = os.path.join(d, "shot.png"); open(p, "wb").write(full)
    tier, payload = decode.decode(p); check("grid still decodes with the trailer present", tier == "R" and payload == bytes(range(200)))
    check("images extracted", pocket_meta.read(full, with_images=True)["image2_rgb"].shape == (360, 400, 3))
    print("PASSED" if not fails else "FAILED %s" % fails); return 1 if fails else 0
if __name__ == "__main__": raise SystemExit(main())
