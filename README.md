<p align="center"><img src="docs/logo/banner.png" alt="pocket-testkit: a pixel handheld showing a colour grid, in the four CGA colours" width="640"></p>

# pocket-testkit

Get test and diagnostic results **off a device as a picture**, then decode them on a PC. A screenshot or a phone photo of a report page is the transport: no cable, no network, no file system on the device.

Extracted from the report codes of the Tau project for the Analogue Pocket. It works on any screen size.

## Pick a carrier

One payload and one CRC32, three ways to draw it. Choose by how the picture leaves the device.

| Tier | Carrier | Survives | Use when | Capacity |
|---|---|---|---|---|
| **L** | Lossless colour grid | a lossless PNG only | you copy the screenshot file off | table below (most) |
| **R** | Robust colour grid | JPEG q80+, chat resize | the screenshot goes through chat or email | table below |
| **Q** | QR code | a phone photo (small codes), any scanner app | an **external photo** of the screen | 271 B (photo) to 2,699 B (screenshot only) |

A damaged picture fails loudly on the CRC32; it is never decoded to a wrong payload.

## Capacity by screen size

The grid keeps the same pixel size on every screen (1 px per 16 bits for L, 4 px cells for R), so a bigger screen holds more. Payload bytes, header already deducted.

| Screen | Size | L, lossless | R, robust (4 px cells) |
|---|---|---|---|
| Game Boy | 160x144 | 41,456 | 956 |
| Game Boy Advance | 240x160 | 51,184 | 1,184 |
| QVGA | 320x240 | 115,184 | 2,684 |
| Small LCD | 480x272 | 147,952 | 3,452 |
| **Analogue Pocket** | 400x360 | 259,184 | 6,059 |
| VGA | 640x480 | 460,784 | 10,784 |
| WVGA | 800x480 | 460,784 | 10,784 |
| 720p | 1280x720 | 1,036,784 | 24,284 |
| 1080p | 1920x1080 | 2,332,784 | 54,659 |
| 4K | 3840x2160 | 9,331,184 | 218,684 |

QR does not depend on the screen. Its capacity is set by the QR version, and the screen only decides how large the modules are drawn:

| QR density level | Version | Bytes | Meant for |
|---|---|---|---|
| `photo` (default) | 1-10 | 271 | a phone scanner |
| `careful` | 11-22 | 1,003 | a steady, close, sharp photo (warns) |
| `max` | 23-38 | 2,699 | screenshots only; refused unless confirmed |

Why these limits, and the simulated-photo results behind them: [docs/DENSITY.md](docs/DENSITY.md). A robust grid with 8 px cells holds about a quarter of the R column and survives harsher scaling ([docs/RESOLUTIONS.md](docs/RESOLUTIONS.md)).

## Quick start

```bash
pip install numpy pillow opencv-python

python3 python/tpg.py encode report.bin shot.png --mode R --size 1280x720   # draw a grid for any screen
python3 python/qr_tier.py "PKT1 PASS run=17" qr.png                         # draw a QR (density photo)
python3 python/decode.py shot.png                                           # read any tier; --json, --out file
```

Rust: `cargo run --features cli --bin pocket-decode -- shot.png` in `rust/`. On a device, copy `c/tpg.h` and `c/qr/`. Full wiring, by hand or with an AI coding agent: [docs/INTEGRATION.md](docs/INTEGRATION.md).

## What the pictures look like

Left: the 400x360 screen as drawn on the device. Right: the code enlarged. Regenerate with `python3 examples/make_examples.py`.

**L, lossless grid** (2,352-byte sample report; a 40,000-byte report just grows the block)

![Lossless grid](docs/img/tier_l_lossless.png)
![Large lossless grid](docs/img/tier_l_large.png)

**R, robust grid** (decodes after JPEG q80)

![Robust grid](docs/img/tier_r_robust.png)

**Q, QR code**: a small summary code (photo level), and a dense one carrying the whole record (version 23, 2 px modules, screenshot only)

![QR code](docs/img/tier_q_qr.png)
![Dense QR code](docs/img/tier_q_dense.png)

**Simulated phone photos** (tilt, blur, noise, JPEG q70): the QR decodes, the colour grid does not. That is why tier Q exists.

| QR | Robust grid |
|---|---|
| ![](docs/img/sim_photo_qr.jpg) | ![](docs/img/sim_photo_robust_grid.jpg) |

## What is in the repo

| Path | What |
|---|---|
| `python/` | `decode.py` (any tier), `tpg.py` (grid encode/decode), `qr_tier.py` (QR draw + density guard), `qr_decode.py` (QR read) |
| `c/` | `tpg.h` (grid core), `qr/` (QR encoder, no libc, no malloc, versions 1-38) |
| `rust/` | OS-independent decoder crate: no dependencies in the core, `png` / `jpeg` / `qr` features, `pocket-decode` binary ([rust/README.md](rust/README.md)) |
| `docs/` | [INTEGRATION](docs/INTEGRATION.md), [DENSITY](docs/DENSITY.md), [RESOLUTIONS](docs/RESOLUTIONS.md), logo |
| `agent/` | [`AGENTS.snippet.md`](agent/AGENTS.snippet.md): rules to paste into an AI agent's instructions |
| `tests/` | tests and the density study |

Tests: `python3 tests/test_tpg_resolutions.py`, `test_tpg_c.py`, `test_decode_and_density.py`, `test_qr.py` (needs `pip install segno`), and `cargo test --features cli` in `rust/`.

## Format (TPG2)

A 16-byte header (`TPG2`, mode, flags, reserved, payload length, CRC32; big endian), then the payload, in a square block centred on the screen. The block side comes from a ladder that depends only on the screen's short side; flag byte 5 holds the robust cell size when it is not 4. At 400x360 the output is byte-identical to the original Pocket format (`tests/golden_400x360.json`). Details: the docstring in `python/tpg.py`.

## Status

| | Evidence |
|---|---|
| Grid on a real Pocket | Tau screenshots from its test cores decode; the Python and Rust decoders agree on all 31 real captures of Tau Omega's test data |
| QR on a real Pocket | decoded from real screenshots, up to a 2,281-byte dense code; the encoder also matches `segno` for all 38 versions |
| Rust crate | tests pass in CI on Linux, macOS and Windows; the core and QR build for WebAssembly |
| Other screen sizes | host tests only (13 sizes, Python and C equal pixel for pixel) |
| Phone photos | **simulated only**: no real phone trial recorded yet |

Not done: a real phone-photo trial, error correction for tier R, multi-QR for full reports through a camera, a web decoder, a sample test core for the Pocket.

## Licence

Apache License 2.0 ([LICENSE](LICENSE), [NOTICE](NOTICE)). The grid codec and QR encoder were written for Tau by the same author and are relicensed here. No copyleft code is included.
