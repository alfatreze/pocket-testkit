# Simulation

**Phase:** simulate · **Cost:** minutes to an hour · **Status in this kit:** testbenches for the debug-link RTL (iverilog); no whole-core simulation

## What it does
Runs your RTL (and optionally your firmware on its soft CPU) in a simulator against a model of the surroundings, so wiring and logic bugs appear at your desk instead of after a long fit.

## Levels
| Level | What runs | Finds | Cost |
|---|---|---|---|
| **Block** | One module with a testbench | Logic bugs | low |
| **Firmware on the CPU** | Your C on the soft CPU model | Firmware and MMIO bugs | low to medium |
| **Whole core** | The core top with a scripted Pocket host, memory chips, video and audio capture | Wiring mistakes (an unconnected signal put X into a CPU), boot order, persistence | high once |
| **Netlist** | The synthesised netlist with the same vectors | RAM inference differences, initial values | high; read the map report first |
| **Chip32 loader** | The loader program on a PC | Loader bugs | low: [openfpga-chip32-sim](https://github.com/agg23/openfpga-chip32-sim) |

## Whole-core simulation: what to model
Model the Pocket side as a **scripted host**, written from the docs:
- boot order: status 1 (booting), 2 (setup), host commands and data-slot writes, target 0140 (ready to run), status 3, reset exit, status 4;
- bridge reads that may arrive up to the next strobe, and a data loader that cannot be told to wait, so test back-to-back reads and a stalling client;
- three unrelated clocks (`clk_74a`, `clk_74b`, your PLL outputs) with random phase per run;
- video (RGB888 with sync and enable), I2S audio at 48 kHz, your SDRAM, PSRAM and cart models;
- the Pocket-only failure classes: the three persistence paths and shutdown flush, savestate and sleep round trips, the grayscale display-mode response, the docked-state notification, heartbeat loss and a JTAG reload ([Pocket notes](../../docs/pocket-notes.md)).

**Use the vendor models for FIFOs and RAM** (`<quartus>/eda/sim_lib/altera_mf.v`, licensed, never committed) and hand-write only the PLL: a wrong hand-written `dcfifo` model gives false passes. Whether a given free simulator compiles every vendor model is unverified; iverilog ran `dcfifo` in the Tau project.

Frame dumps compared with golden images turn "boot, read a file, show the picture" into a test. Keep Analogue's licensed APF files out of public repos.

## Pros and cons
| Pros | Cons |
|---|---|
| Bugs found at the desk, repeatable, scriptable | Only as faithful as your host model; hardware timing is not modelled |
| Mutation and coverage work here | A whole-core setup is real work (the vendor IP models, the host model) |

## In this kit
Testbenches for the debug-link RTL: [`methods/debug-links/sim`](../debug-links/sim/), run by [`test_debug_link.py`](../debug-links/tests/test_debug_link.py) (iverilog). They drive the Virtual JTAG signals directly; they are not a JTAG TAP model.

## References
[Icarus Verilog](https://steveicarus.github.io/iverilog/), [Verilator](https://verilator.org/guide/latest/), [cocotb](https://docs.cocotb.org/), Analogue [developer docs](https://www.analogue.co/developer/docs) (boot process, bridge).
