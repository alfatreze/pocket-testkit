# Audit: testing an Analogue Pocket core with an AI agent

Review of [TESTING_STACK.md](TESTING_STACK.md) against the Analogue developer docs and the evidence-graded knowledge base of the `analogue-pocket-dev` skill (KB ids below). Evidence labels: **docs** (Analogue text), **KB-nnn** (with its status), **project** (seen in Tau Alpha's repo), **inference** (my reasoning, untested), **unverified** (needs a test on your setup).

## 1. Verdict on the proposed items

| # | Item | Verdict | Pocket-specific finding |
|---|---|---|---|
| 1 | Bit-exact reference models | Keep | Tau already has them. The weak point is who writes the oracle (section 3, rule 1). |
| 2 | Mutation sweeps | Keep | Cheap and independent of the author's assumptions. |
| 3 | Verilator coverage | Keep, check tooling | Tau uses iverilog (`sim/test_cymo_i2s_rate.py`), not Verilator. Verilator needs the Altera primitives replaced or wrapped. **Unverified** for the APF files. |
| 4 | Per-block timing fit | **Keep with a caveat** | A block alone gets easy placement. KB-011 (community-reported): at 90-99% occupancy placement dominates, identical RTL spread 1.19 ns across four seeds, and hold can fail in the fast corner while passing slow. An isolated Fmax is an upper bound, never a pass. Use it to reject blocks that fail alone, and keep a margin for the integrated fit. |
| 5 | Synthesis-only STA gate | **Weaker than stated** | Before placement there is no real routing delay, so slack is an estimate. **Unverified**: whether your Quartus edition gives a useful pre-fit timing report; test it on a past fit and compare with the final slack before trusting it. Better value from the same run: parse the map report for what it can see exactly (see section 2). |
| 6 | Whole-core simulation | **Highest value, with a fidelity warning** | See section 4. |
| 7 | Post-synthesis netlist sim | Lower priority | Slow, and the same questions are mostly answered by reading the map report for inferred RAM modes and by the vendor models in item 6. KB-052 and KB-058 (both community-reported) are RAM-inference failures a report parser catches. |
| 8 | Formal (SymbiYosys) | Keep for small control logic | Cannot prove CDC safety (metastability). Use it on FIFOs, muxes and FSMs only. |
| 9 | Fuzzing C parsers | Keep | Cheap. Also run the parser once on the real soft CPU in simulation, since stack and heap limits differ from the host. |
| 10 | CI | Keep, split in two | A hosted runner cannot practically run a Quartus fit; keep fits on a VM and run host tests in CI. |

Corrections made to TESTING_STACK.md as a result: caveats on rows 4 and 5, the "few hundred logic cells" figure marked unmeasured, a warning about clone USB Blasters, and the Pocket's built-in debug channels added.

## 2. What the list is missing (Pocket-specific, cheap)

| Check | Why | Evidence |
|---|---|---|
| **JSON validator** for `core.json`, `data.json`, `interact.json`, `video.json`, `input.json`, `instance.json` | The Pocket gives almost no feedback on malformed JSON; a typo means a core that silently misbehaves or is missing from the menu | docs (Debugging Aids: "Builds" list), skill practice 4 |
| **Package check**: SHA-256 of the `.rbf_r` on the card against the build output | A stale bitstream silently loads the old core | skill practice 5; project (`tools/install_dev_core.py`) |
| **Map and fit report gates** | Resource counts against a budget; inferred RAM mode; ignored SDC constraints (fail the build on them); worst setup and hold slack in both corners | KB-027 (community-reported), KB-011, KB-052, KB-058 |
| **CDC lint** (a grep is a start) | Multi-bit buses through per-bit `synch_3` chains; synchroniser chains turned into block RAM | KB-009 (community-reported, high confidence), KB-010 |
| **Tie-off check** for cartridge and link pins | A mis-set translator with a powered cart can destroy cart data; PSRAM chip enables must never both assert | skill practice 7 |
| **Seed sweep policy** | One failing fit is not proof of a regression. Three or four seeds are data; ten is a lottery | KB-011; KB-051 notes a fit is deterministic for identical source and seed, but bitstreams differ because the framework stamps `build_id.mif` on every compile |
| **Video timing check** in simulation | The Pocket reports sync rate and status in its Statistics overlay; compute the frame rate from the pixel clock and line counts in the testbench and check it against the allowed range in `video.json` | docs (Debugging Aids, `video.json`) |

## 3. How to use the AI efficiently

1. **Separate the author of the oracle from the author of the design.** The same model writing RTL and its test tends to share one misconception. Derive the expected behaviour from an independent source: Analogue's text, real files and real captures, a second model reading only the spec, or a mutation run. Tau's optional second opinion (Codex) is this idea. Evidence: project practice; the reasoning is **inference**.
2. **Build a ladder by turnaround time and push every decision down it.** Lint (seconds), host tests (minutes), whole-core simulation (minutes to an hour), synthesis (about 13 minutes in Tau), full fit (about 1h40 in Tau, project figures), then a human on the device. The agent is fastest at the top rungs, so catch what you can there.
3. **Make every check print one machine-readable verdict** (pass or fail, key numbers, an evidence label) and have the agent read the summary, not the log. This saves context and avoids guessing from noisy output.
4. **Ground the agent in the knowledge base, not memory.** Load the `analogue-pocket-dev` skill; cite KB ids; treat community-reported entries as leads to test. The template and the docs disagree in places (the shipped template never issues commands 0188, 0181, 0185 or 0152), so tell the agent that the source beats the summary, and hardware beats both.
5. **Turn each repeated mistake into a check** (section 2) instead of a reminder in a prompt. Typical Pocket mistakes: bridge reads treated as synchronous (KB-008), per-bit synchronisers on buses (KB-009), a pin tie-off copied from another core, a stale `.rbf_r`.
6. **Treat the human trip as the scarce resource.** One card install should answer many questions: a diagnostic build that runs a battery of self-tests and shows every verdict on one report page (this is where the grid is strongest: one screenshot carries the whole battery). Ask for a written test list before the install, not after.
7. **Do not let the agent poll long jobs.** Launch the fit in the background, state the expected finish time, and have it resume on completion.

## 4. Whole-core simulation: what to model, and what not to fake

Model the Pocket side as a scripted host, written from the docs:

- boot order: status 1 (booting), 2 (setup), the host commands and data-slot writes, then target command 0140 (ready to run), status 3, reset exit, status 4;
- bridge reads: KB-008 says read data may arrive up to the next read strobe, so the model has to reproduce that, and tests should read back to back;
- the data loader pushes a byte every 8 clocks and cannot be told to wait (KB-028, community-reported, low confidence): test a client that stalls, such as SDRAM refresh;
- three unrelated clocks: `clk_74a`, `clk_74b` and your PLL outputs, with random phase per run;
- video (RGB888 with sync and enable), I2S audio at 48 kHz, and your SDRAM, PSRAM and cart models.

**Do not hand-write the vendor blocks that have subtle behaviour.** A wrong `dcfifo` or RAM model gives false passes. Use Intel's own simulation models (`<quartus>/eda/sim_lib/altera_mf.v`, never committed) as Tau's `sim/test_cymo_i2s_rate.py` already does, and hand-write only the PLL (it has no data behaviour, so sweep its phases instead). Whether the models compile in a given free simulator is **unverified** for your install; Tau's iverilog runs show it works for `dcfifo`.

Frame dumps against golden images also work as the "boot, read a file, show the picture" test. Keep Analogue's licensed APF files out of any public repo; reference them in your private tree.

## 5. Device-side channels the Pocket already has

| Channel | What it gives | Evidence and catch |
|---|---|---|
| **Target command 0152, Debug Event Log** | A time-stamped 32-bit value written to the log during runtime, in the shipping build, with no extra hardware | docs (host-target commands, framework 1.2). Needs Debug Logging on; the log goes to `/System/Logs/` on the SD card. **Unverified**: event rate, and whether the Developer menu is available on every unit. Tau's notes record that the template never issues it, so you add the command. |
| **Debug Logging and Asset Load Detail** | Boot and slot-load trace on the card | docs |
| **Pause Core Boot / Pause Load Data** | Time to arm a SignalTap trigger before boot or data load | docs, KB-018 |
| **Statistics overlay** | Video sync rate and status, plus temperature; power on developer units | docs |
| **USB SD access** | Pull logs and screenshots without removing the card, about 700 KB/s | docs |
| **Firmware measurement exposed over MMIO** | Real-silicon measurements with no cable, such as a toggle plus destination-domain counter for CDC timing | KB-082 (hardware-validated, local technique) |
| **Devkit debug cart** | A USB-UART (CP2104, up to 2 Mbps), needs `cartridge_adapter` 0 and cart power | KB-018 (community-reported) |
| **Link port as a serial line** | A UART to a cheap adapter | KB-013 (community-reported): needs `link_port: true` and `cartridge_adapter: 0`, which powers the cart port, so keep a game cart out; about 6 MHz limit, irrelevant for a UART |

JTAG facts that matter for the closed loop: reloading the bitstream over JTAG makes the Pocket re-run the whole load with the same starting conditions (docs, getting-started), so an agent can reflash and re-test unattended. **Never use a clone USB Blaster on the Pocket's header**: a clone was reported to have killed a Pocket (KB-018, community-reported). A cheap link-port adapter is a different thing and is not on the JTAG header.

Idea, not tested: inject button input through a register, so an agent can drive menus without a person. This depends on how the core takes controller bits; check your `cont1_key` path first.

## 6. Recommended order for a Pocket project

1. Reports and checks that cost minutes: JSON validator, package SHA check, map and fit gates, CDC lint.
2. Host tests with independent oracles, mutation sweeps, coverage.
3. Whole-core simulation with vendor models and a scripted host.
4. Per-block fits as a filter, then the full fit with a seed policy.
5. One self-testing diagnostic build per card install, reported through a grid.
6. At the desk: a JTAG master or serial line only when a question needs live data.

Not verified by this audit: nothing here was run. It is a review against the documents and the knowledge base. Items marked unverified need a test on your setup first.
