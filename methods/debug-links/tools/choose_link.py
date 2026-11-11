#!/usr/bin/env python3
"""Pick a debug link for an Analogue Pocket core from a few project facts.

An AI agent (or a person) fills in the facts from the project, runs this, and gets a ranked
list with reasons and caveats. The rules mirror methods/debug-links/CHOOSING.md; change both
together. Costs are NOT measured here: every cost statement is a reason to measure, not a fact.

  python3 tools/choose_link.py --where desk --need registers --has-regbus --headroom ok
  python3 tools/choose_link.py --json facts.json
"""
import argparse
import json
import sys

NEEDS = ("registers", "memory", "stream", "signals", "post-hoc")


def choose(f: dict):
    """f keys: where (desk|field), need (see NEEDS), third_party, has_blaster, has_regbus,
    has_avalon, headroom (low|ok), fast_events, nios_tools, has_cpu."""
    where = f.get("where", "desk")
    need = f.get("need", "registers")
    out = []  # (name, score, reasons[])

    def add(name, score, *reasons):
        out.append([name, score, list(reasons)])

    if where != "desk" or f.get("third_party") or need == "post-hoc" or not f.get("has_blaster", True):
        why = []
        if where != "desk": why.append("not at a desk: no cable")
        if f.get("third_party"): why.append("a third party has to produce the data")
        if need == "post-hoc": why.append("a record kept next to the build is wanted")
        if not f.get("has_blaster", True): why.append("no genuine USB Blaster")
        add("report-code (grid or QR)", 100, *why, "screenshot also carries core name and version")
        add("debug event log (target 0152)", 60, "no extra hardware; needs a core-side sender and Debug Logging on")
        if need == "stream" and not f.get("has_blaster", True):
            add("link-port or devkit UART", 50, "needs link_port true and cartridge_adapter 0 (powers the cart port)")
        return _rank(out)

    reg = f.get("has_regbus") or f.get("has_cpu")
    if need in ("registers", "memory"):
        if need == "memory" or (f.get("has_avalon") and not f.get("headroom") == "low"):
            add("jtag-avalon-master", 80 if need == "memory" else 70,
                "scripted reads and writes, block transfers with master_read_memory",
                "needs Platform Designer and an Avalon-MM route to your registers",
                "Avalon clock must be at least 2x TCK, a timeout can lock the JTAG chain")
        add("vjtag-regwin (pk_vjtag_regwin)", 85 if reg else 60,
            "pure RTL, one instance, own 32-bit register window, no Platform Designer",
            "slower per access than a bus master, you own the protocol",
            *( [] if reg else ["needs a register bus to attach to; write one first"] ))
        if f.get("headroom") == "low":
            add("issp (few probes)", 55, "smallest footprint for a handful of signals", "polling misses fast events")
    if need == "signals":
        if f.get("headroom") != "low":
            add("signaltap", 90, "waveforms with triggers", "uses block RAM and logic; a probe change means a re-fit")
        add("issp (few probes)", 70 if f.get("headroom") == "low" else 50,
            "a handful of signals", "polling misses fast events: latch in the core and read afterwards")
    if need == "stream":
        add("vjtag-stream (pk_reg_stream)", 85, "console or log through the same window, host polls",
            "no Nios tools needed")
        if f.get("nios_tools") and f.get("has_avalon"):
            add("jtag-uart", 65, "a ready byte stream into Platform Designer systems",
                "needs nios2-terminal; the program can block without a terminal; one JTAG client at a time")
    if f.get("case_closed") and need in ("stream", "registers", "memory"):
        add("link-port or pad UART (3.3 V adapter)", 75,
            "works with the rear cover on; the Blaster header needs it off on a retail unit",
            "needs a UART in the core; link_port true and cartridge_adapter 0 power the cart port (keep a cart out); voltage is a mechanical switch, not core.json (KB-248)",
            "dbg_tx/dbg_rx and user1/user2 pads exist in the template, undocumented (KB-249)")
    if f.get("fast_events"):
        for o in out:
            o[2].append("fast events: latch them in the core, then read; do not poll")
    if not out:
        add("report-code (grid or QR)", 50, "no link fits the facts given")
    return _rank(out)


def _rank(out):
    return [{"link": n, "score": s, "reasons": r} for n, s, r in sorted(out, key=lambda x: -x[1])]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", help="facts as a JSON file")
    p.add_argument("--where", choices=("desk", "field"), default="desk")
    p.add_argument("--need", choices=NEEDS, default="registers")
    p.add_argument("--third-party", action="store_true")
    p.add_argument("--no-blaster", action="store_true")
    p.add_argument("--has-regbus", action="store_true")
    p.add_argument("--has-cpu", action="store_true")
    p.add_argument("--has-avalon", action="store_true")
    p.add_argument("--headroom", choices=("low", "ok"), default="ok")
    p.add_argument("--fast-events", action="store_true")
    p.add_argument("--nios-tools", action="store_true")
    p.add_argument("--case-closed", action="store_true", help="retail unit, cover must stay on")
    a = p.parse_args(argv)
    f = json.load(open(a.json)) if a.json else {
        "where": a.where, "need": a.need, "third_party": a.third_party, "has_blaster": not a.no_blaster,
        "has_regbus": a.has_regbus, "has_cpu": a.has_cpu, "has_avalon": a.has_avalon,
        "headroom": a.headroom, "fast_events": a.fast_events, "nios_tools": a.nios_tools,
        "case_closed": a.case_closed}
    for r in choose(f):
        print(f"{r['score']:3d}  {r['link']}")
        for x in r["reasons"]:
            print(f"       - {x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
