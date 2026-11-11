# Formal checks

**Phase:** check before you build · **Cost:** medium · **Status in this kit:** guide only, not set up

## What it does
Proves a property holds for all inputs up to a bound, instead of sampling with tests: random simulation says no failure was seen, formal says none exists (within the bound).

## Use it when
Small control logic with crisp properties: FIFOs ("never overflows"), port muxes ("done goes to exactly one client"), state machines ("no deadlock"), handshakes. Not for datapath arithmetic or whole cores.

## Pros and cons
| Pros | Cons |
|---|---|
| Finds corner cases no test reaches | Needs properties written; bounded proofs |
| Fast on small modules | Cannot prove clock-domain-crossing safety (metastability): use a synchroniser pattern and simulate many clock ratios and phases instead |
| | Tool language subset: check your SystemVerilog constructs are supported |

## Setup outline
[SymbiYosys](https://symbiyosys.readthedocs.io/) with Yosys and a solver: write `assert`/`assume`/`cover` properties in a wrapper, a `.sby` file, run `sby -f`. Keep properties next to the module and run them in [CI](../ci/README.md).

## Candidates in this kit
[`pk_reg_stream`](../debug-links/rtl/stream/pk_reg_stream.sv) (FIFO occupancy, no overflow) and [`pk_vjtag_regwin`](../debug-links/rtl/jtag/pk_vjtag_regwin.sv) (request/response handshake, no lost request). Not done.

## References
[SymbiYosys](https://symbiyosys.readthedocs.io/), [Yosys](https://github.com/YosysHQ/yosys).
