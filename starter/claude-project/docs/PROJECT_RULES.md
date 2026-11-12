# Project rules (shared by Claude Code and other agents)

1. **Evidence labels on every result.** `code-review` (read only), `host` (ran on the PC), `simulation` (RTL or CPU simulation), `quartus` (map or fit report), `pocket` (ran on the device). Never describe a lower label as a higher one. Say what was and was not run.
2. **Test ladder, cheapest first:** JSON and package checks, host tests, simulation, map gate, full fit, device. Run `make verdict` (one line, machine-readable) and read that, not the logs. Do not start a long fit before the cheap rungs pass.
3. **Tests must be able to fail.** Break the design on purpose (mutation) and confirm a test catches it. Write the expected behaviour from the spec or real captures, not from the code under test.
4. **Long jobs:** before launching a fit, say how long it takes and the local finish time; do not poll, wait for the completion notice.
5. **Hardware and card writes need the owner's approval.** Use the project's install script (dry run first), never hand-typed copies. After writing, compare the file's SHA-256 with the build output (`tools/check_package.py`).
6. **Concurrent sessions:** use worktrees; check `git branch --show-current` before every commit; commit only your own files; never `git stash` or `git reset` on a shared tree.
7. **Diagnostic-only code is registered** in one feature list, never a bare `#if DIAGNOSTIC`. If a build misses its memory floor, drop features; never lower the floor.
8. **No copyleft code in a permissive project.** Read for ideas only and record the inspiration in `docs/PROVENANCE.md`.
9. **Keep decisions and knowledge:** write assessed-and-rejected options into `docs/DECISIONS.md`; record every finished change in `docs/AUDIT_TRAIL.md` (id, evidence label, what was not run on the device).
10. **Record outcomes.** Every test method you run gets a record in `docs/outcomes/outcomes.jsonl` (`tools/outcomes.py add ...`, or `tools/verdict.py --record docs/outcomes/outcomes.jsonl` for the automatic rungs): method, technique, cost in minutes, outcome, findings (real bug, test gap, or the test setup's fault) and how late each would otherwise have been found. Add `confirm` when the device later agrees or disagrees. Share files only with an anonymous project key.
