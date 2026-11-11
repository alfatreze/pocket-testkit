"""The Pocket core's RTL in simulation: render a sample page file with the C code, load it through simulated bridge writes into
pk_fb_video, capture one video frame, and decode that frame with the kit's decoder. Needs iverilog and a C compiler."""
import glob, os, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "python")); sys.path.insert(0, str(ROOT / "tests")); sys.path.insert(0, str(ROOT / "examples"))
import decode, make_gallery
from test_sample import expect

W, H = 320, 240
PAGES = ["L-sample", "L-max", "R-sample", "R-max", "Q-photo-max", "Q-careful"]


def build_tb(tmp):
    exe = Path(tmp) / "tb.vvp"
    subprocess.run(["iverilog", "-g2012", "-o", str(exe), str(ROOT / "core/sim/tb_pk_fb_video.sv"), str(ROOT / "core/rtl/pk_fb_video.sv")], check=True)
    return exe


def render_bins(tmp):
    exe = Path(tmp) / "host_gallery"; make_gallery.build(exe)
    d = Path(tmp) / "bins"; d.mkdir()
    subprocess.run([str(exe), str(d), "-b", "-u", "%dx%d" % (W, H)], check=True)
    return d


def run(tb, binfile, out, flags=()):
    r = subprocess.run(["vvp", str(tb), "+img=%s" % binfile, "+out=%s" % out] + ["+" + f for f in flags], capture_output=True, text=True, check=True)
    assert "PASS" in r.stdout, r.stdout
    return r.stdout


def test_pages_through_the_core():
    if not shutil.which("iverilog"):
        import pytest; pytest.skip("iverilog not installed")
    with tempfile.TemporaryDirectory() as tmp:
        tb, bins = build_tb(tmp), render_bins(tmp)
        for name in PAGES:
            f = glob.glob(str(bins / ("page*_%s_%dx%d.bin" % (name, W, H))))[0]
            page = int(Path(f).name.split("_")[0][4:])
            out = Path(tmp) / (name + ".ppm"); run(tb, f, out)
            tier, payload = decode.decode(str(out))
            import numpy as np, tpg
            from PIL import Image
            want = tpg.to_rgb(np.frombuffer(Path(f).read_bytes(), ">u2").reshape(H, W))      # what a Pocket screenshot should hold
            assert (np.asarray(Image.open(out).convert("RGB")) == want).all(), name + ": frame differs from the expanded picture"
            row = [l.split("\t") for l in (bins / "manifest.tsv").read_text().splitlines()[1:] if l.split("\t")[2] == name][0]
            assert tier == row[3] and payload == expect(page, int(row[4]), name, tier, W, H), name
            print("ok", name, tier, len(payload), "bytes through the core")


def test_swap_switches():
    if not shutil.which("iverilog"):
        import pytest; pytest.skip("iverilog not installed")
    with tempfile.TemporaryDirectory() as tmp:
        tb, bins = build_tb(tmp), render_bins(tmp)
        f = glob.glob(str(bins / ("page*_L-sample_%dx%d.bin" % (W, H))))[0]
        raw = Path(f).read_bytes()
        swapped_bytes = b"".join(raw[i + 1:i + 2] + raw[i:i + 1] for i in range(0, len(raw), 2))
        swapped_pixels = b"".join(raw[i + 2:i + 4] + raw[i:i + 2] for i in range(0, len(raw), 4))
        for label, data, flags in (("bytes", swapped_bytes, ["sb"]), ("pixels", swapped_pixels, ["sp"]), ("both", b"".join(swapped_bytes[i + 2:i + 4] + swapped_bytes[i:i + 2] for i in range(0, len(raw), 4)), ["sb", "sp"])):
            p = Path(tmp) / (label + ".bin"); p.write_bytes(data)
            out = Path(tmp) / (label + ".ppm"); run(tb, p, out, flags)
            assert decode.decode(str(out))[1][:40] == expect(0, 256, "L-sample", "L", W, H)[:40], label
        # and without the switch the swapped file must NOT decode (the switch is what fixes it)
        p = Path(tmp) / "nosw.bin"; p.write_bytes(swapped_bytes); out = Path(tmp) / "nosw.ppm"; run(tb, p, out)
        try:
            decode.decode(str(out)); assert False, "a byte-swapped file decoded without the switch"
        except ValueError:
            pass
        print("ok swap switches")


if __name__ == "__main__":
    test_pages_through_the_core(); test_swap_switches(); print("ok")
