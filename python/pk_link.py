"""Frame helpers and a batch runner for pk_vjtag_regwin (see rtl/jtag/pk_vjtag_regwin.sv).

The frames are what the RTL expects: REQ DR = 48 bits {we, addr[14:0], data[31:0]};
RSP DR = 35 bits {overrun, busy, err, rdata[31:0]}; ID DR = 32 bits. Hardware not tested:
confirm with `id` first."""
import re
import subprocess
import sys
from pathlib import Path

ID_EXPECTED = 0x504B0101
TCL = Path(__file__).resolve().parent.parent / "host" / "pk_vjtag.tcl"


def pack_req(we: bool, addr: int, data: int) -> int:
    if not 0 <= addr < 1 << 15:
        raise ValueError("address is a 15-bit word address")
    return (int(bool(we)) << 47) | (addr << 32) | (data & 0xFFFFFFFF)


def unpack_rsp(v: int) -> dict:
    return {"data": v & 0xFFFFFFFF, "err": bool(v >> 32 & 1),
            "busy": bool(v >> 33 & 1), "overrun": bool(v >> 34 & 1)}


def run_batch(cmds, quartus_stp="quartus_stp", workdir=None):
    """cmds: list of ("r", addr) | ("w", addr, data) | ("id",). Returns parsed result dicts."""
    import tempfile
    lines = []
    for c in cmds:
        lines.append(" ".join(hex(x) if isinstance(x, int) else str(x) for x in c))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, dir=workdir) as f:
        f.write("\n".join(lines) + "\n")
        name = f.name
    out = subprocess.run([quartus_stp, "-t", str(TCL), "batch", name],
                         capture_output=True, text=True, check=True).stdout
    res = []
    for ln in out.splitlines():
        m = re.match(r"(r|w) (0x[0-9A-Fa-f]+) (0x[0-9A-Fa-f]+) err=(\d) overrun=(\d)", ln)
        if m:
            res.append({"op": m[1], "addr": int(m[2], 16), "data": int(m[3], 16),
                        "err": m[4] == "1", "overrun": m[5] == "1"})
        elif ln.startswith("id "):
            res.append({"op": "id", "data": int(ln.split()[1], 16)})
    return res


if __name__ == "__main__":
    print(run_batch([("id",), ("r", 0), ("w", 1, 0xCAFE1234), ("r", 1)]), file=sys.stdout)
