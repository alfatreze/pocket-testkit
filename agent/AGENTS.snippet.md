## Report pictures (pocket-testkit)

This project carries test and diagnostic results off the device as a picture. Do not invent a new format; use pocket-testkit.

- Tiers: **L** lossless colour grid (screenshot file only), **R** robust grid (survives JPEG/chat), **Q** QR (phone photo). Pick by how the picture leaves the device.
- Decode any picture with `python3 python/decode.py <image> --json`. Exit 1 means it could not be read: report that, never guess the payload.
- QR density: the default level is `photo` (QR version <= 10, 271 bytes). Never raise the level on your own. `careful` (<= 1,003 B) needs a stated reason; `max` (<= 2,699 B, screenshots only) needs the owner's explicit yes, and `--yes-max` / `allow_max=True` must not be added by an agent unasked.
- Screen size: pass the real screen size to the grid encoder (`size=(w, h)` / `tpg_init_ex`); never assume 400x360. Keep the 4 px cell unless asked. QR does not depend on the screen.
- Payload meaning is the project's, not the kit's: parse it in the project's own code.
- After any change: `tests/test_decode_and_density.py`, `tests/test_tpg_resolutions.py`, `tests/test_tpg_c.py` and `tests/test_qr.py` must pass. Say which evidence you have: host test, a screenshot decoded, or a real device/photo. Do not call a QR "phone-readable" unless a real phone photo was decoded.

## Debug link selection (pocket-testkit)

- To pick between report codes, ISSP, SignalTap, a Virtual JTAG window, a JTAG-to-Avalon master, a JTAG UART or a serial link, read `docs/DEBUG_LINK_CHOICE.md` and run `python3 tools/choose_link.py` with facts you read from the project (fit report headroom, existing register bus or Avalon system, blaster available, desk or field). Do not guess the facts.
- The RTL in `rtl/` is simulated only. Never describe it as working on hardware until `id` returned `0x504B0101` on a real Pocket. Never put a clone USB Blaster on the Pocket's JTAG header. Gate every link behind a macro so the shipped build has none.
- Resource costs of these blocks on Cyclone V are not measured: read them from the fit report and record them.

## Test ladder and project starter (pocket-testkit)

- For a new or existing project, adapt `templates/claude-project/` (CLAUDE.md, rules, status files, `ladder.json`, `tools/verdict.py`). Run `python3 tools/verdict.py` and read its one-line verdict; it reports manual rungs (fit, package check, device) as NOT RUN and never claims more evidence than was run.
- Validate a Pocket core folder with `tools/check_pocket_json.py` and compare the card's bitstream with the build output using `tools/check_package.py` before any hardware claim. Method overview: `docs/TESTING_METHODS.md`.

