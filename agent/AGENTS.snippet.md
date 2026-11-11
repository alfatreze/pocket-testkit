## Report pictures (pocket-testkit)

This project carries test and diagnostic results off the device as a picture. Do not invent a new format; use pocket-testkit.

- Tiers: **L** lossless colour grid (screenshot file only), **R** robust grid (survives JPEG/chat), **Q** QR (phone photo). Pick by how the picture leaves the device.
- Decode any picture with `python3 python/decode.py <image> --json`. Exit 1 means it could not be read: report that, never guess the payload.
- QR density: the default level is `photo` (QR version <= 10, 271 bytes). Never raise the level on your own. `careful` (<= 1,003 B) needs a stated reason; `max` (<= 2,699 B, screenshots only) needs the owner's explicit yes, and `--yes-max` / `allow_max=True` must not be added by an agent unasked.
- Payload meaning is the project's, not the kit's: parse it in the project's own code.
- After any change: `python3 tests/test_decode_and_density.py` and `python3 tests/test_qr.py` must pass. Say which evidence you have: host test, a screenshot decoded, or a real device/photo. Do not call a QR "phone-readable" unless a real phone photo was decoded.
