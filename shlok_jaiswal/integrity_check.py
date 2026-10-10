# integrity_check.py  (Owner: Shlok Jaiswal)
# Quick self-test: every protocol must deliver the file perfectly, even when the
# channel loses, duplicates, reorders and corrupts packets.

import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "main_app"))
from main import run_transfer

os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
source = os.path.join(ROOT, "results", "check_in.bin")
target = os.path.join(ROOT, "results", "check_out.bin")
with open(source, "wb") as f:
    f.write(random.Random(7).randbytes(15000))

for protocol in ["stop-and-wait", "gbn", "sr"]:
    r = run_transfer(protocol, source, target, window=8, loss=0.15, duplicate=0.1,
                     reorder=0.1, corrupt=0.1, seed=3)
    status = "PASS" if r["intact"] else "FAIL"
    print(status, protocol, "retransmissions =", r["retransmissions"], "time = %.2fs" % r["time"])
    if not r["intact"]:
        sys.exit(1)
print("All protocols delivered the file intact.")
