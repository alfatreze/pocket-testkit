# Continuous integration

**Phase:** process · **Cost:** low · **Status in this kit:** one workflow (Rust crate on Linux, macOS, Windows, plus a WebAssembly build)

## What it does
Runs the host tests on every push so a broken test is noticed the same day. A suite nobody runs fails silently.

## Plan
| Where | What |
|---|---|
| **Hosted runner** (GitHub Actions) | Host tests, mutation spot checks, fuzzing for minutes, lint, link checks |
| **Build machine or VM** | Quartus map and fit (a hosted runner cannot practically run a fit), launched on demand or nightly |
| **Nightly** | Slow sweeps, seeds, coverage |

Record golden performance numbers (clocks per tile, frame time) and fail on regressions. Beware path quirks such as spaces in make variables.

## In this kit
[`.github/workflows/rust.yml`](../../.github/workflows/rust.yml). The Python, C and RTL tests are not in CI yet: add a job per method that runs its `tests/` (iverilog, a C compiler, `pip install numpy pillow opencv-python segno` are the needs).

## References
[GitHub Actions](https://docs.github.com/actions).
