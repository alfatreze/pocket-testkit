import shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "host")); sys.path.insert(0, str(ROOT / "tools"))
import pk_link, choose_link


def test_frames():
    assert pk_link.pack_req(True, 1, 0xCAFE1234) == 0x8001CAFE1234
    assert pk_link.pack_req(False, 0x7FFF, 0) == 0x7FFF << 32
    r = pk_link.unpack_rsp((1 << 34) | (1 << 32) | 0xDEADBEEF)
    assert r == {"data": 0xDEADBEEF, "err": True, "busy": False, "overrun": True}
    try:
        pk_link.pack_req(False, 1 << 15, 0); assert False
    except ValueError:
        pass


def names(**f): return [r["link"] for r in choose_link.choose(f)]


def test_choice_rules():
    assert names(where="field", need="registers")[0].startswith("report-code")
    assert names(third_party=True)[0].startswith("report-code")
    assert names(has_blaster=False, need="stream")[0].startswith("report-code")
    assert names(need="registers", has_regbus=True)[0].startswith("vjtag-regwin")
    assert names(need="memory", has_avalon=True)[0] == "jtag-avalon-master"
    assert names(need="signals", headroom="ok")[0] == "signaltap"
    assert "signaltap" not in names(need="signals", headroom="low")
    assert names(need="stream")[0].startswith("vjtag-stream")
    assert any(n.startswith("link-port") for n in names(need="stream", case_closed=True))


def test_rtl_sims():
    if not shutil.which("iverilog"):
        import pytest; pytest.skip("iverilog not installed")
    s = ROOT / "sim"; r = ROOT / "rtl"
    for tb, srcs in (("tb_vjtag.sv", ["common/*.sv", "jtag/pk_vjtag_regwin.sv", "jtag/pk_debug_decode.sv", "stream/*.sv"]),
                     ("tb_avmm.sv", ["jtag/pk_avmm_master_to_bus.sv", "common/pk_demo_regs.sv"])):
        files = [str(p) for g in srcs for p in sorted(r.glob(g))]
        exe = f"/tmp/{tb}.vvp"
        subprocess.run(["iverilog", "-g2012", "-o", exe, str(s / tb)] + files, check=True)
        out = subprocess.run(["vvp", exe], capture_output=True, text=True, check=True).stdout
        assert "PASS" in out and "FAIL" not in out, out


if __name__ == "__main__":
    test_frames(); test_choice_rules(); test_rtl_sims(); print("ok")
