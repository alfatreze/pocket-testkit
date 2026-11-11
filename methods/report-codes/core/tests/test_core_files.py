"""The core's JSON files pass the kit's validator, the template patches apply (and fail loudly on a different template), and packaging
reverses bits. Analogue's template is not needed: the patch functions are tested on the exact anchor lines."""
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT.parents[2] / "starter" / "claude-project" / "tools"))
import assemble, check_pocket_json

TOP = "\n".join(["module core_top();", "assign video_rgb_clock = clk_core_12288;"] + [o for o, _ in assemble.VIDEO_ASSIGNS] + ["endmodule"])
QSF = "set_global_assignment -name QIP_FILE apf/apf.qip\nset_global_assignment -name VERILOG_FILE core/core_top.v\n"


def test_json_files_validate():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "alfatreze.PKPages"; d.mkdir()
        for f in assemble.JSON_DIR.glob("*.json"): (d / f.name).write_bytes(f.read_bytes())
        (d / "bitstream.rbf_r").write_bytes(b"x")
        assert check_pocket_json.check(d) == ([], []), check_pocket_json.check(d)
        slot = json.loads((d / "data.json").read_text())["data"]["data_slots"][0]
        assert slot["size_exact"] == 320 * 240 * 2 and slot["address"] == "0x10000000"        # the RTL's picture size and window
        assert json.loads((d / "video.json").read_text())["video"]["scaler_modes"][0]["width"] == 320


def test_patch_core_top():
    out = assemble.patch_core_top(TOP)
    assert "u_pk_fb" in out and "assign video_rgb = pk_rgb;" in out and "vidout" not in out and out.index("u_pk_fb") < out.index("assign video_rgb_clock")
    try: assemble.patch_core_top(TOP.replace("assign video_vs = vidout_vs;", "")); assert False
    except assemble.TemplateMismatch: pass
    try: assemble.patch_core_top(TOP + "\nassign video_hs = vidout_hs;"); assert False        # two matches is also a mismatch
    except assemble.TemplateMismatch: pass
    assert "pk_fb_video.sv" in assemble.patch_qsf(QSF)
    try: assemble.patch_qsf("nothing"); assert False
    except assemble.TemplateMismatch: pass


def test_reverse_bits():
    assert assemble.reverse_bits(bytes([0x01, 0x80, 0xF0, 0xA5])) == bytes([0x80, 0x01, 0x0F, 0xA5])


def test_rtl_matches_the_window():
    s = (ROOT / "rtl" / "pk_fb_video.sv").read_text()
    assert "H_ACTIVE = 320" in s and "V_ACTIVE = 240" in s and "8'h10" in s and "8'h20" in s


if __name__ == "__main__":
    test_json_files_validate(); test_patch_core_top(); test_reverse_bits(); test_rtl_matches_the_window(); print("ok")
