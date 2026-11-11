"""Starter kit tools: verdict ladder honesty, Pocket JSON checks, package check."""
import json, subprocess, sys, tempfile
from pathlib import Path
T = Path(__file__).resolve().parent.parent / "claude-project" / "tools"
sys.path.insert(0, str(T))
import verdict, check_pocket_json, check_package


def test_verdict_cannot_overclaim():
    ladder = [{"name": "a", "label": "host", "cmd": "true"}, {"name": "b", "label": "simulation", "cmd": "true"},
              {"name": "c", "label": "quartus", "cmd": "x", "manual": True}, {"name": "d", "label": "pocket", "cmd": "x", "manual": True}]
    s = verdict.summarise(verdict.run(ladder))
    assert s["ok"] and s["evidence_reached"] == "simulation" and s["not_run"] == ["c", "d"], s
    ladder[1]["cmd"] = "false"
    s = verdict.summarise(verdict.run(ladder))
    assert not s["ok"] and s["failed"] == ["b"] and s["evidence_reached"] == "host", s
    s = verdict.summarise(verdict.run([{"name": "a", "label": "pocket", "cmd": "true"}]))
    assert s["evidence_reached"] == "pocket"          # an automatic rung labelled pocket (for example a scripted device run) may reach it


def test_unfilled_makefile_stub_fails():
    mk = T.parent / "Makefile"
    r = subprocess.run(["make", "-s", "-f", str(mk), "test-host"], capture_output=True, text=True)
    assert r.returncode != 0 and "not implemented" in r.stdout


def good_core(d):
    core = {"core": {"magic": "APF_VER_1", "metadata": {"platform_ids": ["x"], "shortname": d.name, "description": "d", "author": "a", "url": "u",
                     "version": "1.0.0", "date_release": "2026-11-11"},
                     "framework": {"target_product": "Analogue Pocket", "version_required": "2.1"},
                     "cores": [{"id": 0, "name": "default", "filename": "core.rbf_r"}]}}
    (d / "core.json").write_text(json.dumps(core)); (d / "core.rbf_r").write_bytes(b"x")
    (d / "data.json").write_text(json.dumps({"data": {"magic": "APF_VER_1", "data_slots": [{"name": "rom", "id": 1}]}}))


def test_pocket_json():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "Me.Core"; d.mkdir(); good_core(d)
        assert check_pocket_json.check(d) == ([], [])
        bad = json.loads((d / "core.json").read_text()); bad["core"]["metadata"]["shortname"] = "Other.Core"; bad["core"]["magic"] = "NOPE"
        (d / "core.json").write_text(json.dumps(bad))
        e, _ = check_pocket_json.check(d)
        assert any("must match the folder" in x for x in e) and any("magic" in x for x in e), e
        (d / "data.json").write_text("{not json")
        assert any("invalid JSON" in x for x in check_pocket_json.check(d)[0])
        (d / "data.json").write_text(json.dumps({"data": {"magic": "APF_VER_1", "data_slots": [{"name": "a", "id": 1}, {"name": "b", "id": 1}]}}))
        assert any("duplicate slot ids" in x for x in check_pocket_json.check(d)[0])


def test_package():
    with tempfile.TemporaryDirectory() as t:
        a, b = Path(t) / "a", Path(t) / "b"; a.write_bytes(b"1"); b.write_bytes(b"1")
        assert subprocess.run([sys.executable, str(T / "check_package.py"), str(a), str(b)], capture_output=True).returncode == 0
        b.write_bytes(b"2")
        assert subprocess.run([sys.executable, str(T / "check_package.py"), str(a), str(b)], capture_output=True).returncode == 1


if __name__ == "__main__":
    test_verdict_cannot_overclaim(); test_unfilled_makefile_stub_fails(); test_pocket_json(); test_package(); print("ok")
