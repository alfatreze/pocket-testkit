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

def screen(text, W=400, H=360):
    ver, _, mat = encode_matrix(text.encode())
    quiet = 4; n = mat.shape[0] + 2 * quiet
    px = max(2, min(W, H - 40) // n)
    img = np.pad(255 * (1 - mat), quiet, constant_values=255).astype(np.uint8).repeat(px, 0).repeat(px, 1)
    s = Image.new("RGB", (W, H), (0, 0, 0)); q = Image.fromarray(img).convert("RGB")
    s.paste(q, ((W - q.width) // 2, (H - q.height) // 2)); return s
