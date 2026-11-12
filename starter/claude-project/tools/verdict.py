#!/usr/bin/env python3
"""Run a test ladder and print ONE verdict an agent can read instead of logs.

  python3 tools/verdict.py                      run ladder.json
  python3 tools/verdict.py --only lint,host     run some rungs;  --json prints machine output only
  python3 tools/verdict.py --record docs/outcomes/outcomes.jsonl --project p-xxxx   also append one outcome record per automatic rung (outcome clean, or failed until classified)
Each rung in ladder.json: {"name", "label", "cmd", "manual": false}. `label` is the evidence a PASS gives: code-review, host, formal-bounded, formal-unbounded,
simulation, netlist, quartus, pocket. An optional `method` (a methods/ folder name) and `target` (a target kind) are used by --record. A manual rung (a fit you launch yourself, a Pocket run by a person) is never run here and is always reported NOT RUN,
so the summary cannot claim more than was actually done. Exit 0 only if no rung failed. Evidence reached = the highest label whose rung
and every automatic rung below it passed."""
import argparse, json, subprocess, sys, time
LABELS = ["code-review", "host", "formal-bounded", "formal-unbounded", "simulation", "netlist", "quartus", "pocket"]


def run(ladder, only=None, cwd=None):
    res = []
    for r in ladder:
        if only and r["name"] not in only: continue
        if r.get("manual"):
            res.append({"name": r["name"], "label": r["label"], "status": "NOT RUN", "note": "manual rung", "secs": 0}); continue
        t = time.time()
        p = subprocess.run(r["cmd"], shell=True, cwd=cwd, capture_output=True, text=True, timeout=r.get("timeout", 3600))
        tail = (p.stdout + p.stderr).strip().splitlines()[-1:] or [""]
        res.append({"name": r["name"], "label": r["label"], "status": "PASS" if p.returncode == 0 else "FAIL",
                    "note": tail[0][:120], "secs": round(time.time() - t, 1)})
    return res


def record(res, ladder, path, project):
    """one outcome record per rung that ran (see methods/effectiveness): outcome clean on PASS, failed on FAIL (a person classifies the findings afterwards)"""
    import datetime, importlib.util, os
    here = os.path.dirname(os.path.abspath(__file__)); spec = importlib.util.spec_from_file_location("outcomes", os.path.join(here, "outcomes.py")); o = importlib.util.module_from_spec(spec); spec.loader.exec_module(o)
    by = {r["name"]: r for r in ladder}; n = 0
    existing = [json.loads(l) for l in open(path) if l.strip()] if os.path.isfile(path) else []
    nid = max([int(x["id"][2:]) for x in existing if x.get("id", "")[:2] == "o-" and x["id"][2:].isdigit()] + [0])
    with open(path, "a") as fh:
        for r in res:
            if r["status"] == "NOT RUN": continue
            nid += 1; n += 1; b = by[r["name"]]
            rec = {"schema": 1, "id": "o-%03d" % nid, "date": datetime.date.today().isoformat(), "project": project, "method": b.get("method", "other"), "technique": b.get("technique", r["name"]),
                   "target": {"kind": b.get("target", "other")}, "label": r["label"], "cost": {"setup_min": None, "run_min": max(1, round(r["secs"] / 60)), "human_min": None},
                   "outcome": "clean" if r["status"] == "PASS" else "failed", "findings": [], "notes": "recorded by verdict.py: " + r["note"][:120]}
            assert not o.validate_record(rec), o.validate_record(rec); fh.write(json.dumps(rec, sort_keys=True) + "\n")
    print("recorded %d outcome(s) in %s" % (n, path))


def summarise(res):
    failed = [r["name"] for r in res if r["status"] == "FAIL"]
    reached = None
    for lab in LABELS:                       # highest label with everything at or below it passing (manual rungs break the chain)
        rungs = [r for r in res if LABELS.index(r["label"]) <= LABELS.index(lab)]
        if rungs and all(r["status"] == "PASS" for r in rungs) and any(r["label"] == lab for r in rungs): reached = lab
        elif any(r["label"] == lab for r in rungs): break
    return {"ok": not failed, "failed": failed, "evidence_reached": reached,
            "passed": [r["name"] for r in res if r["status"] == "PASS"], "not_run": [r["name"] for r in res if r["status"] == "NOT RUN"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="ladder.json"); ap.add_argument("--only"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--record", help="append an outcome record per automatic rung to this JSONL file (needs tools/outcomes.py)"); ap.add_argument("--project", default="p-unset")
    a = ap.parse_args(argv)
    ladder = json.load(open(a.config))
    for r in ladder:
        if r["label"] not in LABELS: sys.exit("unknown evidence label %r (use %s)" % (r["label"], ", ".join(LABELS)))
    res = run(ladder, a.only.split(",") if a.only else None)
    s = summarise(res)
    if a.record: record(res, ladder, a.record, a.project)
    if not a.json:
        for r in res: print("%-8s %-12s %-14s %5.1fs  %s" % (r["status"], r["name"], r["label"], r["secs"], r["note"]))
        print("VERDICT %s | failed: %s | evidence reached: %s | not run: %s" % ("OK" if s["ok"] else "FAIL", ",".join(s["failed"]) or "-",
              s["evidence_reached"] or "none", ",".join(s["not_run"]) or "-"))
    print(json.dumps({"results": res, **s}) if a.json else "")
    return 0 if s["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
