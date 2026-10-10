
# go_back_n.py  (Owner: Utkarsh Aditya)
# Go-Back-N: the sender may have up to `window` unacknowledged packets in flight.
# The receiver only accepts packets IN ORDER and sends CUMULATIVE ACKs:
#   ACK n means "I have received every packet below n, send me n next".
# If the timer expires, the sender goes back and resends the whole window.

import time
from packet import make_packet, receive_packet, DATA, ACK, FIN, GIVE_UP_SECONDS


def send(chan, dest, chunks, window, timeout, adaptive=True):
    items = [(DATA, c) for c in chunks] + [(FIN, b"")]
    total = len(items)
    packets = [make_packet(t, seq, p) for seq, (t, p) in enumerate(items)]

    base = 0                    # oldest packet not yet acknowledged
    next_seq = 0                # next new packet to send
    timer_start = time.time()   # one timer, for the oldest unacked packet
    last_progress = time.time()
    packets_sent = 0
    retransmissions = 0

    while base < total:
        # 1) Fill the window: send new packets while there is room.
        while next_seq < total and next_seq < base + window:
            chan.sendto(packets[next_seq], dest)
            packets_sent += 1
            if base == next_seq:                # window was empty -> start the timer
                timer_start = time.time()
            next_seq += 1

        # 2) Wait for an ACK, but no longer than the timer allows.
        remaining = timeout - (time.time() - timer_start)
        reply = receive_packet(chan, remaining) if remaining > 0 else None

        if reply is not None:
            reply_type, ack_number, _ = reply
            # Cumulative ACK: everything below ack_number has arrived.
            if reply_type == ACK and base < ack_number <= next_seq:
                base = ack_number                # slide the window forward
                timer_start = time.time()        # restart timer for the new oldest packet
                last_progress = time.time()
        elif time.time() - timer_start >= timeout:
            # 3) Timeout: go back and resend everything from base up to next_seq.
            for seq in range(base, next_seq):
                chan.sendto(packets[seq], dest)
                packets_sent += 1
                retransmissions += 1
            timer_start = time.time()

        if time.time() - last_progress > GIVE_UP_SECONDS:
            raise TimeoutError("go-back-n: receiver not responding")

    return {"packets_sent": packets_sent, "retransmissions": retransmissions}


def receive(chan, dest, window, linger):
    expected = 0            # next in-order sequence number we want
    chunks = []
    finished = False

    while True:
        wait = linger if finished else GIVE_UP_SECONDS
        packet = receive_packet(chan, wait)
        if packet is None:
            if finished:
                return chunks
            raise TimeoutError("go-back-n: sender went silent")

        packet_type, seq, payload = packet
        if packet_type == ACK:
            continue
        if seq == expected:                     # in order -> accept
            if packet_type == FIN:
                finished = True
            else:
                chunks.append(payload)
            expected += 1
        # Out-of-order packets are simply discarded (that is Go-Back-N!).
        # Always answer with a cumulative ACK = next packet we expect.
        chan.sendto(make_packet(ACK, expected),
