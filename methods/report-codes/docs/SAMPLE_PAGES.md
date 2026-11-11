# Sample test pages

*Part of [report codes](../README.md). Paths below are relative to `methods/report-codes/`.*

Nine pages that show every carrier at a typical size and at its limit, for any screen size. The page logic is portable C (`c/sample/pk_sample.h`: no libc, no malloc, no I/O), so the same file renders on a PC today and is what a Pocket core's firmware would call. **Status: host-tested only** (all 54 pictures below decode back to the exact payload, and two injected bugs are caught). A [Pocket core](../core/README.md) that displays these pages exists and is simulated, but has not been compiled with Quartus or run on a Pocket.

## The pages

| # | Page | Carrier | Payload | Notes |
|---|---|---|---|---|
| 0 | L-sample | lossless grid | 256 B | a small block, centred |
| 1 | L-typical | lossless grid | 4 KB | a typical report |
| 2 | L-max | lossless grid | the screen's capacity | 259,184 B at 400x360 |
| 3 | R-sample | robust grid | 128 B | |
| 4 | R-max | robust grid | the screen's capacity | 6,059 B at 400x360 |
| 5 | Q-photo | QR | 120 B | phone-readable level |
| 6 | Q-photo-max | QR | 271 B | the largest "photo" payload (QR version 10) |
| 7 | Q-careful | QR | 1,003 B | steady, close, sharp photo |
| 8 | Q-max | QR | 2,699 B | **locked**: red stripes until deliberately unlocked; lossless screenshots only |

A payload the screen cannot carry is clamped, and the page says how much it kept (grid capacity grows with the screen; QR size is fixed by its version, but the symbol must still fit with modules of at least 2 px, so small screens clamp it). Every payload starts with a text line naming the page, size and byte count, so a decoded picture identifies itself, then a fixed filler pattern that a test checks byte for byte. A small marker of page+1 white squares sits in the top-left corner whenever it does not touch the code.

Ready-made pictures at 160x144, 400x360 and 800x480 (with the locked page unlocked): [docs/img/gallery](img/gallery) and its `manifest.tsv`. Regenerate them for any size:

```bash
python3 examples/make_gallery.py docs/img/gallery 320x240 800x720 --unlock
python3 python/decode.py docs/img/gallery/page2_L-max_400x360.png
```

## Experiment

1. Render pages for your screen size (above) and decode them: the decoder prints the tier and the payload's first line.
2. Degrade them like your real path does (chat resize, JPEG, a photo of the screen) and see which pages still decode: `python3 python/decode.py degraded.jpg`. Exit 1 means unreadable; a bad CRC is reported as such, never as a wrong payload.
3. Compare with [DENSITY.md](DENSITY.md) and [RESOLUTIONS.md](RESOLUTIONS.md). Those limits come from simulated photos; real phone photos of your screen are the better test.

## Use it in a core

```c
#include "sample/pk_sample.h"
static void row(void *ctx, uint32_t y, const uint16_t *rgb565, uint32_t w) { /* write the row to your frame buffer */ }
/* payload: PK_SAMPLE_PAYLOAD_MAX bytes (less on a small screen), qrbuf: QR_BUF_LEN bytes, 4-byte aligned, rowbuf: w uint16_t */
int r = pk_sample_draw(page, 400, 360, unlocked /* a deliberate key press */, payload, sizeof payload, qrbuf, rowbuf, row, 0, 0);
```

`pk_sample_info(page, w, h, &info)` tells what a page carries on a screen before you draw it. Memory: the payload buffer must hold the page's bytes (up to the grid capacity for the L-max page), so on a RAM-poor core use a smaller page set or keep the payload in external RAM.

## On a Pocket

The [sample-pages core](../core/README.md) loads one rendered page file (`host_gallery -b`) and shows it at 320x240, so a Pocket screenshot of each page can be decoded. Status and what is unverified are listed there. To draw the pages from firmware instead, call `pk_sample_draw` as above.
