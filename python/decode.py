#!/usr/bin/env python3
"""One decoder for every tier: give it a screenshot or a photo, it says which carrier it found and returns the payload.
  python3 python/decode.py shot.png                 prints the tier and the payload (text if it is text, else a hex dump)
  python3 python/decode.py shot.png --out rec.bin   also writes the raw payload
  python3 python/decode.py shot.jpg --json          machine output: {"tier": "R", "length": N, "payload_hex": ...} / {"tier": "Q", "text": ...}
Exit 0 = decoded, 1 = nothing decodable (a bad CRC is reported as such, never as a wrong payload), 2 = usage.
As a library:  import decode; tier, payload = decode.decode("shot.png")   # tier is 'L', 'R' or 'Q'; payload is bytes"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tpg

def decode(path):
    rgb = np.asarray(Image.open(path).convert("RGB"))
    errs = []
    try:                                           # tiers L and R: the CRC32 inside makes a wrong read fail, never mis-decode
        payload = tpg.decode(rgb)
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
    a = ap.parse_args(argv)
    try: tier, payload = decode(a.image)
    except ValueError as e: print("invalid: %s" % e, file=sys.stderr); return 1
    if a.out: open(a.out, "wb").write(payload)
    if a.json:
        d = {"tier": tier, "length": len(payload)}
        try: d["text"] = payload.decode("utf-8")
        except UnicodeDecodeError: d["payload_hex"] = payload.hex()
        print(json.dumps(d))
    else:
        try: body = payload.decode("utf-8")
        except UnicodeDecodeError: body = payload.hex()
        print("tier %s, %d bytes\n%s" % (tier, len(payload), body[:2000]))
    return 0

if __name__ == "__main__": raise SystemExit(main())
