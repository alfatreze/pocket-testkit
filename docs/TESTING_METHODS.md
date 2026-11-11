# Testing methods: what to use, when

One idea runs through all of it: **catch bugs as early and as cheaply as possible, and say exactly what was proven.** Steps are ordered by cost. Details and Pocket-specific caveats: [TESTING_STACK](TESTING_STACK.md), [TESTING_AUDIT](TESTING_AUDIT.md). Evidence labels: `code-review`, `host`, `simulation`, `quartus`, `pocket`.

## Methods

| Method | Finds | Cost | Tools and docs | In this repo |
|---|---|---|---|---|
| **Checks on files** (JSON limits, stale bitstream, report parsing) | Silent misconfiguration | seconds | Analogue [developer docs](https://www.analogue.co/developer/docs) (JSON files) | [`check_pocket_json.py`, `check_package.py`](../templates/claude-project/README.md) |
| **Reference models and golden vectors** | Wrong arithmetic or format | low | any language; compare bit for bit | `tests/golden_400x360.json`, C vs Python vs Rust equality |
| **Mutation sweeps** (break it on purpose) | Tests that cannot fail | low | [MCY](https://github.com/YosysHQ/mcy) for RTL; by hand for software | the tests were checked with injected bugs |
| **RTL simulation** | Logic and wiring bugs | minutes | [Icarus Verilog](https://steveicarus.github.io/iverilog/), [Verilator](https://verilator.org/guide/latest/), [cocotb](https://docs.cocotb.org/) | `sim/`, `rtl/` testbenches |
| **Coverage** | Features no test touches | low | [Verilator coverage](https://verilator.org/guide/latest/exe_verilator_coverage.html) | not yet |
| **Formal checks** on small control logic | "Never overflows", "no deadlock" | medium | [SymbiYosys](https://symbiyosys.readthedocs.io/) | not yet |
| **Fuzzing** parsers | Crashes, hangs on any input | low | [libFuzzer](https://llvm.org/docs/LibFuzzer.html), [AFL++](https://aflplus.plus/), [OSS-Fuzz](https://github.com/google/oss-fuzz) | not yet |
| **Whole-core simulation** with a scripted host | Wiring, boot order, persistence | high once | vendor sim models, your host model | [guide](TESTING_AUDIT.md#4-whole-core-simulation-what-to-model-and-what-not-to-fake) |
| **Per-block fit, map gate, full fit** | Timing, resources, RAM inference | minutes to hours | Quartus reports; seeds vary the result | [stack](TESTING_STACK.md) |
| **Chip32 loader simulation** | Loader bugs before hardware | low | [openfpga-chip32-sim](https://github.com/agg23/openfpga-chip32-sim) | n/a |
| **Report codes** (grid, QR) | What the device did, from anyone | no cable | this kit | `python/`, `c/`, `rust/`, [sample pages](SAMPLE_CORE.md) |
| **Live debug links** (JTAG, serial) | Live registers, waveforms | cable and a build | [Virtual JTAG guide](https://www.intel.com/content/www/us/en/docs/programmable/683705/20-3/design-flow-of-the-virtual-jtag-core.html) | [link guide](DEBUG_LINK_CHOICE.md), [`rtl/`](../rtl/README.md), `tools/choose_link.py` |
| **Pocket's own tools** (debug log, event log, statistics, pause options) | Boot and load problems | none | Analogue [debugging aids](https://www.analogue.co/developer/docs/debugging-aids) | [audit](TESTING_AUDIT.md) |
| **CI** | Broken tests nobody ran | low | [GitHub Actions](https://docs.github.com/actions) | `.github/workflows/rust.yml` |

## Methodology

1. **Ladder.** Run cheap rungs first; never start a long fit while a cheap rung fails. Template: `templates/claude-project/ladder.json` and `tools/verdict.py`.
2. **Evidence labels.** Every result says how far it was proven. Simulation passing is not hardware.
3. **Independent oracle.** The expected behaviour comes from the spec, real captures or a second reader, not from the code being tested (an AI that writes both shares one misconception).
4. **One verdict.** Each check prints a machine-readable line; the agent reads that, not logs.
5. **One device trip, many questions.** A self-testing build that shows every result on one report page (this kit's grid) answers a whole battery per trip.
6. **Gate diagnostics.** Debug links and report pages are behind a build flag; the shipped build carries none unless chosen.
7. **Keep what you learn.** Decisions, rejected options and results go in files the next session reads ([project starter](../templates/claude-project/README.md)).

## Choosing a debug link

At a desk with a genuine Blaster, for registers or memory: a Virtual JTAG window or JTAG master. For signals: SignalTap (block RAM permitting) or ISSP. In the field, with a third party, or case closed: report codes, the event log, or a serial UART. Rules and a script: [DEBUG_LINK_CHOICE](DEBUG_LINK_CHOICE.md).
