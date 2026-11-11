#!/usr/bin/env python3
"""Build c/sample/host_gallery.c and write every sample page as PNG (default: docs/img/gallery, three screen sizes).
  python3 examples/make_gallery.py [OUTDIR] [WxH ...] [--unlock]"""
import glob, os, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent


def build(exe):
    cmd = ["cc", "-O2", "-o", str(exe), str(ROOT / "c/sample/host_gallery.c")]
    if subprocess.run(cmd, capture_output=True).returncode == 0: return
    for sdk in sorted(glob.glob("/Library/Developer/CommandLineTools/SDKs/MacOSX*.sdk"), reverse=True):   # macOS: default SDK can be unusable
        if subprocess.run(cmd, capture_output=True, env={**os.environ, "SDKROOT": sdk}).returncode == 0: return
    raise SystemExit("could not build host_gallery.c")


def render(outdir, sizes=(), unlock=False):
    """Writes PNGs and manifest.tsv into outdir; returns the manifest rows as dicts."""
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp) / "host_gallery"; build(exe)
        subprocess.run([str(exe), tmp] + (["-u"] if unlock else []) + list(sizes), check=True)
        rows = []
        lines = (Path(tmp) / "manifest.tsv").read_text().splitlines()
        keys = lines[0].split("\t")
        for ln in lines[1:]:
            r = dict(zip(keys, ln.split("\t")))
            if r["file"] != "-":
                png = r["file"].replace(".ppm", ".png")
                Image.open(Path(tmp) / r["file"]).save(outdir / png); r["file"] = png
            rows.append(r)
        (outdir / "manifest.tsv").write_text("\n".join("\t".join(r[k] for k in keys) for r in [dict(zip(keys, keys))] + rows) + "\n")
    return rows


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--unlock"]
    out = args[0] if args and "x" not in args[0].lower().replace("/", "") else str(ROOT / "docs/img/gallery")
    sizes = [a for a in args if a != out]
    rows = render(out, sizes, "--unlock" in sys.argv)
    print(len(rows), "rows,", sum(1 for r in rows if r["file"] != "-"), "pictures in", out)
