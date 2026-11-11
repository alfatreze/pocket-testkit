# Debug links: live registers, memory and signals

**Phase:** observe on the device · **Cost:** a cable, a build with the link, often a re-fit · **Status in this kit:** RTL simulated with iverilog and host-tested scripts; **never fitted or run on a Pocket**

## What it does
Connects a PC to a running core through JTAG or a serial line, to read and write registers and memory, see signals, or stream a console. It is the opposite trade to [report codes](../report-codes/README.md): live and fast, but needs a cable and a person at a desk.

## Use it when
You are at a desk with a genuine USB Blaster (or a serial adapter) and need live registers or memory, signals over time, or a scripted loop where an AI agent reads and writes the real device. Not for third parties or the field: use report codes or the [Pocket's own tools](../pocket-native/README.md).

## The options

| Link | What you get | Pros | Cons |
|---|---|---|---|
| **Report code** (grid or QR) | Data out of the device as a picture | No cable, third parties can send it, measures the shipped build, archived with core name and version | Slow, one-way, a person has to take the picture |
| **Debug event log** (target 0152) | 32-bit time-stamped values in `/System/Logs/` | No hardware, shipping build (docs, KB-241) | Needs a core-side sender; rate unknown (OQ-15) |
| **ISSP** (In-System Sources and Probes) | A few signals read, a few driven | Small, simple, already used in Tau (KB-057) | Polled, misses fast events: latch in the core and read afterwards |
| **SignalTap** | Waveforms with triggers | Best tool for signal-level bugs; Pause Core Boot / Pause Load Data help arming (docs, KB-242) | Block RAM and logic; probe change = re-fit; one report says fast I/O register packing may be lost with it (KB-053, low confidence) |
| **Virtual JTAG register window** (`rtl/jtag/pk_vjtag_regwin.sv`) | Read and write 32-bit words on a register bus, plus a byte stream | Pure RTL, one instance, no Platform Designer, tiny (expected, unmeasured), `quartus_stp` Tcl only, same window can carry a console | You own the protocol; per-access speed limited by `quartus_stp` round trips; JTAG clock crossing is yours to get right (here it is done and simulated) |
| **JTAG-to-Avalon master bridge** | Scripted reads and writes of any Avalon-MM address, block reads | Standard Intel IP, System Console `master_read_memory` for blocks, an agent can read any register | Needs Platform Designer and an Avalon route to your registers (`pk_avmm_master_to_bus` adapts it); Avalon clock must be at least 2x TCK or accesses time out; a timeout can lock the JTAG chain, which also blocks SignalTap; about 3 ms per single access reported (web) |
| **JTAG UART** | A byte stream (console) | Ready IP, good for a soft CPU's `printf` | Needs `nios2-terminal`, which comes with the Nios tools (may not be in a Lite install: unverified); the program can block when no terminal is attached; one JTAG client at a time (web) |
| **Link-port UART** | Serial to a cheap adapter, no Quartus | No JTAG session, works when a Blaster is awkward | `link_port: true` and `cartridge_adapter: 0` (powers the cart port: keep a game cart out); needs a UART in the core; reported to degrade above about 6 MHz (KB-013) |
| **Devkit debug key** | USB-UART up to 2 Mbps | Official accessory | Needs the key, cart power too (KB-018) |

Always use a genuine Blaster on the Pocket's JTAG header; a clone was reported to have damaged one (KB-018). A JTAG reload makes the Pocket redo the whole load, so an agent can reflash and retest, but your script must reconnect after each reload (docs, KB-243).


Always use a genuine Blaster on the Pocket's JTAG header; a clone was reported to have damaged one. A JTAG reload makes the Pocket redo the whole load, so an agent can reflash and retest, but scripts must reconnect after each reload.

## Pros and cons at a glance
| Link | Best for | Main cost |
|---|---|---|
| Virtual JTAG window | Cheapest scripted register access, plus a console | You own the protocol |
| JTAG-to-Avalon master | Any Avalon address, block reads | Platform Designer, clock rule, timeout hazards |
| SignalTap | Waveforms | Block RAM, re-fit per probe change |
| ISSP | A few signals | Polling misses fast events |
| JTAG UART | A soft CPU's `printf` | Nios tools, one JTAG client at a time |
| Serial (link port, pads, devkit key) | Case closed, no Quartus | Needs a UART in the core; see [SERIAL](SERIAL.md) |

## Documentation and code
| What | Where |
|---|---|
| How to choose (rules, numbers from the web, the chooser script) | [CHOOSING](CHOOSING.md) |
| Serial routes and corrections to common claims | [SERIAL](SERIAL.md) |
| The reusable RTL: add a register window to a core | [rtl/README](rtl/README.md) |
| Host scripts | `host/` (`pk_vjtag.tcl`, `pk_link.py`, `sysconsole_master.tcl`) |
| Testbenches | `sim/`, run by `tests/test_debug_link.py` (needs iverilog) |
| Chooser | `tools/choose_link.py` |

Evidence labels: **docs** (Analogue or Intel text), **web** (forum or support article seen in a search, primary page not read), **KB-nnn** (the [analogue-pocket-dev](https://github.com/alfatreze/analogue-pocket-dev-skill) knowledge base), **inference**, **unverified**.
