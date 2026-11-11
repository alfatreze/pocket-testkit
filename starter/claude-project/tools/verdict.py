#!/usr/bin/env python3
"""Run a test ladder and print ONE verdict an agent can read instead of logs.

  python3 tools/verdict.py                      run ladder.json
  python3 tools/verdict.py --only lint,host     run some rungs;  --json prints machine output only
Each rung in ladder.json: {"name", "label", "cmd", "manual": false}. `label` is the evidence a PASS gives: code-review, host, simulation,
quartus, pocket. A manual rung (a fit you launch yourself, a Pocket run by a person) is never run here and is always reported NOT RUN,
so the summary cannot claim more than was actually done. Exit 0 only if no rung failed. Evidence reached = the highest label whose rung
and every automatic rung below it passed."""
import argparse, json, subprocess, sys, time
LABELS = ["code-review", "host", "simulation", "quartus", "pocket"]


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
    a = ap.parse_args(argv)
    ladder = json.load(open(a.config))
    for r in ladder:
        if r["label"] not in LABELS: sys.exit("unknown evidence label %r (use %s)" % (r["label"], ", ".join(LABELS)))
    res = run(ladder, a.only.split(",") if a.only else None)
    s = summarise(res)
    if not a.json:
        for r in res: print("%-8s %-12s %-14s %5.1fs  %s" % (r["status"], r["name"], r["label"], r["secs"], r["note"]))
        print("VERDICT %s | failed: %s | evidence reached: %s | not run: %s" % ("OK" if s["ok"] else "FAIL", ",".join(s["failed"]) or "-",
              s["evidence_reached"] or "none", ",".join(s["not_run"]) or "-"))
    print(json.dumps({"results": res, **s}) if a.json else "")
    return 0 if s["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
