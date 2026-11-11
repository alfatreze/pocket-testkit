#!/usr/bin/env python3
"""One decoder for every tier: give it a screenshot or a photo, it says which carrier it found and returns the payload.
  python3 python/decode.py shot.png                 prints the tier and the payload (text if it is text, else a hex dump)
  python3 python/decode.py shot.png --out rec.bin   also writes the raw payload
  python3 python/decode.py shot.jpg --json          machine output: {"tier": "R", "length": N, "payload_hex": ...} / {"tier": "Q", "text": ...}
Exit 0 = decoded, 1 = nothing decodable (a bad CRC is reported as such, never as a wrong payload), 2 = usage.
Any screen size: the grid reads the picture's own size; for a resized copy pass --native WxH. QR needs nothing.
As a library:  import decode; tier, payload = decode.decode("shot.png")   # tier is 'L', 'R' or 'Q'; payload is bytes"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tpg

def decode(path, native=None):
    rgb = np.asarray(Image.open(path).convert("RGB"))
    errs = []
    try:                                           # tiers L and R: the CRC32 inside makes a wrong read fail, never mis-decode
        payload = tpg.decode(rgb, native)
        return ("R" if "mode R" in tpg.LAST_READ else "L"), payload
    except ValueError as e: errs.append("grid: %s" % e)
    try:                                           # tier Q: needs OpenCV
        import qr_decode
        return "Q", qr_decode.decode(path).encode("latin1", "replace")
    except ImportError: errs.append("QR: OpenCV not installed")
    except ValueError as e: errs.append("QR: %s" % e)
    raise ValueError("; ".join(errs))

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image"); ap.add_argument("--out"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--native", help="WxH, the screen size, when the grid picture is a resized copy (tier R only)")
    a = ap.parse_args(argv)
    try: tier, payload = decode(a.image, tuple(int(v) for v in a.native.lower().split("x")) if a.native else None)
    except ValueError as e: print("invalid: %s" % e, file=sys.stderr); return 1
    if a.out: open(a.out, "wb").write(payload)
    try:
        import pocket_meta; meta = pocket_meta.read(a.image)
    except Exception: meta = None     # no Pocket trailer (a photo, an edited copy): fine
    if a.json:
        d = {"tier": tier, "length": len(payload)}
        if meta: d["pocket"] = {k: meta[k] for k in ("author", "core", "version", "file", "platform_id", "platform_name", "consistent")}
        try: d["text"] = payload.decode("utf-8")
        except UnicodeDecodeError: d["payload_hex"] = payload.hex()
        print(json.dumps(d))
    else:
        try: body = payload.decode("utf-8")
        except UnicodeDecodeError: body = payload.hex()
        if meta: print("from %s %s (%s)" % (meta["core"], meta["version"], meta["author"]))
        print("tier %s, %d bytes\n%s" % (tier, len(payload), body[:2000]))
    return 0

if __name__ == "__main__": raise SystemExit(main())
