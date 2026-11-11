# Serial routes, and corrections to common claims

A pasted AI-generated answer (not a primary source) circulated claims about the link port. Checked against Analogue's docs and template:

| Claim | Check |
|---|---|
| The JTAG header is inside the unit, bottom edge; retail units need the rear cover off, Developer Edition has a door | Confirmed (docs, getting-started) |
| Only Intel or Terasic blasters; clones may damage the Pocket | Docs say clones "may have unexpected behavior and/or cause hardware damage". The voltage-reference explanation and the part number P0302 are the answer's own additions |
| The link port has four data lines (SI, SO, SCK, SD) | Confirmed in the template; direction comments in the template are GBA-style, KB-013 (community-reported) says all four work both ways |
| Core.json sets the link voltage (3.3 V or 5 V) | **Not what the docs say.** Voltage is a mechanical switch (5 V when depressed, 3.3 V when not); core.json only enables power (KB-248). Use a 3.3 V adapter and insert nothing that depresses the switch |
| `link_port: true` alone enables translators and power | Docs say only "whether link port is utilized"; KB-013 says `cartridge_adapter: 0` is needed too and that powers the cart port. Unverified |
| Wire SO to adapter RX, SI to adapter TX on a cut link cable | Only valid with the cable crossing checked by continuity; a Game Boy link cable crosses SO and SI. Unverified |
| A Terasic blaster cannot give an interactive console | **Overstated.** A JTAG UART with `nios2-terminal` is interactive in both directions, and the Virtual JTAG window's byte stream here is too (host polls) |
| Link-port serial works with the case closed | True and the main advantage on a retail unit: JTAG needs the cover off |

**Extra routes the pasted answer missed**

- The core template exposes `dbg_tx` / `dbg_rx` (a USB UART on a breakout board) and `user1` / `user2` (solder pads near the JTAG connector), all tied off by default (KB-249). Not documented elsewhere; check the pads and levels before connecting anything (OQ-23).
- A soft RISC-V core's JTAG debug module can in principle be bit-banged over the four link pins to a cheap FTDI MPSSE adapter with OpenOCD, giving GDB (halt, step, memory, firmware load without the SD card) with the case closed. Untested here; the link pins reportedly degrade above about 6 MHz, which is enough for OpenOCD; check the debug module's licence first (OQ-24). This is a different thing from the Blaster and must not be connected to the Pocket's JTAG header.

**For a retail unit used on the move** the practical order is: report codes (nothing to carry), then a link-port or pad UART (case closed), then the Blaster at a desk with the cover off.

