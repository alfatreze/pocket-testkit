"""Tier Q: encode with the Pocket firmware's own QR encoder (c/qr/qrcode.h, built natively) and draw it on a 400x360 screen.
  qr_tier.encode_matrix(b'text') -> (version, mask, numpy 0/1 matrix)    level L, byte mode, versions 1..38
  qr_tier.screen(text)           -> PIL image, black screen, code centred, white quiet zone, modules as big as fit (min 2 px)
"""
import os, subprocess, tempfile
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "c", "qr", "qr_cli.c")
_BIN = os.path.join(tempfile.gettempdir(), "pocket_qr_cli")

def _build():
    if not os.path.exists(_BIN) or os.path.getmtime(_BIN) < os.path.getmtime(SRC):
        cmd = ["cc", "-O2", "-Wno-unused-function", "-o", _BIN, SRC]
        if subprocess.run(cmd, capture_output=True).returncode == 0: return
        # macOS: the default SDK can be unusable for the linker (seen 2026-11 with MacOSX27.2); try the other installed SDKs
        import glob
        for sdk in sorted(glob.glob("/Library/Developer/CommandLineTools/SDKs/MacOSX*.sdk"), reverse=True):
            if subprocess.run(cmd, capture_output=True, env={**os.environ, "SDKROOT": sdk}).returncode == 0: return
        subprocess.run(cmd, check=True)

def encode_matrix(payload: bytes, minver=1, maxver=38, mask=-1):
    _build()
    out = subprocess.run([_BIN, str(minver), str(maxver), str(mask)], input=payload, capture_output=True, check=True).stdout.split()
    if out[0] != b"QR": raise ValueError("payload too big for QR version %d" % maxver)
    ver, m, sz, hx = int(out[1]), int(out[2]), int(out[3]), out[4].decode()
    bits = bin(int("1" + hx, 16))[3:][:sz * sz]
    return ver, m, np.array([int(c) for c in bits], np.uint8).reshape(sz, sz)

# Density levels, from tests/qr_density_study.py (docs/qr_density.md). Bytes are the level-L byte-mode capacity of the version.
LEVELS = {"photo": 10,      # <= 271 B: a phone scanner reads it (OpenCV's classic detector, the closest stand-in, is reliable here)
          "careful": 22,    # <= 1,003 B: simulated photos decode with the Aruco decoder; a steady, close, sharp photo is needed
          "max": 38}        # <= 2,699 B: 2 px modules; screenshots only (lossless PNG or JPEG q80). Photos failed in the study.
DEFAULT_DENSITY = "photo"

class DensityError(ValueError):
    """The payload needs a denser QR than the chosen level allows, or the max level was asked for without confirmation."""

def check_density(version, density=DEFAULT_DENSITY, allow_max=False):
    import warnings
    if density not in LEVELS: raise DensityError("unknown density %r (use one of %s)" % (density, ", ".join(LEVELS)))
    if version > LEVELS[density]:
        need = next(n for n, v in LEVELS.items() if version <= v)
        raise DensityError("this payload needs QR version %d; density %r allows up to version %d. Shorten it, or ask for density=%r." % (version, density, LEVELS[density], need))
    if density == "max" and not allow_max:
        raise DensityError("density 'max' (versions up to 38, 2 px modules) is for lossless screenshots only: phones and heavy JPEG fail. Pass allow_max=True (CLI: --yes-max) if that is what you want.")
    if density == "max": warnings.warn("QR density 'max': read it from the original PNG with python/qr_decode.py; do not expect a phone to scan it.", stacklevel=3)
    elif density == "careful": warnings.warn("QR density 'careful': photograph it close, sharp and straight; test the decode before relying on it.", stacklevel=3)

def screen(text, W=400, H=360, density=DEFAULT_DENSITY, allow_max=False):
    ver, _, mat = encode_matrix(text.encode())
    check_density(ver, density, allow_max)
    quiet = 4; n = mat.shape[0] + 2 * quiet
    px = max(2, min(W, H - 40) // n)
    img = np.pad(255 * (1 - mat), quiet, constant_values=255).astype(np.uint8).repeat(px, 0).repeat(px, 1)
    s = Image.new("RGB", (W, H), (0, 0, 0)); q = Image.fromarray(img).convert("RGB")
    s.paste(q, ((W - q.width) // 2, (H - q.height) // 2)); return s


def main(argv=None):
    import argparse, sys
    ap = argparse.ArgumentParser(description="Draw a QR code on a 400x360 screen picture with a density guard.")
    ap.add_argument("text"); ap.add_argument("out"); ap.add_argument("--density", choices=list(LEVELS), default=DEFAULT_DENSITY)
    ap.add_argument("--yes-max", action="store_true", help="confirm density 'max' without the interactive prompt")
    a = ap.parse_args(argv)
    ok = a.yes_max
    if a.density == "max" and not ok:
        if sys.stdin.isatty():
            print("Density 'max' makes a 2 px-module code that only a lossless screenshot decodes; phones and JPEG fail.\nType MAX to continue: ", end="", flush=True)
            ok = sys.stdin.readline().strip() == "MAX"
        if not ok: print("refused: density 'max' needs --yes-max or typing MAX.", file=sys.stderr); return 2
    try: screen(a.text, density=a.density, allow_max=ok).save(a.out)
    except DensityError as e: print("refused: %s" % e, file=sys.stderr); return 2
    print("wrote %s" % a.out); return 0

if __name__ == "__main__": raise SystemExit(main())
