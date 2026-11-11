# Choosing a debug link for a Pocket core

Evidence labels: **docs** (Analogue or Intel text), **web** (forum or support article seen in a search, primary page not read), **KB-nnn** (analogue-pocket-dev knowledge base), **inference**, **unverified** (not tested by this kit). Nothing in the RTL here has been fitted or run on a Pocket: it passes iverilog simulations only (`sim/`, `tests/test_debug_link.py`), and one mutation of each key path was caught.

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

## Numbers and rules from the web (not measured here)

- JTAG master: the Avalon clock should be at least 2x the TCK frequency; a Blaster II defaults to 24 MHz TCK and 6 or 16 MHz can help; a System Console timeout locks the JTAG chain ([Intel article 000084688](https://www.intel.com/content/www/us/en/support/programmable/articles/000084688.html), via a search summary; the page itself did not load for me).
- Single-word `master_read_32` / `master_write_32` move one item per round trip, roughly 3 ms each in one report; `master_read_memory` / `master_write_memory` are faster for blocks ([community thread](https://community.altera.com/discussions/quartus-prime/how-can-i-improve-jtag-to-avalon-master-bridge-write-speeds-through-system-conso/322114)).
- Virtual JTAG: the TCK clocks the whole SLD infrastructure (10 MHz maximum with an Intel cable, per the guide), so cross to your clock properly ([user guide](https://www.intel.com/content/www/us/en/docs/programmable/683705/20-3/design-flow-of-the-virtual-jtag-core.html)). From Tcl: lock the device, shift the virtual IR, then the DR, with `device_virtual_ir_shift` and `device_virtual_dr_shift` ([scripting reference](https://intel.com/content/www/us/en/docs/programmable/683432/21-4/tcl_pkg_jtag_ver_1.0_cmd_device_virtual_dr_shift.html)).
- JTAG UART: host tool is `nios2-terminal`; only one JTAG connection at a time ([forum](https://community.altera.com/discussions/nios-system/jtag-uart-console/109188)).
- Not found anywhere: the logic cost of the SLD hub, the virtual JTAG node or the master bridge on Cyclone V. Measure it (OQ-18): the fitter report's per-entity utilisation shows it.

## How an AI should choose

Collect these facts from the project (read the code and the last fit report, do not guess), then run `python3 tools/choose_link.py` or follow the rules by hand.

1. **Where is the device when the data is needed?** In the field, with a third party, or wanted as an archive next to the build: report code (plus the 0152 log). Stop here.
2. **Is a genuine Blaster available at the desk?** If not: report code, 0152 log, or a link-port or devkit UART.
3. **What is needed?**
   - Registers or memory values: Virtual JTAG window if the core has (or can get) a register bus; JTAG master if there is already an Avalon system or blocks of memory must be read.
   - A console or log stream: the window's byte stream (`pk_reg_stream`); JTAG UART only if Nios tools are present and an Avalon system exists.
   - Signals over time: SignalTap if there is block RAM headroom; otherwise ISSP, and latch fast events in the core.
4. **Headroom.** Read the fit report. Low block RAM or logic: avoid SignalTap and the Avalon route; use the window or ISSP. A link adds resources, so say what it cost after the fit.
5. **Fast events** (shorter than a poll): never poll. Latch in the core, then read.
6. **Ship it gated.** Put the link behind a macro so the shipped build carries none of it, and say so in the report.
7. **Say what was and was not run.** Simulation passing is not hardware; check the link with `id` (expects `0x504B0101`) and the demo registers before trusting anything else.

## Reusable RTL

[rtl/README.md](../rtl/README.md): the pieces, how to add them, and what is simulated.
