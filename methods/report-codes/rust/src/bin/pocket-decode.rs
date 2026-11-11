//! `pocket-decode <picture> [--native WxH] [--out file] [--json]`: decode a screenshot or photo. Exit 0 ok, 1 unreadable, 2 usage.
use pocket_testkit::{files, Options, Tier};
use std::process::ExitCode;

fn main() -> ExitCode {
    let mut path = None;
    let (mut out, mut json, mut opts) = (None, false, Options::default());
    let mut args = std::env::args().skip(1);
    while let Some(a) = args.next() {
        match a.as_str() {
            "--json" => json = true,
            "--out" => out = args.next(),
            "--native" => {
                let v = args.next().unwrap_or_default();
                match v.to_lowercase().split_once('x').and_then(|(w, h)| Some((w.parse().ok()?, h.parse().ok()?))) {
                    Some(wh) => opts.native = Some(wh),
                    None => return usage(),
                }
            }
            _ if path.is_none() && !a.starts_with("--") => path = Some(a),
            _ => return usage(),
        }
    }
    let Some(path) = path else { return usage() };
    match files::decode_file(&path, &opts) {
        Ok(d) => {
            if let Some(o) = out {
                if std::fs::write(&o, &d.payload).is_err() {
                    eprintln!("cannot write {o}");
                    return ExitCode::from(1);
                }
            }
            let tier = match d.tier { Tier::L => "L", Tier::R => "R", Tier::Q => "Q" };
            match String::from_utf8(d.payload.clone()) {
                Ok(t) if json => println!("{{\"tier\":\"{tier}\",\"length\":{},\"text\":{:?}}}", d.payload.len(), t),
                Ok(t) => println!("tier {tier}, {} bytes\n{}", d.payload.len(), t.chars().take(2000).collect::<String>()),
                Err(_) => {
                    let hex: String = d.payload.iter().map(|b| format!("{b:02x}")).collect();
                    if json { println!("{{\"tier\":\"{tier}\",\"length\":{},\"payload_hex\":\"{hex}\"}}", d.payload.len()) } else { println!("tier {tier}, {} bytes\n{}", d.payload.len(), &hex[..hex.len().min(2000)]) }
                }
            }
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("invalid: {e}");
            ExitCode::from(1)
        }
    }
}

fn usage() -> ExitCode {
    eprintln!("usage: pocket-decode <picture.png|jpg> [--native WxH] [--out file] [--json]");
    ExitCode::from(2)
}
