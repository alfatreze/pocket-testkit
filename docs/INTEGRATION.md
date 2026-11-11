# Integrating pocket-testkit into a project

Two ways in: **with an AI coding agent** or **by hand**. Both end at the same place: your device draws a picture, `decode.py` reads it, your code parses the payload.

## What you are wiring together

```
device firmware                          your PC / CI
  record bytes ──▶ encode ──▶ picture ──▶ screenshot or photo ──▶ decode ──▶ record bytes ──▶ your parser
  (your format)    tier L / R / Q        (a file)                  decode.py   (CRC checked)
```

The kit owns the middle. **Your record format is yours**: the kit carries bytes and checks them, it never interprets them.

## The decoders

| Tool | What it reads | Needs |
|---|---|---|
| `python/decode.py <image>` | **Everything.** Tries the colour grid (L, R), then QR (Q), and says which it found. `--json`, `--out file.bin`. Exit 0 ok, 1 unreadable | numpy, Pillow; OpenCV for QR |
| `python/tpg.py decode shot.png out.bin` | Grids only (L, R). Exit 1 on bad CRC | numpy, Pillow |
| `python/qr_decode.py` (`decode(path_or_array)`) | QR only. Tries the Aruco detector first, then the classic one, at scales 1-4 (dense 2 px codes need it) | OpenCV |

Rules for decoding: use the **original PNG** for the grids (a resized copy only works for tier R); a failed CRC means "damaged", never "retry with a different guess"; a phone photo reads as tier Q only.

```python
import sys; sys.path.insert(0, "pocket-testkit/python")
import decode
tier, payload = decode.decode("shot.png")     # tier 'L' | 'R' | 'Q', payload: bytes; raises ValueError if unreadable
```

## Choosing the tier and the QR density

| The picture leaves the device as... | Tier | Size |
|---|---|---|
| a screenshot file you copy off | **L** | up to ~259 KB |
| a screenshot sent through chat/email | **R** | up to ~6 KB |
| a photo from a phone | **Q**, level `photo` | up to 271 bytes (version 10) |

QR has **three density levels**, measured in `docs/qr_density.md` (see [DENSITY.md](DENSITY.md)). `photo` is the default. `careful` (to 1,003 B) and `max` (to 2,699 B, screenshots only) are deliberately harder to reach: `careful` warns; `max` raises an error unless you pass `allow_max=True` (CLI `--yes-max`, or type `MAX` at the prompt).

---

## Path A: with an AI coding agent

Works with Claude Code, Codex or any agent that reads a rules file.

1. **Give the agent the rules.** Copy [`agent/AGENTS.snippet.md`](../agent/AGENTS.snippet.md) into your project's `AGENTS.md` (Codex and others) or `CLAUDE.md` (Claude Code). It tells the agent the three tiers, the decoder command, that it must **not** raise the QR density on its own, and what evidence to claim.
2. **Add the kit.** Copy a tagged release into your repo (e.g. `third_party/pocket-testkit/`) and record the path, commit and SHA-256 in your provenance file. No submodule, so an upstream change cannot break you silently.
3. **Prompt it.** A prompt that works:

   > Add a report picture to the device's diagnostics page using pocket-testkit. Our record is the bytes produced by `<your function>`. Use tier R as the default view and tier L automatically if the record is over 6,059 bytes. Add a QR view at density `photo`; if the record is over 271 bytes, show a summary (verdict, counter, CRC32 of the full record) instead. Do not enable the `careful` or `max` densities. Wire a host test that encodes a sample record, decodes it with `python/decode.py --json` and compares the bytes. Then run `tests/test_decode_and_density.py`.

4. **Check the agent's work yourself, quickly:**
   - It called `qr_encode()` with `QR_V_PHOTO` (from `c/qr/qr_policy.h`) as `maxver`, not 38.
   - It did not add `--yes-max` or `allow_max=True` anywhere.
   - The test compares **bytes**, not just "decode succeeded".
   - Its claims say *host test* until a real picture from a real device was decoded. "Works on a phone" needs a decoded phone photo.
5. **Give it a way to see pictures.** An agent can read a screenshot you drop in the chat or a path, run `python3 python/decode.py <file> --json`, and parse the payload with your parser. Tell it to report exit code 1 as "unreadable", not to guess.

## Path B: manual development

### Device side (C)

1. Copy `c/tpg.h` (grid core: where the block is and which value pixel (x, y) has) and, if you want tier Q, `c/qr/qrcode.h`, `c/qr/qr_tables.h`, `c/qr/qr_policy.h`. Portable C; no libc beyond what you already link, no malloc; the QR needs a caller-supplied buffer of `QR_BUF_LEN` bytes (put it in slow RAM).
2. Build your record into a byte buffer.
3. Draw it. For the grid, loop over the screen and ask `tpg.h` for each pixel's value (see its header and `python/tpg.py`, which matches it pixel for pixel). For QR:

   ```c
   #include "qr/qrcode.h"
   #include "qr/qr_policy.h"
   static uint8_t qrbuf[QR_BUF_LEN];
   uint32_t ver, mask;
   uint32_t size = qr_encode(text, text_len, 1, QR_V_PHOTO, -1, qrbuf, &ver, &mask);  /* returns 0 if too big for a photo */
   if (!size) { /* show the summary instead, or tier R/L */ }
   else for (y..size) for (x..size) plot(qr_get(qrbuf, size, x, y));   /* 4+ px per module, 4-module white border */
   ```

4. Make the pages say what they are: a caption naming the tier and byte count, and a key that cycles views. A dense QR (`QR_V_MAX`) belongs behind a deliberate key press with a caption "SCREENSHOT ONLY".

### Host side (Python)

```bash
pip install numpy pillow opencv-python      # segno only for the QR test
python3 python/decode.py shot.png --json    # {"tier": "R", "length": 2352, "text": ...}
python3 python/decode.py shot.png --out record.bin
```

Then parse `record.bin` with your own code. In CI, run `decode.py` on the artifact screenshot and fail the job on exit code 1.

### Verify your integration (both paths)

```bash
python3 tests/test_decode_and_density.py    # decoder names each tier, bad pictures fail, density guard works
python3 tests/test_qr.py                    # the QR encoder against the segno reference, versions 1-38 (needs segno)
python3 tests/qr_density_study.py           # re-measure density on your own picture/screen size (several minutes)
```

Then the step no host test replaces: take a **real** picture on the real device and decode it. Log it as hardware evidence; log anything else as host or simulation.

### Common traps

- A screenshot re-saved as JPEG or resized breaks tier L; use R or keep the PNG.
- A dense QR (2 px modules) decodes from a PNG with `qr_decode.py` but a phone will not scan it.
- The default macOS SDK can fail to link the native QR helper; `qr_tier.py` retries other installed SDKs.
- Do not put a device id or other private data in a record that may be posted publicly.
