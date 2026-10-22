# plot_results.py  (Owner: Shlok Jaiswal)
# Reads the CSV files and draws 3 line plots (one line per protocol) into results/*.png

import os
import matplotlib
matplotlib.use("Agg")                  # draw to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")


def draw(csv_name, x_column, y_column, title, xlabel, ylabel, png_name):
    path = os.path.join(RESULTS, csv_name)
    if not os.path.exists(path):
        print("skipping", csv_name, "(run the experiments first)")
        return
    df = pd.read_csv(path)
    mean = df.groupby([x_column, "protocol"])[y_column].mean().reset_index()   # average of the runs
    plt.figure(figsize=(6, 4))
    for protocol in ["stop-and-wait", "gbn", "sr"]:
        part = mean[mean["protocol"] == protocol]
        plt.plot(part[x_column], part[y_column], marker="o", label=protocol)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS, png_name), dpi=120)
    plt.close()
    print("saved", png_name)


draw("exp_a_loss.csv", "loss", "goodput", "Goodput vs loss rate (window 8)",
     "loss probability", "goodput (bytes/s)", "goodput_vs_loss.png")
draw("exp_b_window.csv", "window", "goodput", "Goodput vs window size (loss 10%)",
     "window size", "goodput (bytes/s)", "goodput_vs_window.png")
draw("exp_c_reorder.csv", "reorder", "retransmissions", "Retransmissions vs reordering (window 8)",
     "reorder probability", "retransmissions", "retransmissions_vs_reorder.png")
