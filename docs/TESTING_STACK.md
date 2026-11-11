# Testing stack: what to check before the Pocket

Reviewed against the Analogue docs and a knowledge base: [TESTING_AUDIT.md](TESTING_AUDIT.md).

The report codes (grid and QR) are for getting data **out of a device**. They answer "what happened on the Pocket?". They are not the first line of testing. Most bugs should be caught at the desk, before a human ever sees the device. This page lists the layers worth having, in the order they pay off, for projects where an AI agent writes and reviews most of the code.

Each row is a suggestion with a cost and a catch. None of it is built into this kit, and evidence for each row has to come from your own project.

## The layers

| # | Layer | Catches | Cost | Notes |
|---|---|---|---|---|
| 1 | **Bit-exact reference models** (Python or C) compared with the RTL in simulation | Wrong arithmetic, wrong format handling | Medium | Usually the layer people already have. |
| 2 | **Mutation sweeps**: break the design on purpose, confirm a test fails | Tests that never exercise a feature | Low to medium | Found untested hold, FIFO-clear and start/clear cases in one project. |
| 3 | **Coverage** (Verilator line, toggle, FSM state) | The same gaps, without guessing mutants | Low | Run it first, then spend mutants where coverage is thin. |
| 4 | **Per-block timing fit**: a stand-alone Quartus project per block at the target clock | Fmax misses found in minutes instead of after a full fit | Low | Treat the result as an upper bound: placement of the integrated design is worse and varies by seed (see [TESTING_AUDIT.md](TESTING_AUDIT.md)). A bit-exact decoder can still fail timing at the target clock. In one project 3,217 endpoints failed at 100 MHz and it showed up 1h35m into the fit. |
| 5 | **Synthesis-only gate**: `quartus_map` plus a quick STA on every RTL change | The same, for the whole design, before the long fit | Low | Minutes against hours, but slack before placement is only an estimate: compare it with a past fit before trusting it. Parsing the map report (RAM modes, resource counts, ignored constraints) is the safer use. |
| 6 | **Whole-core simulation**: stand-ins for PLL, FIFO and RAM IP, a host model of the bridge and data slots, your memory chip model, and a frame dumper compared with golden images | Wiring mistakes (an unconnected signal put X into the CPU in one project) | High, once | Turns "boot, read a file, show the picture" into a test. A Pocket session then confirms instead of discovers. |
| 7 | **Post-synthesis netlist simulation** with the same vectors | RAM read-during-write behaviour, initial values, inference differences | Medium | Run it where RAM inference has bitten you before. |
| 8 | **Formal checks** (SymbiYosys) on small control logic: FIFOs, port muxes, tile state machines | "Never overflows", "done goes to exactly one client", "no deadlock" | Medium | Random tests say nothing failed; formal says nothing can fail up to a bound. For clock crossings, sweep many clock ratios and phases in simulation. |
| 9 | **Fuzzing** C parsers and container readers (libFuzzer or AFL, with ASan and UBSan, seeded from real files) | Crashes, hangs, claims of "any input decodes in bounded time" | Low | About an afternoon. |
| 10 | **CI** running the host test suite on every push, slow sweeps nightly, golden performance numbers (clocks per tile) | Broken tests nobody noticed, speed regressions | Low | A suite nobody runs fails silently. Watch for path quirks such as spaces in make variables. |

If you can only do two things from this table, do the timing gates (4 and 5) and the whole-core simulation (6). They turn the two expensive surprises, a long fit that misses timing and an integration never tried until hardware, into desk findings.

## What only the device can answer

Some questions need the real hardware: timing margins in the fitted design, SDRAM and display electricals, behaviour of the host and the SD card, anything involving a person looking at the result. Keep these on the device, and record each result with an evidence label (code-review, host, simulation, Quartus, Pocket), so nobody mistakes a simulation for a hardware result.

## Where the report codes fit

Use the grids and the QR when:

- a **third party** (a tester or user) has to send you data and has no cable;
- you want to measure **the build users actually run**, not an instrumented one;
- you want a record **archived next to the build** (the Pocket adds core name and version, see [SCREENSHOT_METADATA.md](SCREENSHOT_METADATA.md));
- a screenshot already shows the context you need (page, state, moment).

Prefer a cable when you are at your desk and need live or high-rate data.

## Built-in Pocket channels

The Pocket already offers a time-stamped debug event log (target command 0152), Debug Logging to `/System/Logs/`, Pause Core Boot and Pause Load Data, and a Statistics overlay. Details and caveats: [TESTING_AUDIT.md](TESTING_AUDIT.md).

## JTAG options at the desk

| Option | What you get | Catch |
|---|---|---|
| ISSP or a few probes | Live reads of selected registers | A separate instrumented build. Polling cannot catch fast events; latch the value in the core and read it afterwards. |
| SignalTap | Waveforms | Takes block RAM and logic; a probe change means a re-fit. |
| JTAG-to-Avalon master (System Console `master`) | Scripted reads and writes of a memory-mapped bus, so an agent can read any register | Resource cost not measured here (expected small). Not yet tried in the project that motivated this page. |
| Virtual JTAG or JTAG-UART | A byte stream in and out | Needs a small core-side block. |
| Link-cable port as a serial line | A UART to a cheap USB-serial adapter, no Quartus needed | Needs `link_port: true` and `cartridge_adapter: 0` (which powers the cart port, so keep a game cart out) and a UART in the core; reported to degrade above about 6 MHz. Check pin and voltage details before wiring. Never put a clone USB Blaster on the JTAG header (reported to have killed a Pocket). |

A scripted JTAG link is also what lets an AI agent drive and read the real device directly. The report codes are the slower, free alternative that anyone can use.

## Working with an AI agent

- Have the agent write fixtures and tests before any fit, and make it report which evidence label each claim has.
- Gate long jobs: ask for the expected duration and finish time before launching a fit.
- Add the rules in [agent/AGENTS.snippet.md](../agent/AGENTS.snippet.md) so the agent decodes screenshots correctly and never raises QR density unasked.
- Turn recurring mistakes into checks the suite runs, not reminders in a prompt.
