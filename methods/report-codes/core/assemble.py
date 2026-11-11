#!/usr/bin/env python3
"""Assemble and package the sample-pages Pocket core. Analogue's template files are NOT in this repo (they belong to Analogue): you give
the path to your own copy of https://github.com/open-fpga/core-template and this script copies it, adds our RTL, patches three things in
core_top.v and one in the .qsf, and stops with a clear message if the template differs from what it expects.

  python3 assemble.py build   --template PATH/core-template --out BUILD_DIR        # a Quartus project in BUILD_DIR/src/fpga
  python3 assemble.py package --rbf BUILD_DIR/src/fpga/output_files/ap_core.rbf --out SD_DIR [--no-pages]
                                                                                     # an SD-card tree: Cores/, Assets/
Quartus is not run here. Build with:  cd BUILD_DIR/src/fpga && quartus_sh --flow compile ap_core   (Quartus Prime Lite 25.1 for Cyclone V)."""
import argparse, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
RTL = HERE / "rtl" / "pk_fb_video.sv"
JSON_DIR = HERE / "json"
VIDEO_ASSIGNS = [("assign video_rgb = vidout_rgb;", "assign video_rgb = pk_rgb;"), ("assign video_de = vidout_de;", "assign video_de = pk_de;"),
                 ("assign video_skip = vidout_skip;", "assign video_skip = pk_skip;"), ("assign video_vs = vidout_vs;", "assign video_vs = pk_vs;"),
                 ("assign video_hs = vidout_hs;", "assign video_hs = pk_hs;")]
INSTANCE = """// ---- pocket-testkit sample pages: a framebuffer viewer replaces the template's grey test screen ----
wire [23:0] pk_rgb; wire pk_de, pk_skip, pk_vs, pk_hs;
pk_fb_video u_pk_fb (
    .clk_bridge ( clk_74a ), .bridge_wr ( bridge_wr ), .bridge_addr ( bridge_addr ), .bridge_wr_data ( bridge_wr_data ),
    .clk_vid ( clk_core_12288 ), .reset_n ( reset_n ),
    .rgb ( pk_rgb ), .de ( pk_de ), .skip ( pk_skip ), .vs ( pk_vs ), .hs ( pk_hs )
);
"""
CLOCK_ANCHOR = "assign video_rgb_clock = clk_core_12288;"
QSF_ANCHOR = "set_global_assignment -name VERILOG_FILE core/core_top.v"
QSF_ADD = "set_global_assignment -name SYSTEMVERILOG_FILE core/pk_fb_video.sv"
IGNORE = ("output_files", "db", "incremental_db", ".git", "simulation")


class TemplateMismatch(SystemExit):
    pass


def patch_core_top(text):
    """Returns the patched core_top.v text; raises TemplateMismatch if an anchor is missing (a different template version)."""
    for old, new in VIDEO_ASSIGNS:
        if text.count(old) != 1: raise TemplateMismatch("core_top.v: expected exactly one %r (template version differs?)" % old)
        text = text.replace(old, new)
    if text.count(CLOCK_ANCHOR) != 1: raise TemplateMismatch("core_top.v: anchor %r not found once" % CLOCK_ANCHOR)
    return text.replace(CLOCK_ANCHOR, INSTANCE + CLOCK_ANCHOR)


def patch_qsf(text):
    if text.count(QSF_ANCHOR) != 1: raise TemplateMismatch(".qsf: anchor %r not found once" % QSF_ANCHOR)
    return text.replace(QSF_ANCHOR, QSF_ANCHOR + "\n" + QSF_ADD)


def build(template, out):
    template, out = Path(template), Path(out)
    src = template / "src" / "fpga"
    if not (src / "core" / "core_top.v").exists(): raise SystemExit("not a core template: %s/src/fpga/core/core_top.v missing" % template)
    if out.exists() and any(out.iterdir()): raise SystemExit("%s is not empty; pick a new build directory" % out)
    dst = out / "src" / "fpga"
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*IGNORE))
    (dst / "core" / "core_top.v").write_text(patch_core_top((dst / "core" / "core_top.v").read_text()))
    (dst / "ap_core.qsf").write_text(patch_qsf((dst / "ap_core.qsf").read_text()))
    shutil.copy(RTL, dst / "core" / "pk_fb_video.sv")
    print("project in", dst, "\nbuild: cd %s && quartus_sh --flow compile ap_core" % dst)


def reverse_bits(data):
    table = bytes(int("{:08b}".format(b)[::-1], 2) for b in range(256))
    return data.translate(table)


def package(rbf, out, pages=True, size=(320, 240)):
    out = Path(out)
    meta = json.loads((JSON_DIR / "core.json").read_text())["core"]["metadata"]
    name = "%s.%s" % (meta["author"], meta["shortname"])
    core = out / "Cores" / name; core.mkdir(parents=True, exist_ok=True)
    for f in JSON_DIR.glob("*.json"): shutil.copy(f, core / f.name)
    (core / "bitstream.rbf_r").write_bytes(reverse_bits(Path(rbf).read_bytes()))
    if pages:
        assets = out / "Assets" / "_none" / name; assets.mkdir(parents=True, exist_ok=True)
        sys.path.insert(0, str(HERE.parent / "examples")); import make_gallery
        with tempfile.TemporaryDirectory() as t:
            exe = Path(t) / "host_gallery"; make_gallery.build(exe)
            subprocess.run([str(exe), str(assets), "-b", "-u", "%dx%d" % size], check=True)
        (assets / "manifest.tsv").unlink(missing_ok=True)
    print("SD tree in", out, "(core folder %s). Copy Cores/ and Assets/ to the card root after the owner approves." % name)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--template", required=True); b.add_argument("--out", required=True)
    p = sub.add_parser("package"); p.add_argument("--rbf", required=True); p.add_argument("--out", required=True); p.add_argument("--no-pages", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "build": build(a.template, a.out)
    else: package(a.rbf, a.out, not a.no_pages)


if __name__ == "__main__":
    main()
