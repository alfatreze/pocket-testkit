# Analogue Pocket notes for testing

Facts and traps that matter when testing a Pocket core. Labels as in [methodology](methodology.md#2-evidence-labels). Sources: Analogue's [developer docs](https://www.analogue.co/developer/docs) and the [analogue-pocket-dev](https://github.com/alfatreze/analogue-pocket-dev-skill) knowledge base (KB ids).

## Boot and host behaviour (docs)
Bitstream loaded, status 1 (booting); the Pocket polls until 2 (setup); cartridge probe; bridge writes from the JSON; data slots loaded in order; target command 0140 (ready to run), status 3; reset exit, status 4. Heartbeat loss, or a JTAG reload, makes the Pocket reload the core with the same starting conditions. A whole-core simulation needs a host that does this ([simulation](../methods/simulation/README.md)).

## What a host model should exercise
Bridge reads that may arrive up to the next strobe (KB-008); a data loader that cannot be told to wait (KB-028, community-reported); the three persistence paths and the shutdown flush (nonvolatile slots, target write/flush on deferload slots, interact persist values; KB-001, KB-007); savestate and sleep round trips (KB-016, KB-017); the grayscale display-mode response word `16'h444D`; the docked-state notification; heartbeat loss and JTAG reload; unrelated clocks (`clk_74a`, `clk_74b`, PLL outputs).

## Debug and trace channels
[Pocket's own tools](../methods/pocket-native/README.md): Debug Logging, the debug event log (target 0152; KB-241), pause options (KB-242), JTAG reload (KB-243).

## Link port and serial
- Voltage is a **mechanical switch** (5 V when depressed, 3.3 V otherwise), not `core.json`; link power shares the cartridge rail (docs; KB-248). Use a 3.3 V adapter and insert nothing that depresses the switch.
- `link_port: true` and `cartridge_adapter: 0` are both needed in practice and the latter powers the cart port, so keep a game cart out (KB-013, community-reported).
- The template exposes `dbg_tx`/`dbg_rx` (a breakout USB UART) and `user1`/`user2` (pads near the JTAG connector), tied off by default (KB-249, one source, untested).
- Never put a clone USB Blaster on the JTAG header (docs; KB-018).
More: [SERIAL](../methods/debug-links/SERIAL.md).

## Timing and fit
Seeds vary results by about 1.2 ns at high occupancy; read hold in the fast corner; fail on ignored SDC constraints; no per-bit synchronisers on buses (KB-011, KB-027, KB-009, all community-reported). See [timing-fit](../methods/timing-fit/README.md).

## Quartus and edition claims
Cyclone V builds in Quartus Prime Lite or Standard, never Pro (KB-049). Claims like "X is Standard only" are unreliable (one was refuted, KB-050): test on your edition.

## Open questions with a cheap test
The skill's `open-questions.md` lists them with tests: debug-event-log rate and availability (OQ-15), pre-placement timing estimates (OQ-16), Verilator on the APF files (OQ-17), the cost of a JTAG master (OQ-18), button injection (OQ-19), the user pads (OQ-23), a RISC-V debug module over the link pins (OQ-24), the Virtual JTAG window on hardware (OQ-21).
