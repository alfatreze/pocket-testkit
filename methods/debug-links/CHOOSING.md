# Choosing a debug link

Rules for a person or an AI agent. Collect the facts from the project (read the code and the last fit report; do not guess), then run `python3 tools/choose_link.py` (from this folder) or follow the steps by hand.

## Steps

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


## Numbers and rules from the web (not measured here)

- JTAG master: the Avalon clock should be at least 2x the TCK frequency; a Blaster II defaults to 24 MHz TCK and 6 or 16 MHz can help; a System Console timeout locks the JTAG chain ([Intel article 000084688](https://www.intel.com/content/www/us/en/support/programmable/articles/000084688.html), via a search summary; the page itself did not load for me).
- Single-word `master_read_32` / `master_write_32` move one item per round trip, roughly 3 ms each in one report; `master_read_memory` / `master_write_memory` are faster for blocks ([community thread](https://community.altera.com/discussions/quartus-prime/how-can-i-improve-jtag-to-avalon-master-bridge-write-speeds-through-system-conso/322114)).
- Virtual JTAG: the TCK clocks the whole SLD infrastructure (10 MHz maximum with an Intel cable, per the guide), so cross to your clock properly ([user guide](https://www.intel.com/content/www/us/en/docs/programmable/683705/20-3/design-flow-of-the-virtual-jtag-core.html)). From Tcl: lock the device, shift the virtual IR, then the DR, with `device_virtual_ir_shift` and `device_virtual_dr_shift` ([scripting reference](https://intel.com/content/www/us/en/docs/programmable/683432/21-4/tcl_pkg_jtag_ver_1.0_cmd_device_virtual_dr_shift.html)).
- JTAG UART: host tool is `nios2-terminal`; only one JTAG connection at a time ([forum](https://community.altera.com/discussions/nios-system/jtag-uart-console/109188)).
- Not found anywhere: the logic cost of the SLD hub, the virtual JTAG node or the master bridge on Cyclone V. Measure it (OQ-18): the fitter report's per-entity utilisation shows it.



## The chooser

```bash
python3 tools/choose_link.py --where desk --need registers --has-regbus --headroom ok
python3 tools/choose_link.py --where field --need stream --case-closed
```
It ranks the options and prints reasons and caveats. The scores are hand-set and untuned: treat the output as a prompt for reasoning, not a verdict. Costs of the blocks on Cyclone V are **not measured**: read them from your fit report and record them.
