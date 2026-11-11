# Reusable debug-link RTL

Drop-in blocks to read and write a core's registers from a PC. Simulated with iverilog (`tests/test_debug_link.py`); **not fitted or run on hardware** by this kit.

| File | Role |
|---|---|
| `pk_vjtag_debug.sv` | One instance to add: Virtual JTAG window, demo registers, byte stream, and a pass-through to your registers |
| `jtag/pk_vjtag_altera.sv` | The `sld_virtual_jtag` primitive and the window (Quartus only; not simulated) |
| `jtag/pk_vjtag_regwin.sv` | The window itself, pure RTL: REQ/RSP/ID frames, JTAG-clock crossing, timeout, overrun flag |
| `jtag/pk_debug_decode.sv` | Address decode shared by every link |
| `jtag/pk_avmm_master_to_bus.sv` | Adapts a JTAG-to-Avalon master's exported master port to the same register bus |
| `stream/pk_reg_stream.sv` | Byte FIFOs (core to host, host to core) as registers: a console without the Nios tools |
| `common/pk_demo_regs.sv` | ID, scratch, counter: proves the link before your registers are wired |
| `common/pk_toggle_sync.sv` | Single-bit toggle synchroniser (never use it per bit on a bus, KB-009) |

Host: `../host/pk_vjtag.tcl` (`quartus_stp -t`), `../host/pk_link.py`, `../host/sysconsole_master.tcl` (master path). Pick the link: [CHOOSING](../CHOOSING.md).

## Add it to a core

1. Copy `rtl/` into the project; add the files to the `.qsf`. Instantiate `pk_vjtag_debug` behind a macro (for example `PK_DEBUG_LINK`); `clk` should be well above the JTAG clock (2x as Intel advises for the master bridge; a 74 MHz clock is fine). The window's crossings do not depend on the ratio, only the bus timeout does.
2. Connect your registers to the `u_*` port (word addresses 0x4000 and up) or leave it unconnected (`u_ack` tied 0 gives a timeout, not a hang).
3. Constrain the JTAG clock and `clk` as asynchronous clock groups in the SDC.
4. Fit. Read the per-entity utilisation for the cost and write it down. Check KB-010: no synchroniser chain should become block RAM.
5. Reload over JTAG, then `quartus_stp -t host/pk_vjtag.tcl id` must print `0x504B0101`; then read `0x0` (`0xD0C0FFEE`), write and read `0x1`.

## Assumptions to confirm first on hardware

- Register-bit order on the DR (LSB first) and the capture/shift timing of the TDO output; the Intel example registers it on the rising TCK edge, as here.
- The primitive's port and parameter names for your Quartus version.
- Register-bus timing: the bus is request/ack, ack may come the same cycle or later; `TIMEOUT` clock cycles without ack returns `0xDEADBEEF` with the error flag.
