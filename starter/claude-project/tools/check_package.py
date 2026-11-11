#!/usr/bin/env python3
"""A stale .rbf_r silently loads the old core: compare the file on the card with the build output.
  python3 tools/check_package.py build/output.rbf_r /Volumes/CARD/Cores/Author.Core/core.rbf_r     exit 0 = identical"""
import hashlib, sys
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    a, b = sha(sys.argv[1]), sha(sys.argv[2])
    print("build", a[:16], "card ", b[:16], "SAME" if a == b else "DIFFERENT: the card has another build")
    sys.exit(0 if a == b else 1)
