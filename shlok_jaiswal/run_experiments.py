# run_experiments.py  (Owner: Shlok Jaiswal)
# Runs the experiments from our proposal and saves results into results/*.csv
# Usage: python shlok_jaiswal/run_experiments.py [a] [b] [c]      (no argument = run all)
#   a = goodput vs loss rate         (fixed window)
#   b = goodput vs window size       (fixed loss)
#   c = retransmissions vs reordering

import csv
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "main_app"))
from main import run_transfer          # main.py also sets up the other folders

RESULTS = os.path.join(ROOT, "results")
TEST_FILE = os.path.join(RESULTS, "test_file.bin")
OUT_FILE = os.path.join(RESULTS, "received_%d.bin" % os.getpid())   # own output file per run
PROTOCOLS = ["stop-and-wait", "gbn", "sr"]
RUNS = 3                               # repeat each setting 3 times (different seeds)


def make_test_file():
    # A fixed 40 KB file of random bytes (seeded so it is always the same).
    os.makedirs(RESULTS, exist_ok=True)
    if os.path.exists(TEST_FILE):
        return
    with open(TEST_FILE, "wb") as f:
        f.write(random.Random(42).randbytes(40000))


def run_one(name, columns, settings_list):
    # settings_list: list of (x_value, keyword-arguments for run_transfer)
    rows = []
    for x, kwargs in settings_list:
        for protocol in PROTOCOLS:
            for run in range(RUNS):
                # SR uses a FIXED timeout here so the comparison with the others is fair.
                r = run_transfer(protocol, TEST_FILE, OUT_FILE, seed=run + 1,
                                 adaptive=False, **kwargs)
                assert r["intact"], "file corrupted!"
                rows.append([x, protocol, run, round(r["goodput"], 1),
                             r["retransmissions"], round(r["time"], 3)])
                print(name, x, protocol, "run", run, "goodput", round(r["goodput"]))
    with open(os.path.join(RESULTS, name + ".csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([columns, "protocol", "run", "goodput", "retransmissions", "time"])
        writer.writerows(rows)


def experiment_a():   # loss 0% to 30%, window 8
    run_one("exp_a_loss", "loss",
            [(l, dict(loss=l, window=8)) for l in [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]])


def experiment_b():   # window 1..16, loss 10%
    run_one("exp_b_window", "window",
            [(w, dict(loss=0.10, window=w)) for w in [1, 2, 4, 8, 16]])


def experiment_c():   # reordering 0..40%, no loss, window 8
    run_one("exp_c_reorder", "reorder",
            [(p, dict(reorder=p, window=8)) for p in [0, 0.1, 0.2, 0.3, 0.4]])


if __name__ == "__main__":
    make_test_file()
    chosen = sys.argv[1:] or ["a", "b", "c"]
    if "a" in chosen:
        experiment_a()
    if "b" in chosen:
        experiment_b()
    if "c" in chosen:
        experiment_c()
    if os.path.exists(OUT_FILE):
        os.remove(OUT_FILE)             # clean up the temporary received file
