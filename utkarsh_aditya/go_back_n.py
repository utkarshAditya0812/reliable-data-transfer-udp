import time
from packet import make_packet, receive_packet, DATA, ACK, FIN, GIVE_UP_SECONDS


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

    return {"packets_sent": packets_sent, "retransmissions": retransmissions}
