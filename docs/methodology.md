# Methodology

How to test so that results can be trusted. The methods themselves are in [methods/](../methods/README.md); this page is the thinking that ties them together.

## 1. The ladder: cheapest first
Every check costs time. Order them by turnaround and settle as much as possible near the top; the device, and the person holding it, are the scarce resource.

| Rung | Turnaround | Evidence label | Method |
|---|---|---|---|
| File checks | seconds | `host` | [file-checks](../methods/file-checks/README.md) |
| Host tests, fuzzing, formal | seconds to minutes | `host` | [host-tests](../methods/host-tests/README.md), [fuzzing](../methods/fuzzing/README.md), [formal](../methods/formal/README.md) |
| Simulation | minutes to an hour | `simulation` | [simulation](../methods/simulation/README.md) |
| Map gate, block fits | minutes | `quartus` | [timing-fit](../methods/timing-fit/README.md) |
| Full fit | about 1h40 in the project this came from | `quartus` | [timing-fit](../methods/timing-fit/README.md) |
| Device | a human trip | `pocket` | [report codes](../methods/report-codes/README.md), [debug links](../methods/debug-links/README.md), [Pocket tools](../methods/pocket-native/README.md) |

Never start a long fit while a cheap rung fails. The [project starter](../starter/README.md) encodes the ladder as data (`ladder.json`) with one runner (`verdict.py`).

## 2. Evidence labels
Every result says how far it was proven, and never claims more.

| Label | Means |
|---|---|
| `code-review` | read only; nothing run |
| `host` | ran on a PC |
| `formal-bounded` | a formal check to a depth (BMC): no counterexample within the bound |
| `formal-unbounded` | a formal proof for all inputs (k-induction or PDR), under the stated assumptions |
| `simulation` | ran in RTL or CPU simulation |
| `netlist` | simulated the synthesised netlist |
| `quartus` | a map or fit report |
| `pocket` | ran on a real device |

Other labels used in these docs: **docs** (Analogue or Intel text), **web** (seen in a forum or search, primary page not read), **KB-nnn** (an entry in the [analogue-pocket-dev](https://github.com/alfatreze/analogue-pocket-dev-skill) knowledge base, with its status), **inference** (reasoning, untested), **unverified**. Simulation passing is not hardware.

## 3. An independent oracle
The expected behaviour comes from the spec, real captures or a second reader, not from the code under test. A model (or an AI) that writes both the design and its test shares one misconception and passes wrongly. Mutation (break it on purpose) shows whether a test can fail at all.

## 4. One verdict
Each check prints a machine-readable verdict; people and agents read that, not logs. The verdict states what was run and what was **not**.

## 5. One device trip, many questions
A human trip is expensive. Build a self-testing diagnostic that runs a battery of checks and shows every verdict on one report page, captured as one screenshot ([report codes](../methods/report-codes/README.md)). Ask for the written test list before the install, not after.

## 6. Gate diagnostics
Debug links and report pages sit behind a build flag; the shipped build carries none unless chosen, and says so.

## 7. Long jobs
Before launching a fit, state how long it takes and the finish time; run it in the background; do not poll.

## 8. Keep what you learn
Record decisions (and rejected options), results and handoffs in files the next session reads ([starter](../starter/README.md)). A result that is not written down is lost with the session.

## 9. Record what each method found
Write one outcome record per result (method, technique, cost, outcome, findings with severity and how late they would otherwise have surfaced) and pool the files of many projects: [effectiveness](../methods/effectiveness/README.md). Separate real bugs from alarms that were the test setup's fault; both are results, and the second kind is the cost of a method.
