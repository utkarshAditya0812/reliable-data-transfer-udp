
# go_back_n.py (Owner: Utkarsh Aditya)
# Go-Back-N sender and receiver implementation.

import time
from packet import make_packet, receive_packet, DATA, ACK, FIN, GIVE_UP_SECONDS


def send(chan, dest, chunks, window, timeout, adaptive=True):
    pass


def receive(chan, dest, window, linger):
    pass


def send(chan, dest, chunks, window, timeout, adaptive=True):
    items = [(DATA, c) for c in chunks] + [(FIN, b"")]
    total = len(items)
    packets = [make_packet(t, seq, p) for seq, (t, p) in enumerate(items)]

    base = 0
    next_seq = 0
    timer_start = time.time()
    last_progress = time.time()
    packets_sent = 0
    retransmissions = 0
    
    while base < total:
        while next_seq < total and next_seq < base + window:
            chan.sendto(packets[next_seq], dest)
            packets_sent += 1
            if base == next_seq:
                timer_start = time.time()
            next_seq += 1


