# main.py  - the MAIN working file. Run:  python main_app/main.py --protocol sr --input main_app/sample_input.txt --loss 0.1
# It ties everything together: reads a file, sends it over UDP through the
# channel emulator using the chosen protocol, and checks the result with SHA-256.

import argparse
import os
import socket
import sys
import threading
import time

# --- make the member folders importable (they sit next to this folder) ---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for folder in ["main_app", "arijeet_kundu", "utkarsh_aditya", "vedant_bhatnagar", "shlok_jaiswal"]:
    sys.path.insert(0, os.path.join(ROOT, folder))

import config
import stop_and_wait
import go_back_n
import selective_repeat
from channel_emulator import ChannelSocket
from file_hash import files_match

PROTOCOLS = {
    "stop-and-wait": stop_and_wait,
    "gbn": go_back_n,
    "sr": selective_repeat,
}


def run_transfer(protocol, input_path, output_path, window=config.DEFAULT_WINDOW,
                 loss=0.0, duplicate=0.0, reorder=0.0, corrupt=0.0,
                 delay=config.DEFAULT_DELAY, jitter=config.DEFAULT_JITTER,
                 seed=1, timeout=config.DEFAULT_TIMEOUT, adaptive=True):
    module = PROTOCOLS[protocol]

    # 1) Read the file and cut it into pieces.
    with open(input_path, "rb") as f:
        data = f.read()
    size = config.PAYLOAD_SIZE
    chunks = [data[i:i + size] for i in range(0, len(data), size)]

    # 2) Make two UDP sockets (port 0 = let the OS pick a free port).
    sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_sock.bind((config.HOST, 0))
    receiver_sock.bind((config.HOST, 0))
    sender_addr = sender_sock.getsockname()
    receiver_addr = receiver_sock.getsockname()

    # 3) Wrap both in the bad-network emulator (different seeds for each direction).
    settings = dict(loss=loss, duplicate=duplicate, reorder=reorder,
                    corrupt=corrupt, delay=delay, jitter=jitter)
    sender_chan = ChannelSocket(sender_sock, seed=seed, **settings)
    receiver_chan = ChannelSocket(receiver_sock, seed=seed + 1000, **settings)

    # 4) Run the receiver in a background thread.
    outcome = {}

    def receiver_job():
        try:
            outcome["chunks"] = module.receive(receiver_chan, sender_addr, window, config.LINGER)
        except Exception as error:
            outcome["error"] = error

    thread = threading.Thread(target=receiver_job)
    thread.start()

    # 5) Run the sender here and time it.
    start = time.time()
    stats = module.send(sender_chan, receiver_addr, chunks, window, timeout, adaptive)
    elapsed = time.time() - start

    thread.join()
    sender_chan.close()
    receiver_chan.close()
    if "error" in outcome:
        raise outcome["error"]

    # 6) Save the received file and compare hashes.
    with open(output_path, "wb") as f:
        f.write(b"".join(outcome["chunks"]))

    stats.update({
        "protocol": protocol,
        "bytes": len(data),
        "time": elapsed,
        "goodput": len(data) / elapsed if elapsed > 0 else 0,   # useful bytes per second
        "intact": files_match(input_path, output_path),
        "dropped": sender_chan.dropped + receiver_chan.dropped,
    })
    return stats


def main():
    parser = argparse.ArgumentParser(description="Reliable file transfer over UDP")
    parser.add_argument("--protocol", choices=list(PROTOCOLS), required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="received_output.txt")
    parser.add_argument("--window", type=int, default=config.DEFAULT_WINDOW)
    parser.add_argument("--loss", type=float, default=0.0)
    parser.add_argument("--duplicate", type=float, default=0.0)
    parser.add_argument("--reorder", type=float, default=0.0)
    parser.add_argument("--corrupt", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=config.DEFAULT_TIMEOUT)
    args = parser.parse_args()

    r = run_transfer(args.protocol, args.input, args.output, args.window, args.loss,
                     args.duplicate, args.reorder, args.corrupt, seed=args.seed,
                     timeout=args.timeout)

    print("Protocol        :", r["protocol"])
    print("File size       :", r["bytes"], "bytes")
    print("Time taken      : %.3f s" % r["time"])
    print("Goodput         : %.0f bytes/s" % r["goodput"])
    print("Packets sent    :", r["packets_sent"])
    print("Retransmissions :", r["retransmissions"])
    print("Packets dropped :", r["dropped"])
    print("SHA-256 match   :", "YES - file is intact" if r["intact"] else "NO - file is broken!")


if __name__ == "__main__":
    main()
