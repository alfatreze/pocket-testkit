#!/usr/bin/env python3
"""Regenerate every picture in docs/img/ from one sample report.  python3 examples/make_examples.py
Needs numpy, Pillow, opencv-python.  The 'photo' pictures are a SIMULATION (blur, noise, tilt, JPEG), not a real camera."""
import io, os, sys, zlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
import tpg, qr_tier, qr_decode, base64
OUT = os.path.join(ROOT, "docs", "img"); os.makedirs(OUT, exist_ok=True)
W, H = tpg.W, tpg.H

_rows = ",".join('["t%03d",%d,%d]' % (i, i % 3, (i * 37) % 1000) for i in range(150))
REPORT = ('{"report":"USER CHECK","run":17,"verdict":"PASS","build":"0.7.1","note":"sample record for pocket-testkit","tests":[' + _rows + ']}').encode()
SUMMARY = "PKT1 PASS run=17 b=0.7.1 crc=%08X" % zlib.crc32(REPORT)

def screen_png(arr565=None, rgb=None):
    return Image.fromarray(tpg.to_rgb(arr565)) if rgb is None else Image.fromarray(rgb)

def qr_screen(text): return qr_tier.screen(text)          # the Pocket firmware's own encoder (c/qr/qrcode.h)

def caption(img, top, bottom):
    d = ImageDraw.Draw(img); d.text((8, 6), top, fill=(255, 160, 40)); d.text((8, H - 16), bottom, fill=(140, 146, 160)); return img

def with_zoom(img):
    """Screen on the left, the code block enlarged on the right (a 400x360 screen is small on a README)."""
    a = np.asarray(img.convert("RGB")); ys, xs = np.nonzero(a.sum(2)[24:H - 24] > 0); 
    box = (xs.min() - 2, ys.min() + 22, xs.max() + 3, ys.max() + 25)
    z = img.crop(box); f = max(1, min(8, 360 // max(z.width, z.height))); z = z.resize((z.width * f, z.height * f), Image.NEAREST)
    out = Image.new("RGB", (W + 360 + 12, H), (24, 24, 28)); out.paste(img, (0, 0)); out.paste(z, (W + 12 + (360 - z.width) // 2, (H - z.height) // 2)); return out

def fake_photo(img, seed=1):
    """Simulated phone photo of the screen: tilt, blur, gamma, noise, JPEG q70."""
    rng = np.random.default_rng(seed)
    a = np.asarray(img.convert("RGB").resize((W * 2, H * 2), Image.BICUBIC))
    big = np.full((H * 3, W * 3, 3), 40, np.uint8); y0, x0 = H // 2, W // 2
    big[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a
    src = np.float32([[x0, y0], [x0 + a.shape[1], y0], [x0 + a.shape[1], y0 + a.shape[0]], [x0, y0 + a.shape[0]]])
    dst = src + np.float32([[18, 10], [-12, 22], [-20, -14], [10, -20]])
    out = cv2.warpPerspective(big, cv2.getPerspectiveTransform(src, dst), (W * 3, H * 3), borderValue=(40, 40, 40))
    out = cv2.GaussianBlur(out, (0, 0), 1.6).astype(np.float32) / 255
    out = np.clip(out ** 1.15 + rng.normal(0, 0.03, out.shape), 0, 1)
    im = Image.fromarray((out * 255).astype(np.uint8)); b = io.BytesIO(); im.save(b, "JPEG", quality=70); b.seek(0)
    return Image.open(b).convert("RGB")

def qr_decode_safe(img):
    try: return qr_decode.decode(img)
    except ValueError: return ""

def main():
    log = []
    L = screen_png(tpg.encode(REPORT, tpg.MODE_L)); R = screen_png(tpg.encode(REPORT, tpg.MODE_R)); Q = qr_screen(SUMMARY)
    big = bytes(np.random.default_rng(7).integers(0, 256, 40000, dtype=np.uint8))
    DENSE = "TAUD1:" + base64.urlsafe_b64encode(zlib.compress(REPORT, 9)).decode().rstrip("=")
    QD = qr_screen(DENSE)
    LB = screen_png(tpg.encode(big, tpg.MODE_L))
    for name, im, top, bot in [("tier_l_lossless", L, "LOSSLESS GRID  %d B" % len(REPORT), "PNG ONLY"),
                               ("tier_r_robust", R, "ROBUST GRID  %d B" % len(REPORT), "SURVIVES JPEG / RESIZE"),
                               ("tier_q_qr", Q, "QR  summary only", "SURVIVES A PHONE CAMERA"),
                               ("tier_q_dense", QD, "QR  full record (compressed) %d chars" % len(DENSE), "DENSE: NEEDS A STEADY CLEAN PHOTO"),
                               ("tier_l_large", LB, "LOSSLESS GRID  40000 B", "BIG REPORT: BLOCK GROWS")]:
        with_zoom(caption(im, top, bot)).save(os.path.join(OUT, name + ".png"))
    # checks
    for im in (L, R): assert tpg.decode(np.asarray(im.convert("RGB"))) == REPORT   # the captioned screenshot itself decodes
    assert qr_decode_safe(Q) == SUMMARY
    log.append("dense QR (%d chars, version %d): %s" % (len(DENSE), qr_tier.encode_matrix(DENSE.encode())[0], "decoded by OpenCV" if qr_decode_safe(QD) == DENSE else "NOT decoded by OpenCV"))
    assert tpg.decode(tpg.to_rgb(tpg.encode(REPORT, tpg.MODE_L))) == REPORT
    assert tpg.decode(tpg.to_rgb(tpg.encode(REPORT, tpg.MODE_R))) == REPORT
    assert tpg.decode(tpg.to_rgb(tpg.encode(big, tpg.MODE_L))) == big
    # JPEG q80 on robust (screenshot sent through chat)
    b = io.BytesIO(); Image.fromarray(tpg.to_rgb(tpg.encode(REPORT, tpg.MODE_R))).save(b, "JPEG", quality=80); b.seek(0)
    rj = np.asarray(Image.open(b).convert("RGB")); log.append("robust after JPEG q80: " + ("OK" if tpg.decode(rj) == REPORT else "FAIL"))
    # simulated photos
    for name, im in [("sim_photo_qr", Q), ("sim_photo_robust_grid", R)]:
        ph = fake_photo(im); ph.save(os.path.join(OUT, name + ".jpg"), quality=70)
        if "qr" in name: log.append("simulated photo of QR: " + ("decoded -> " + qr_decode_safe(ph) if qr_decode_safe(ph) == SUMMARY else "NOT decoded"))
        else:
            try: ok = tpg.decode(np.asarray(ph.resize((W, H), Image.LANCZOS))) == REPORT
            except ValueError: ok = False
            log.append("simulated photo of robust grid: " + ("decoded" if ok else "not decoded (expected: a camera is not supported)"))
    print("\n".join(log))
    open(os.path.join(OUT, "RESULTS.txt"), "w").write("\n".join(log) + "\n")

if __name__ == "__main__": main()
