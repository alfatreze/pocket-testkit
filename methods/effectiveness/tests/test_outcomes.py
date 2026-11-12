"""Tests for methods/effectiveness/tools/outcomes.py: validation rules, add/confirm/ingest/report, and mutants of the tool (run: python3 test_outcomes.py [--mutants], or pytest)."""
import copy, json, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent; TOOL = HERE.parent / "tools/outcomes.py"; EXAMPLE = HERE.parent / "examples/outcomes.example.jsonl"
sys.path.insert(0, str(TOOL.parent))
GOOD = {"schema": 1, "id": "o-001", "date": "2026-11-11", "project": "p-a", "method": "fuzzing", "technique": "t", "target": {"kind": "parser"}, "label": "host", "cost": {"setup_min": 100, "run_min": 10, "human_min": None},
        "outcome": "bug-found", "findings": [{"kind": "design-bug", "severity": "medium", "would_otherwise_surface": "field", "summary": "s"}], "mutation": {"killed": 3, "total": 4}}
def run(tool, *args): r = subprocess.run([sys.executable, str(tool), *args], capture_output=True, text=True); return r.returncode, r.stdout + r.stderr
def errs(mod, **ch):
    r = copy.deepcopy(GOOD)
    for k, v in ch.items():
        if v is None: r.pop(k, None)
        else: r[k] = v
    return mod.validate_record(r)
def checks(tool=TOOL):
    import importlib.util
    spec = importlib.util.spec_from_file_location("outcomes_under_test", tool); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    f = []
    def ck(name, cond, extra=None):
        if not cond: f.append(name + ("" if extra is None else " " + str(extra)[:300]))
    ck("a good record validates", errs(mod) == [])
    ck("wrong schema", errs(mod, schema=2) != []); ck("unknown method", errs(mod, method="magic") != []); ck("unknown label", errs(mod, label="trust-me") != []); ck("bad date", errs(mod, date="11/11/2026") != [])
    ck("month-only date is fine", errs(mod, date="2026-11") == []); ck("unknown target", errs(mod, target={"kind": "x"}) != []); ck("negative cost", errs(mod, cost={"setup_min": -1}) != [])
    ck("null cost is fine", errs(mod, cost={"setup_min": None, "run_min": None, "human_min": None}) == []); ck("string cost", errs(mod, cost={"run_min": "5"}) != [])
    ck("bug-found needs a real finding", errs(mod, findings=[{"kind": "test-gap", "severity": "low", "would_otherwise_surface": "never", "summary": "s"}]) != [])
    ck("clean cannot carry a design bug", errs(mod, outcome="clean") != [])
    ck("clean with a test gap is fine", errs(mod, outcome="clean", findings=[{"kind": "test-gap", "severity": "low", "would_otherwise_surface": "never", "summary": "s"}]) == [])
    ck("artefact-only needs findings", errs(mod, outcome="artefact-only", findings=[]) != []); ck("artefact-only with an artefact is fine", errs(mod, outcome="artefact-only", findings=[{"kind": "tool-artefact", "severity": "low", "would_otherwise_surface": "never", "summary": "s"}]) == [])
    ck("finding without a summary", errs(mod, findings=[{"kind": "design-bug", "severity": "low", "would_otherwise_surface": "field", "summary": ""}]) != [])
    ck("mutation killed above total", errs(mod, mutation={"killed": 5, "total": 4}) != []); ck("bad confirmed_by", errs(mod, confirmed_by={"label": "pocket"}) != [])
    ck("good confirmed_by", errs(mod, confirmed_by={"label": "pocket", "note": "agreed"}) == [])
    with tempfile.TemporaryDirectory() as t:
        t = Path(t); a = t / "a.jsonl"
        rc, out = run(tool, "add", str(a), "--project", "p-a", "--method", "formal", "--technique", "k-induction", "--target", "arbiter", "--label", "formal-unbounded", "--outcome", "clean", "--cost", "setup=120,run=1", "--mutation", "7/7", "--date", "2026-11-12")
        ck("add works", rc == 0 and "added o-001" in out); rc, out = run(tool, "add", str(a), "--project", "p-a", "--method", "fuzzing", "--technique", "x", "--target", "parser", "--label", "host", "--outcome", "bug-found", "--finding", "design-bug:high:field:wrap", "--date", "2026-11-12")
        ck("second add gets o-002", rc == 0 and "o-002" in out); rc, out = run(tool, "add", str(a), "--project", "p-a", "--method", "fuzzing", "--technique", "x", "--target", "parser", "--label", "host", "--outcome", "bug-found", "--date", "2026-11-12")
        ck("add refuses an invalid record", rc == 1 and "bug-found needs" in out and len(a.read_text().splitlines()) == 2)
        rc, out = run(tool, "add", str(a), "--id", "o-001", "--project", "p-a", "--method", "formal", "--technique", "k", "--target", "fsm", "--label", "formal-bounded", "--outcome", "clean", "--date", "2026-11-12"); ck("add refuses a duplicate id", rc == 1 and "already" in out)
        rc, out = run(tool, "confirm", str(a), "o-002", "--label", "pocket", "--note", "device agreed"); ck("confirm works", rc == 0 and json.loads(a.read_text().splitlines()[1])["confirmed_by"]["label"] == "pocket")
        rc, out = run(tool, "confirm", str(a), "o-999", "--label", "pocket", "--note", "x"); ck("confirm of an unknown id fails", rc == 1)
        rc, out = run(tool, "validate", str(a)); ck("validate passes", rc == 0 and "2 record(s) ok" in out)
        bad = t / "bad.jsonl"; bad.write_text(a.read_text() + "{not json\n" + json.dumps({"schema": 1}) + "\n"); rc, out = run(tool, "validate", str(bad)); ck("validate reports bad lines", rc == 1 and "not JSON" in out and "missing or empty" in out)
        b = t / "proj-b"; b.mkdir(); (b / "outcomes.jsonl").write_text(json.dumps(dict(GOOD, project="p-b", id="o-001")) + "\n" + json.dumps(dict(GOOD, project="p-b", id="o-001")) + "\n" + json.dumps(dict(GOOD, project="p-b", id="o-002", method="formal", label="formal-unbounded", outcome="clean", findings=[])) + "\n")
        lib = t / "lib.jsonl"; rc, out = run(tool, "ingest", str(lib), str(a), str(b), str(bad)); ck("ingest pools two projects, skips the duplicate and the bad lines", rc == 0 and "4 record(s) from 2 project(s)" in out and "duplicate skipped" in out and "skipped:" in out, out)
        rc, out = run(tool, "report", str(lib)); ck("report has the method table", rc == 0 and "By method" in out and "By target kind" in out and "fuzzing" in out and "formal" in out, out)
        rc, md = run(tool, "report", str(lib), "--md"); ck("markdown report", "| By method |" in md and "|---|" in md)
        recs = [json.loads(l) for l in lib.read_text().splitlines()]; fz = [r for r in recs if r["method"] == "fuzzing"]
        ck("two projects pooled", {r["project"] for r in recs} == {"p-a", "p-b"})
        r1, o1 = run(tool, "report", str(lib)); line = [l for l in o1.splitlines() if l.startswith("fuzzing")][0].split(); ck("fuzzing row: 2 runs, 2 projects, 2 design bugs", line[1] == "2" and line[2] == "2" and line[4] == "2" and line[5] == "2", line)
        ck("bugs per 100 min = 100 * bugs / (setup+run), over the records that have a cost", line[9] == "0.9", line)
        rc, out = run(tool, "validate", str(EXAMPLE)); ck("the shipped example validates", rc == 0, out)
    return f
MUT = [("if r.get(\"outcome\") == \"bug-found\" and not any", "if False and not any"), ("if r.get(\"outcome\") == \"clean\" and isinstance(f, list) and any", "if False and isinstance(f, list) and any"),
       ("not 0 <= m[\"killed\"] <= m[\"total\"]", "False"), ("if key in seen: print", "if False: print"), ("REAL = (\"design-bug\", \"spec-gap\")", "REAL = (\"design-bug\", \"spec-gap\", \"test-gap\")"),
       ("if any(x.get(\"id\") == r[\"id\"] for x in existing)", "if False"), ("and not DATE.match", "and False and not DATE.match"), ("v < 0)", "v < -9)"), ("late = [f for f in real if f[\"would_otherwise_surface\"] in (\"pocket\", \"field\", \"never\")]", "late = []")]
def test_outcomes(): assert checks() == []
if __name__ == "__main__":
    f = checks(); [print("FAIL:", x) for x in f]; bad = 0
    if "--mutants" in sys.argv:
        src = TOOL.read_text()
        for a, b in MUT:
            assert a in src, a
            with tempfile.TemporaryDirectory() as t:
                m = Path(t) / "outcomes.py"; m.write_text(src.replace(a, b, 1)); k = checks(m)
            print("killed  " if k else "SURVIVED", a[:56]); bad += not k
    print("OUTCOMES TEST", "PASSED" if not f and not bad else "FAILED"); sys.exit(1 if f or bad else 0)
