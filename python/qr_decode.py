"""Tier Q decoder (OpenCV). From Tau's decode_tau_suite.qr_text.
Dense codes (2 px modules) defeat OpenCV's classic detector even for reference symbols; the Aruco-based detector reads them once
the pixels are doubled with nearest neighbour (never smoothing). Tries it first, then the classic one, at scales 1..4.
For a lossless screenshot use the original PNG, not a resized copy.  decode(path_or_array) -> str, raises ValueError."""
import cv2, numpy as np

def decode(src) -> str:
    img = cv2.imread(src) if isinstance(src, str) else cv2.cvtColor(np.asarray(src), cv2.COLOR_RGB2BGR)
    if img is None: raise ValueError("cannot read %r" % (src,))
    dets = [cv2.QRCodeDetectorAruco(), cv2.QRCodeDetector()] if hasattr(cv2, "QRCodeDetectorAruco") else [cv2.QRCodeDetector()]
    for det in dets:
        for scale in (1, 2, 3, 4):
            big = img if scale == 1 else cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            txt, _, _ = det.detectAndDecode(big)
            if txt: return txt
    raise ValueError("no QR code found")
