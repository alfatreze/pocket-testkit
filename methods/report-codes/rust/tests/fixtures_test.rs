//! Every picture in tests/fixtures was made by the Python reference (tests/make_rust_fixtures.py); the Rust decoder must read each one
//! back to the same bytes and name the same tier.
use pocket_testkit::{files, Error, Options, Tier};
use std::path::PathBuf;

fn dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures")
}

#[test]
fn every_fixture_decodes_to_the_python_payload() {
    let manifest = std::fs::read_to_string(dir().join("manifest.tsv")).unwrap();
    let mut n = 0;
    for line in manifest.lines() {
        let f: Vec<&str> = line.split('\t').collect();
        let (file, tier, native, expected) = (f[0], f[1], f[2], f[3]);
        let mut opts = Options::default();
        if native != "-" {
            let (w, h) = native.split_once('x').unwrap();
            opts.native = Some((w.parse().unwrap(), h.parse().unwrap()));
        }
        let got = files::decode_file(dir().join(file), &opts).unwrap_or_else(|e| panic!("{file}: {e}"));
        let want = std::fs::read(dir().join(expected)).unwrap();
        assert_eq!(got.payload, want, "{file}: payload differs");
        let want_tier = match tier { "L" => Tier::L, "R" => Tier::R, _ => Tier::Q };
        assert_eq!(got.tier, want_tier, "{file}: tier");
        n += 1;
    }
    assert!(n >= 14, "expected the full fixture set, found {n}");
}

#[test]
fn blank_picture_is_not_found() {
    let rgb = vec![0u8; 800 * 480 * 3];
    assert_eq!(pocket_testkit::decode_rgb(800, 480, &rgb, &Options::default()), Err(Error::NotFound));
}

#[test]
fn damage_is_loud_never_a_wrong_payload() {
    let (w, h, mut rgb) = files::read_rgb(dir().join("grid_800x480_R.png")).unwrap();
    // wipe a patch of the centred block: the header still reads, the CRC must fail
    for y in 230..250 {
        for x in 380..420 {
            rgb[(y * w + x) * 3..][..3].copy_from_slice(&[255, 255, 255]);
        }
    }
    assert!(matches!(pocket_testkit::decode_rgb(w, h, &rgb, &Options::default()), Err(Error::Damaged(_))));
}

#[test]
fn lossless_needs_the_exact_picture() {
    // a lossless grid scaled to another size is not a grid any more: not found (or damaged), never a different payload
    let (w, h, rgb) = files::read_rgb(dir().join("grid_400x360_L.png")).unwrap();
    let r = pocket_testkit::decode_rgb(w, h, &rgb, &Options { native: Some((800, 720)), ..Options::default() });
    assert!(r.is_err());
}
