# Fuzzing

**Phase:** check before you build · **Cost:** low (about an afternoon to set up) · **Status in this kit:** guide only, not set up

## What it does
Feeds random and mutated inputs to a parser or decoder under sanitizers, to find crashes, hangs and out-of-bounds access, and to test claims such as "any byte string decodes in bounded time".

## Use it when
Firmware or tools parse untrusted or user-supplied data: file containers, save files, image or audio headers, protocol frames. Good for AI-written parsers, which tend to trust their input.

## Pros and cons
| Pros | Cons |
|---|---|
| Finds bugs nobody thought to write a test for | Needs a harness per parser; finds crashes, not wrong answers |
| Seeded from real files it reaches deep states | Host builds differ from the soft CPU (stack, heap, word size): also run the parser once on the target CPU in simulation |

## Setup outline
1. Put the parser behind a function `parse(const uint8_t *data, size_t len)` with no I/O.
2. Build a harness with [libFuzzer](https://llvm.org/docs/LibFuzzer.html) or [AFL++](https://aflplus.plus/), with `-fsanitize=address,undefined`.
3. Seed with real files; keep the corpus in the repo; run in [CI](../ci/README.md) for a few minutes per push.

## Candidates in this kit
The report-code decoder paths ([`methods/report-codes/python`](../report-codes/python/), `rust/`) take untrusted images: the Rust crate is the natural first target (`cargo fuzz`). Not done.

## References
[libFuzzer](https://llvm.org/docs/LibFuzzer.html), [AFL++](https://aflplus.plus/), [OSS-Fuzz](https://github.com/google/oss-fuzz).
