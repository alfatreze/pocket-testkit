---
name: verify-ladder
description: Run the project's test ladder and report one evidence-labelled verdict. Use after any change to code, RTL, JSON or build scripts, and before saying something works.
---

1. Run `make verdict` (or `python3 tools/verdict.py`). Read the single VERDICT line and the table, not the logs.
2. If a rung failed, fix it before running a higher rung. Do not start a full fit while a cheap rung fails.
3. Report: the verdict line, the highest evidence label reached, and what was NOT run (manual rungs: fit, package check, device).
4. Never say "works" for a result below the label `pocket` without naming the label.
5. After a card write, run `tools/check_package.py` and add an `AUDIT_TRAIL.md` entry.
