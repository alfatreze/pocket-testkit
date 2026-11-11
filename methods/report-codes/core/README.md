# Sample-pages Pocket core

An Analogue Pocket core that shows one report-code picture at a time (a lossless grid, a robust grid or a QR code), so you can take **real Pocket screenshots** of every carrier at its limits and decode them with this kit. **Status: simulated only.** The RTL passes iverilog simulations; it has **not** been compiled with Quartus, fitted, or run on a Pocket.

## How it works
The PC renders the pages with the same C code a firmware would use ([`c/sample/pk_sample.h`](../c/sample/pk_sample.h), via `host_gallery -b`) into raw picture files. The Pocket loads one file through a data slot into block RAM; a fixed timing generator scans it out at 320x240, 60 Hz. No CPU, no SDRAM. The screenshot of that screen is the test: it should decode to the page's payload.

```
page.bin (320x240 RGB565, big-endian)  --data slot-->  bridge write 0x10000000+  -->  M10K RAM (38,400 x 32 bit)
                                                                                         |  read in the video clock
  interact "Swap bytes" 0x20000000, "Swap pixels" 0x20000004  -->  byte/pixel order  -->  RGB565 -> RGB888 (bit replication)  -->  video
```

| File | Role |
|---|---|
| [`rtl/pk_fb_video.sv`](rtl/pk_fb_video.sv) | The whole core logic: framebuffer, video timing, the two switches |
| [`json/`](json/) | `core.json`, `data.json` (one slot, exactly 153,600 bytes), `video.json` (320x240), `interact.json` (two switches), `audio.json`, `input.json` |
| [`assemble.py`](assemble.py) | `build`: copies your local Analogue core template and patches it; `package`: makes the SD-card tree and the page files |
| [`sim/`](sim/), [`tests/`](tests/) | Testbench and tests (below) |

## Analogue's template is not in this repo
The template belongs to Analogue. Clone it yourself ([open-fpga/core-template](https://github.com/open-fpga/core-template)); `assemble.py build` copies it, adds `pk_fb_video.sv`, swaps the five `video_*` assignments in `core_top.v` to our outputs, instantiates the viewer, and adds the file to the `.qsf`. It stops with a clear error if the template differs (tested against v1.3.0).

## Build and run
```bash
python3 assemble.py build --template path/to/core-template --out /tmp/pkbuild
cd /tmp/pkbuild/src/fpga && quartus_sh --flow compile ap_core        # Quartus Prime Lite 25.1; a few minutes expected, not yet measured
python3 assemble.py package --rbf output_files/ap_core.rbf --out /tmp/pksd
```
Copy `Cores/` and `Assets/` from `/tmp/pksd` to the Pocket's SD card root (back up the card first). Launch the core: the Pocket asks for a page file from `/Assets/_none/alfatreze.PKPages/`. To change page, use the core's menu entry to reload the slot. Take a screenshot (Pocket's screenshot combination) and decode it:

```bash
python3 ../python/decode.py screenshot.png
```

## The pages (at 320x240)
L-sample 256 B, L-typical 4 KB, L-max 115,184 B, R-sample 128 B, R-max 2,684 B, Q-photo 120 B, Q-photo-max 271 B, Q-careful 1,003 B, and Q-max (clamped to 1,091 B at this size, the largest QR that fits with 2 px modules). A page that does not fit is clamped by the page code, as in [SAMPLE_PAGES](../docs/SAMPLE_PAGES.md).

## If the colours look wrong
The file format is big-endian RGB565 (high byte first), assuming the bridge delivers the first file byte in bits 31:24 when `bridge_endian_little = 0` (the template default). I could not confirm that from the docs. If the picture is noise: turn on **Swap bytes**, **Swap pixels**, or both in the core's menu; one of the four combinations is right, and the result is the answer to record.

## What is and is not verified
| Verified (simulation, `tests/test_core_sim.py`) | Not verified |
|---|---|
| Six pages go from `.bin` through simulated bridge writes to a captured video frame that equals the expected expanded picture pixel for pixel and decodes to the payload | Quartus compile and fit (RAM inference as M10K with `no_rw_check`, timing, the template patch building) |
| 60.000 Hz frame period, 512 hsync pulses per frame, hsync three clocks after vsync | Anything on a real Pocket: the file order the bridge delivers, the video sync range, screenshot contents |
| The two switches fix byte-swapped and pixel-swapped files, and a swapped file does not decode without them | Resource use (expected about 150 of 308 M10K blocks, unmeasured) |
| Five injected RTL bugs are caught (pixel order, frame restart, address window, hsync, colour expansion) | |

Tests: `python3 tests/test_core_sim.py` (iverilog and a C compiler), `python3 tests/test_core_files.py` (no tools needed) from this folder.
