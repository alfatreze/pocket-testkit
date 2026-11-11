# Host tests: reference models, golden vectors, mutation, coverage

**Phase:** check before you build · **Cost:** low · **Status in this kit:** used throughout (see each method's `tests/`); no shared framework

## What it does
Runs your algorithms, parsers and formats on a PC, against an independent expectation, many times faster than any hardware loop.

## Techniques
| Technique | What it proves | Example here |
|---|---|---|
| **Reference model + golden vectors** | The implementation matches an independent definition bit for bit | C, Python and Rust codecs agree pixel for pixel; `methods/report-codes/tests/golden_400x360.json` |
| **Round trip** | Encode then decode returns the input; damage is detected, never mis-decoded | `test_decode_and_density.py`, `test_sample.py` (54 pictures) |
| **Mutation (break it on purpose)** | A test can actually fail | Every new test here was checked with an injected bug; for RTL see [MCY](https://github.com/YosysHQ/mcy) |
| **Coverage** | Which code or states no test touches | Not set up; [Verilator coverage](https://verilator.org/guide/latest/exe_verilator_coverage.html) for RTL, `gcov`/`llvm-cov` for C |
| **Damage models** | Behaviour under JPEG, resize, noise | the simulated-photo study in [report-codes](../report-codes/docs/DENSITY.md) |

## Pros and cons
| Pros | Cons |
|---|---|
| Fast, repeatable, no hardware | Only as good as the oracle: a model written from the same misconception passes wrongly |
| Mutation and coverage show what the tests miss | Says nothing about timing or the real device |

## Rules that make it work
1. Write the expected behaviour from the **spec or real captures**, not from the code under test.
2. Every test must be shown to fail on a deliberate bug (mutation) at least once.
3. Report the result with the `host` evidence label; do not call it hardware-verified.

## References
[pytest](https://docs.pytest.org/), [Verilator coverage](https://verilator.org/guide/latest/exe_verilator_coverage.html), [MCY](https://github.com/YosysHQ/mcy). Method: [docs/methodology.md](../../docs/methodology.md).
