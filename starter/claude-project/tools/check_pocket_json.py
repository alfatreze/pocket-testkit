#!/usr/bin/env python3
"""Cheap first check for an Analogue Pocket core folder: the Pocket gives almost no feedback on malformed JSON, so validate before copying.
  python3 tools/check_pocket_json.py path/to/Author.CoreName        exit 0 = no errors (warnings are printed)
Checks the limits listed in Analogue's developer docs (JSON files section); it is not a full schema, so a pass does not prove the Pocket
will accept the core. Limits are in LIMITS below: change them if the docs change."""
import json, re, sys
from pathlib import Path
LIMITS = {"shortname": 31, "description": 63, "author": 31, "url": 63, "version": 31}
FRAMEWORK = {"1.1", "1.2", "2.0", "2.1", "2.3"}
FILES = {"core": "core", "data": "data", "interact": "interact", "video": "video", "input": "input", "audio": "audio", "variants": "variants"}


def check(folder):
    folder = Path(folder); err, warn = [], []
    def load(name):
        p = folder / (name + ".json")
        if not p.exists(): return None
        try: d = json.loads(p.read_text())
        except ValueError as e: err.append("%s.json: invalid JSON (%s)" % (name, e)); return None
        body = d.get(name)
        if not isinstance(body, dict): err.append("%s.json: missing top-level object %r" % (name, name)); return None
        if body.get("magic") != "APF_VER_1": err.append("%s.json: magic must be APF_VER_1" % name)
        return body
    core = load("core")
    if core is None and not (folder / "core.json").exists(): err.append("core.json is required")
    if core:
        m = core.get("metadata", {})
        for k, n in LIMITS.items():
            if k in m and len(str(m[k])) > n: err.append("core.json: metadata.%s longer than %d" % (k, n))
        want = "%s.%s" % (m.get("author", ""), m.get("shortname", ""))
        if m.get("shortname") and folder.name != want: err.append("core.json: the folder must be named <author>.<shortname> = %r, not %r" % (want, folder.name))
        if m.get("date_release") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(m["date_release"])): err.append("core.json: date_release must be YYYY-MM-DD")
        if len(m.get("platform_ids", [])) > 4: err.append("core.json: more than 4 platform_ids")
        f = core.get("framework", {})
        if f.get("target_product") != "Analogue Pocket": err.append("core.json: framework.target_product must be 'Analogue Pocket'")
        if f.get("version_required") not in FRAMEWORK: warn.append("core.json: version_required %r not in %s" % (f.get("version_required"), sorted(FRAMEWORK)))
        cores = core.get("cores", [])
        if len(cores) > 8: err.append("core.json: more than 8 cores[]")
        for c in cores:
            if len(str(c.get("filename", ""))) > 15: err.append("core.json: cores[].filename longer than 15")
            elif c.get("filename") and not (folder / c["filename"]).exists(): warn.append("core.json: %s not in the folder (copy the .rbf_r)" % c["filename"])
    data = load("data")
    if data:
        slots = data.get("data_slots", []); ids = [s.get("id") for s in slots]
        if len(slots) > 32: err.append("data.json: more than 32 data_slots")
        if len(set(ids)) != len(ids): err.append("data.json: duplicate slot ids")
        for s in slots:
            if len(str(s.get("name", ""))) > 15: err.append("data.json: slot name %r longer than 15" % s.get("name"))
    inter = load("interact")
    if inter:
        v = inter.get("variables", []); ids = [x.get("id") for x in v]
        if len(v) > 16: err.append("interact.json: more than 16 variables")
        if len(set(ids)) != len(ids): err.append("interact.json: duplicate variable ids")
        for x in v:
            if len(str(x.get("name", ""))) > 23: err.append("interact.json: variable name %r longer than 23" % x.get("name"))
    video = load("video")
    if video:
        if len(video.get("scaler_modes", [])) > 8: err.append("video.json: more than 8 scaler_modes")
        if len(video.get("display_modes", [])) > 16: err.append("video.json: more than 16 display_modes")
    inp = load("input")
    if inp and len(inp.get("controllers", [])) > 4: err.append("input.json: more than 4 controllers")
    for n in ("audio", "variants"): load(n)
    return err, warn


if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    e, w = check(sys.argv[1])
    for x in w: print("warning:", x)
    for x in e: print("error:", x)
    print("OK" if not e else "FAILED: %d error(s)" % len(e))
    sys.exit(1 if e else 0)
