"""Sample pages: every page, at several screen sizes, must decode to the payload the C code says it carries."""
import re, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python")); sys.path.insert(0, str(ROOT / "examples"))
import decode, make_gallery

SIZES = ["160x144", "320x240", "400x360", "800x480", "800x720", "250x130"]
QUIET = 4


def expect(page, n, name, tier, w, h):
    head = ("pocket-testkit sample page=%d name=%s tier=%s size=%dx%d bytes=%d\n" % (page, name, tier, w, h, n)).encode()
    out = bytearray(head[:n])
    i = 0
    while len(out) < n:
        out.append(10 if i % 64 == 63 else ord("a") + (i * 7 + page) % 26); i += 1
    return bytes(out)


def test_all_pages():
    checked = unusable = 0
    with tempfile.TemporaryDirectory() as d:
        rows = make_gallery.render(d, SIZES, unlock=True)
        for r in rows:
            page, n, w, h = int(r["page"]), int(r["bytes"]), int(r["w"]), int(r["h"])
            if r["status"] == "unusable":
                unusable += 1
                # unusable only when the code cannot be drawn: tiny screens
                assert min(w, h) < 200 or r["tier"] == "Q", r
                continue
            assert r["status"] == "ok", r
            tier, payload = decode.decode(str(Path(d) / r["file"]))
            assert tier == r["tier"], (r["file"], tier)
            assert payload == expect(page, n, r["name"], r["tier"], w, h), r["file"]
            checked += 1
    assert checked >= 40, checked
    print("%d pictures decoded and matched, %d unusable on small screens" % (checked, unusable))


def test_qr_quiet_zone_is_four_modules():
    """Decoders forgive a short border, so check it directly: white margin = 4 modules (a finder's outer ring is 7 modules wide)."""
    import numpy as np
    from PIL import Image
    with tempfile.TemporaryDirectory() as d:
        rows = make_gallery.render(d, ["400x360", "800x480"], unlock=True)
        n = 0
        for r in rows:
            if r["tier"] != "Q" or r["file"] == "-": continue
            g = np.array(Image.open(Path(d) / r["file"]).convert("L"))
            if g[3, 3] == 255: g[:8, :52] = 0                                            # the page-number marker is not part of the code
            ys, xs = np.where(g == 255)
            wy0, wy1, wx0, wx1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1      # white area incl. border
            dys, dxs = np.where(g[wy0:wy1, wx0:wx1] == 0)
            top = g[wy0 + dys.min(), wx0 + dxs.min():wx0 + dxs.max() + 1]
            run = 0
            while run < len(top) and top[run] == 0: run += 1                           # first dark run on the symbol's top row
            px = run / 7.0
            assert abs((dxs.min()) / px - 4) < 0.01 and abs((wx1 - wx0 - dxs.max() - 1) / px - 4) < 0.01, (r["file"], dxs.min() / px)
            n += 1
        assert n == 8, n


def test_locked_page_is_not_a_code():
    with tempfile.TemporaryDirectory() as d:
        rows = make_gallery.render(d, ["400x360"], unlock=False)
        r = [x for x in rows if x["name"] == "Q-max"][0]
        assert r["status"] == "locked"
        try:
            decode.decode(str(Path(d) / r["file"])); assert False, "locked page decoded"
        except ValueError:
            pass


if __name__ == "__main__":
    test_all_pages(); test_qr_quiet_zone_is_four_modules(); test_locked_page_is_not_a_code(); print("ok")
