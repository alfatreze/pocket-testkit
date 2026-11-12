# Effectiveness: record outcomes, build a library of what paid off

**Phase:** process · **Cost:** a few minutes per result · **Status in this kit:** tool and tests (host), seed data from one project

## What it does
Every test method gets a one-line **outcome record** (what was run, how long it took, what it found, how serious, how late it would otherwise have been found). Projects keep their records in one file; the kit **ingests** the files of many projects and prints which methods found real bugs per hour spent, which mostly raised false alarms (an artefact of the test setup), and which results the device later confirmed or contradicted.

Why: a team learns which of the many methods in [methods/](../README.md) to start with only if results are comparable. The honest question is not "did the test pass" but "did this method find a real bug, at what cost, and would anything else have found it".

## A record (JSON Lines, one object per line)
```json
{"schema": 1, "id": "o-001", "date": "2026-11-11", "project": "p-example", "method": "fuzzing", "technique": "structure-aware header mutation with checksum repair under ASan and UBSan",
 "tool": "custom C harness", "target": {"kind": "parser"}, "label": "host", "cost": {"setup_min": 240, "run_min": 5, "human_min": 30}, "outcome": "bug-found",
 "findings": [{"kind": "design-bug", "severity": "medium", "would_otherwise_surface": "field", "summary": "32-bit bound check wraps near 2^32"}],
 "mutation": {"killed": 11, "total": 11}, "confirmed_by": null, "ref": "project-local pointer", "notes": ""}
```
| Field | Values |
|---|---|
| `method` | file-checks, host-tests, fuzzing, formal, simulation, timing-fit, report-codes, debug-links, pocket-native, ci, device-run, other (the folders of [methods/](../README.md); `device-run` is a person running the core and reporting) |
| `target.kind` | parser, rtl-block, fsm, arbiter, fifo, cdc, datapath, cpu-firmware, whole-core, build-flow, installer, ui, timing, other |
| `label` | the evidence the result gives: code-review, host, formal-bounded, formal-unbounded, simulation, netlist, quartus, pocket ([methodology](../../docs/methodology.md)) |
| `outcome` | bug-found, clean, artefact-only, inconclusive, failed (run failed, not yet classified), not-run |
| `findings[].kind` | **design-bug** and **spec-gap** (real), **test-gap** (the tests could not have noticed; found by mutation or review), **tool-artefact** and **model-fault** (the alarm was the simulator's, the testbench's or the host model's fault) |
| `findings[].severity` | low, medium, high |
| `findings[].would_otherwise_surface` | where the bug would have shown up without this method: never, simulation, fit, pocket, field |
| `cost` | integer minutes, estimates, any may be null: `setup_min` (building the method once), `run_min` (one run), `human_min` (attention) |

Rules the validator enforces: `bug-found` needs a design-bug or spec-gap finding; `clean` cannot carry one; `artefact-only` needs the artefact findings; `mutation.killed <= total`. The outcome says what the method **did**, not whether the project is healthy: a clean formal proof is a legitimate, useful result.

## Use
```bash
python3 methods/effectiveness/tools/outcomes.py add docs/outcomes/outcomes.jsonl --project p-xxxx --method fuzzing --technique "..." --target parser --label host \
    --outcome bug-found --finding design-bug:medium:field:"what it was" --cost setup=240,run=5,human=30 --mutation 11/11 --ref B-1063
python3 methods/effectiveness/tools/outcomes.py confirm docs/outcomes/outcomes.jsonl o-014 --label pocket --note "the device agreed"
python3 methods/effectiveness/tools/outcomes.py validate docs/outcomes/outcomes.jsonl
python3 methods/effectiveness/tools/outcomes.py ingest library/outcomes.jsonl project-a/outcomes.jsonl project-b/docs/outcomes/   # pool, validate, de-duplicate by project+id
python3 methods/effectiveness/tools/outcomes.py report library/outcomes.jsonl --md                                             # the table
```
The starter's `tools/verdict.py --record docs/outcomes/outcomes.jsonl` writes a record for every automatic rung it runs (outcome `clean`, or `failed` until a person classifies it); add the findings by hand.

## Reading the table
Per method and per target kind: runs, projects, runs that found a bug, design bugs, how many of those would otherwise have surfaced late (device, field or never), test gaps, artefacts, minutes spent (setup plus run), bugs per 100 minutes, mutants killed, results confirmed later. Counts are small and costs are estimates: use it to choose where to start and what to stop doing, not as a measurement. One project's seed data is in [`examples/`](examples/) (made-up) and the field notes of a real stack are in the [analogue-pocket-dev skill](https://github.com/alfatreze/analogue-pocket-dev-skill) (`references/verification-field-notes.md`).

## Privacy
`project` is an anonymous key you choose (a short random string); never a project, product or person name. The free text (`technique`, `summary`, `notes`, `ref`) is yours: read it before sharing a file. The library only holds what projects send.

## Pros and cons
| Pros | Cons |
|---|---|
| Makes method choice evidence-based, across projects | Small numbers; classification (is it a real bug?) is a judgement |
| Cheap: one line per result, mostly automatic for the cost | Only as honest as the people recording; costs are estimates |
| Separates real bugs from artefacts, so cost of a setup is visible | A method that finds nothing may be doing its job: read `clean` with the label and the mutants killed |

## References
[JSON Lines](https://jsonlines.org/), [methodology](../../docs/methodology.md).
