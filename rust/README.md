# pocket-testkit (Rust crate)

Decode test and diagnostic reports that a device carries out as a picture: the colour pixel grid at **any screen size** (tiers L and R) and QR codes (tier Q). Pure Rust: the core takes raw RGB bytes, makes no OS calls and has **no dependencies**, so it builds on Windows, macOS, Linux and WebAssembly. Files and QR are opt-in features.

| Feature | Adds | Dependency |
|---|---|---|
| *(none)* | `tpg::decode_rgb`, `decode_rgb` (grids), CRC-32 | none |
| `png` | PNG files and bytes | `png` |
| `jpeg` | JPEG files and bytes (phone photos, chat copies) | `zune-jpeg` |
| `qr` | `qr::decode_rgb`, QR as tier Q in `decode_rgb` | `rqrr` |
| `cli` | the `pocket-decode` binary (png + jpeg + qr) | the three above |

```toml
[dependencies]
pocket-testkit = { path = "third_party/pocket-testkit/rust", features = ["png", "qr"] }
```

```rust
use pocket_testkit::{files, Options, Tier};

let d = files::decode_file("shot.png", &Options::default())?;      // grid L or R first, then QR
println!("tier {:?}, {} bytes", d.tier, d.payload.len());

// raw pixels from anywhere (a wasm canvas, a capture card): w * h * 3 packed RGB
let d = pocket_testkit::decode_rgb(w, h, &rgb, &Options::default())?;

// a resized copy of a robust grid: say which screen it was made for
let opts = Options { native: Some((1280, 720)), ..Options::default() };
```

Errors are `Error::NotFound` (no grid, no QR), `Error::Damaged` (a header was found but the CRC32 failed: never a wrong payload) and `Error::Invalid` (unusable input).

```bash
cargo run --features cli --bin pocket-decode -- shot.png [--native 1280x720] [--out record.bin] [--json]
```

Exit 0 decoded, 1 unreadable, 2 usage.

## What is proven

- `cargo test --features cli`: 14 pictures made by the Python reference (grids at 160x144, 400x360, 720x1280, 800x480, 1280x720, 1920x1080, cells of 2, 4 and 8 px, a JPEG q80 copy, a half-size copy with `native`, QR on three screen sizes, a dense QR) decode to the same bytes and tier; a blank picture is not found; damage is reported, not guessed.
- The Rust and Python decoders gave the same result on all 31 screenshots of real Pocket reports in Tau Omega's test data (grid L in both layouts, grid R, QR up to a 2,281-byte dense code). Those captures are not copied here.
- `.github/workflows/rust.yml` runs the tests on Ubuntu, macOS and Windows and builds for `wasm32-unknown-unknown`; check the badge/status before relying on a platform.

Limits: decoder only (encoders are in `python/` and `c/`); the QR reader is `rqrr`, so very dense codes in a blurry photo are less forgiving than the Python decoder's Aruco path; no error correction in the grid.
