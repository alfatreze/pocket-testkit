#!/usr/bin/env python3
"""Record what a test method did and found, and pool records from many projects into a library of which methods paid off.

  outcomes.py add FILE --method M --technique "..." --target KIND --label L --outcome O [--finding KIND:SEVERITY:SURFACE:"summary" ...] [--cost setup=240,run=5,human=20]
                       [--mutation KILLED/TOTAL] [--project KEY] [--date YYYY-MM-DD] [--ref TEXT] [--notes TEXT] [--tool TEXT] [--id ID]
  outcomes.py validate FILE...                    check every record; exit 1 on the first problem list
  outcomes.py confirm FILE ID --label pocket --note "..." [--date D]    attach a later cross-check (a simulated result confirmed or contradicted on the device)
  outcomes.py ingest OUT.jsonl FILE_OR_DIR...     pool records from several projects into one library (validated, de-duplicated by project+id; invalid records are reported and skipped)
  outcomes.py report FILE_OR_DIR... [--md]        the effectiveness table: per method and per target kind

A record is one JSON object per line (JSONL). Fields (schema 1; reference: this file, `schema/outcome.schema.json` for other tools):
  schema 1 | id (unique in the project) | date (YYYY-MM-DD or YYYY-MM) | project (an anonymous key you choose, never a name) | method (METHODS) | technique (short text)
  tool (optional) | target.kind (TARGETS) | label (LABELS, the evidence this result gives) | cost {setup_min, run_min, human_min: integer minutes, estimates, any may be null}
  outcome (OUTCOMES) | findings [{kind (FINDING_KINDS), severity (SEVERITIES), would_otherwise_surface (SURFACES: where it would have shown up if this method had not found it), summary}]
  mutation {killed, total} (optional) | confirmed_by {label, date, note} (optional, added later) | ref (a project-local pointer, e.g. an audit id) | notes
What the library answers: per method, how often it found a real design bug, how much it cost, how often its alarms were only artefacts of the test setup (tool-artefact, model-fault),
how severe the bugs were and how late they would have been found. A record with no cost (setup and run both null) is left out of the bugs-per-minute rate. Counts are small and every cost is an estimate: read the table as a prompt for judgement, not as a measurement.
Free text is yours to keep private: do not put project, person or product names in `project`, `technique`, `summary` or `notes` of a record you intend to share."""
import argparse, json, re, sys
from collections import defaultdict
from pathlib import Path

METHODS = ["file-checks", "host-tests", "fuzzing", "formal", "simulation", "timing-fit", "report-codes", "debug-links", "pocket-native", "ci", "device-run", "other"]
TARGETS = ["parser", "rtl-block", "fsm", "arbiter", "fifo", "cdc", "datapath", "cpu-firmware", "whole-core", "build-flow", "installer", "ui", "timing", "other"]
LABELS = ["code-review", "host", "formal-bounded", "formal-unbounded", "simulation", "netlist", "quartus", "pocket"]
OUTCOMES = ["bug-found", "clean", "artefact-only", "inconclusive", "failed", "not-run"]        # failed = the run failed and nobody has classified it yet
FINDING_KINDS = ["design-bug", "test-gap", "tool-artefact", "model-fault", "spec-gap"]
SEVERITIES = ["low", "medium", "high"]
SURFACES = ["never", "simulation", "fit", "pocket", "field"]
REAL = ("design-bug", "spec-gap")                    # findings that count as a real bug in what is being built
NOISE = ("tool-artefact", "model-fault")             # alarms that were the test setup's fault
DATE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")

def validate_record(r):
    e = []
    if not isinstance(r, dict): return ["not an object"]
    if r.get("schema") != 1: e.append("schema must be 1")
    for k in ("id", "date", "project", "method", "technique", "label", "outcome"):
        if not isinstance(r.get(k), str) or not r.get(k): e.append("missing or empty: " + k)
    if isinstance(r.get("date"), str) and not DATE.match(r["date"]): e.append("date must be YYYY-MM-DD or YYYY-MM")
    for k, allowed in (("method", METHODS), ("label", LABELS), ("outcome", OUTCOMES)):
        if r.get(k) not in allowed and isinstance(r.get(k), str): e.append("%s %r not in %s" % (k, r[k], allowed))
    t = r.get("target")
    if not isinstance(t, dict) or t.get("kind") not in TARGETS: e.append("target.kind must be one of %s" % TARGETS)
    c = r.get("cost")
    if not isinstance(c, dict): e.append("cost must be an object")
    else:
        for k in ("setup_min", "run_min", "human_min"):
            v = c.get(k)
            if v is not None and (not isinstance(v, int) or isinstance(v, bool) or v < 0): e.append("cost.%s must be a non-negative integer or null" % k)
    f = r.get("findings")
    if not isinstance(f, list): e.append("findings must be a list")
    else:
        for i, x in enumerate(f):
            if not isinstance(x, dict): e.append("finding %d not an object" % i); continue
            if x.get("kind") not in FINDING_KINDS: e.append("finding %d kind not in %s" % (i, FINDING_KINDS))
            if x.get("severity") not in SEVERITIES: e.append("finding %d severity not in %s" % (i, SEVERITIES))
            if x.get("would_otherwise_surface") not in SURFACES: e.append("finding %d would_otherwise_surface not in %s" % (i, SURFACES))
            if not isinstance(x.get("summary"), str) or not x.get("summary"): e.append("finding %d needs a summary" % i)
    if r.get("outcome") == "bug-found" and not any(isinstance(x, dict) and x.get("kind") in REAL for x in (f if isinstance(f, list) else [])): e.append("outcome bug-found needs a design-bug or spec-gap finding")
    if r.get("outcome") == "clean" and isinstance(f, list) and any(isinstance(x, dict) and x.get("kind") in REAL for x in f): e.append("outcome clean cannot carry a design-bug or spec-gap finding")
    if r.get("outcome") == "artefact-only" and isinstance(f, list) and not f: e.append("outcome artefact-only needs the artefact findings")
    m = r.get("mutation")
    if m is not None and (not isinstance(m, dict) or not isinstance(m.get("killed"), int) or not isinstance(m.get("total"), int) or not 0 <= m["killed"] <= m["total"]): e.append("mutation must be {killed, total} with 0 <= killed <= total")
    cb = r.get("confirmed_by")
    if cb is not None and (not isinstance(cb, dict) or cb.get("label") not in LABELS or not isinstance(cb.get("note"), str)): e.append("confirmed_by must be {label, note[, date]}")
    return e

def load(path):
    out, errs = [], []
    for p in ([Path(path)] if Path(path).is_file() else sorted(Path(path).rglob("*.jsonl"))):
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if not line.strip(): continue
            try: r = json.loads(line)
            except ValueError as ex: errs.append("%s:%d: not JSON (%s)" % (p, n, ex)); continue
            e = validate_record(r)
            if e: errs.append("%s:%d (%s): %s" % (p, n, r.get("id", "?") if isinstance(r, dict) else "?", "; ".join(e)))
            else: out.append(r)
    return out, errs

def parse_finding(s):
    parts = s.split(":", 3)
    if len(parts) != 4: raise SystemExit("--finding KIND:SEVERITY:SURFACE:summary, got %r" % s)
    return {"kind": parts[0], "severity": parts[1], "would_otherwise_surface": parts[2], "summary": parts[3]}

def parse_cost(s):
    c = {"setup_min": None, "run_min": None, "human_min": None}
    for kv in filter(None, (s or "").split(",")):
        k, v = kv.split("="); c[k + "_min"] = int(v)
    return c

def cmd_add(a):
    p = Path(a.file); existing = [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.is_file() else []
    n = max([int(m.group(1)) for x in existing for m in [re.match(r"o-(\d+)$", x.get("id", ""))] if m] + [0]) + 1
    r = {"schema": 1, "id": a.id or "o-%03d" % n, "date": a.date, "project": a.project, "method": a.method, "technique": a.technique, "target": {"kind": a.target}, "label": a.label,
         "cost": parse_cost(a.cost), "outcome": a.outcome, "findings": [parse_finding(f) for f in a.finding]}
    if a.tool: r["tool"] = a.tool
    if a.mutation: k, t = a.mutation.split("/"); r["mutation"] = {"killed": int(k), "total": int(t)}
    if a.ref: r["ref"] = a.ref
    if a.notes: r["notes"] = a.notes
    e = validate_record(r)
    if any(x.get("id") == r["id"] for x in existing): e.append("id %s already in %s" % (r["id"], a.file))
    if e: print("record rejected:\n  " + "\n  ".join(e)); return 1
    with p.open("a") as fh: fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("added", r["id"]); return 0

def cmd_confirm(a):
    p = Path(a.file); recs = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    for r in recs:
        if r["id"] == a.id: r["confirmed_by"] = {"label": a.label, "note": a.note, **({"date": a.date} if a.date else {})}; break
    else: print("no record", a.id); return 1
    e = validate_record(r)
    if e: print("rejected:", "; ".join(e)); return 1
    p.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in recs)); print("confirmed", a.id); return 0

def cmd_validate(a):
    bad = 0
    for f in a.files:
        recs, errs = load(f); bad += len(errs); print("%s: %d record(s) ok, %d problem(s)" % (f, len(recs), len(errs)))
        for x in errs: print("  " + x)
    return 1 if bad else 0

def cmd_ingest(a):
    seen, out, bad = {}, [], 0
    for f in a.inputs:
        recs, errs = load(f); bad += len(errs)
        for x in errs: print("skipped:", x)
        for r in recs:
            key = (r["project"], r["id"])
            if key in seen: print("duplicate skipped:", key); continue
            seen[key] = 1; out.append(r)
    out.sort(key=lambda r: (r["project"], r["date"], r["id"]))
    Path(a.out).write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in out)); print("%d record(s) from %d project(s) -> %s (%d skipped)" % (len(out), len({r["project"] for r in out}), a.out, bad))
    return 0

def total_min(r): return sum(v or 0 for v in (r["cost"].get("setup_min"), r["cost"].get("run_min")))

def group(recs, keyf):
    g = defaultdict(list)
    for r in recs: g[keyf(r)].append(r)
    return g

def row(name, rs):
    real = [f for r in rs for f in r["findings"] if f["kind"] in REAL]; noise = [f for r in rs for f in r["findings"] if f["kind"] in NOISE]
    gaps = [f for r in rs for f in r["findings"] if f["kind"] == "test-gap"]
    costed = [r for r in rs if r["cost"].get("setup_min") is not None or r["cost"].get("run_min") is not None]          # a record without a cost cannot enter the rate
    cost = sum(total_min(r) for r in costed); hum = sum(r["cost"].get("human_min") or 0 for r in rs)
    rate_bugs = sum(1 for r in costed for f in r["findings"] if f["kind"] in REAL)
    late = [f for f in real if f["would_otherwise_surface"] in ("pocket", "field", "never")]
    mk = sum(r["mutation"]["killed"] for r in rs if r.get("mutation")); mt = sum(r["mutation"]["total"] for r in rs if r.get("mutation"))
    conf = sum(1 for r in rs if r.get("confirmed_by"))
    return {"name": name, "runs": len(rs), "projects": len({r["project"] for r in rs}), "bugs": len(real), "late_bugs": len(late), "gaps": len(gaps), "noise": len(noise), "minutes": cost, "human_min": hum,
            "bugs_per_100min": round(100.0 * rate_bugs / cost, 1) if cost else None, "runs_with_bug": sum(1 for r in rs if r["outcome"] == "bug-found"), "mutation": "%d/%d" % (mk, mt) if mt else "-", "confirmed": conf}

def render(recs, md):
    rows = [row(k, v) for k, v in sorted(group(recs, lambda r: r["method"]).items())]; rows2 = [row(k, v) for k, v in sorted(group(recs, lambda r: r["target"]["kind"]).items())]
    hdr = ["", "runs", "projects", "runs with a bug", "design bugs", "of them found late*", "test gaps", "artefacts", "minutes (setup+run)", "bugs / 100 min", "mutants killed", "confirmed later"]
    def line(x): return [x["name"], x["runs"], x["projects"], x["runs_with_bug"], x["bugs"], x["late_bugs"], x["gaps"], x["noise"], x["minutes"], "-" if x["bugs_per_100min"] is None else x["bugs_per_100min"], x["mutation"], x["confirmed"]]
    out = []
    for title, rs in (("By method", rows), ("By target kind", rows2)):
        h = [title] + hdr[1:]
        if md: out += ["", "### " + title, "", "| " + " | ".join(h) + " |", "|" + "---|" * len(h)] + ["| " + " | ".join(str(c) for c in line(x)) + " |" for x in rs]
        else: out += [""] + ["  ".join("%-16s" % c if i == 0 else "%8s" % c for i, c in enumerate(h))] + ["  ".join("%-16s" % c if i == 0 else "%8s" % c for i, c in enumerate(line(x))) for x in rs]
    note = "* found late = would otherwise have surfaced on the device, in the field, or never. Artefacts = alarms that were the test setup's fault (tool-artefact, model-fault). Costs are estimates; counts are small."
    return "\n".join(out + ["", note, "%d record(s), %d project(s)" % (len(recs), len({r["project"] for r in recs}))])

def cmd_report(a):
    recs = []
    for f in a.inputs:
        rs, errs = load(f); recs += rs
        for x in errs: print("skipped:", x, file=sys.stderr)
    seen = set(); uniq = []
    for r in recs:
        k = (r["project"], r["id"])
        if k not in seen: seen.add(k); uniq.append(r)
    print(render(uniq, a.md)); return 0

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add"); p.add_argument("file"); p.add_argument("--method", required=True); p.add_argument("--technique", required=True); p.add_argument("--target", required=True); p.add_argument("--label", required=True)
    p.add_argument("--outcome", required=True); p.add_argument("--finding", action="append", default=[]); p.add_argument("--cost", default=""); p.add_argument("--mutation"); p.add_argument("--project", default="p-unset")
    p.add_argument("--date", default=__import__("datetime").date.today().isoformat()); p.add_argument("--ref"); p.add_argument("--notes"); p.add_argument("--tool"); p.add_argument("--id"); p.set_defaults(f=cmd_add)
    p = sub.add_parser("validate"); p.add_argument("files", nargs="+"); p.set_defaults(f=cmd_validate)
    p = sub.add_parser("confirm"); p.add_argument("file"); p.add_argument("id"); p.add_argument("--label", required=True); p.add_argument("--note", required=True); p.add_argument("--date"); p.set_defaults(f=cmd_confirm)
    p = sub.add_parser("ingest"); p.add_argument("out"); p.add_argument("inputs", nargs="+"); p.set_defaults(f=cmd_ingest)
    p = sub.add_parser("report"); p.add_argument("inputs", nargs="+"); p.add_argument("--md", action="store_true"); p.set_defaults(f=cmd_report)
    a = ap.parse_args(argv); return a.f(a)

if __name__ == "__main__":
    sys.exit(main())
