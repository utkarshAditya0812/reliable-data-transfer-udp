# stop_and_wait.py  (Owner: Arijeet Kundu)
# Stop-and-Wait: send ONE packet, wait for its ACK, only then send the next one.
# If the ACK does not come in `timeout` seconds, send the same packet again.

import time
from packet import make_packet, receive_packet, DATA, ACK, FIN, GIVE_UP_SECONDS


def send(chan, dest, chunks, window, timeout, adaptive=True):
    # `window` and `adaptive` are unused here (kept so all protocols look the same).
    items = [(DATA, c) for c in chunks] + [(FIN, b"")]   # file pieces + a final FIN
    packets_sent = 0
    retransmissions = 0

    for seq, (packet_type, payload) in enumerate(items): # seq = 0, 1, 2, ...
        packet = make_packet(packet_type, seq, payload)
        acked = False
        first_try = True
        started = time.time()

        while not acked:
            chan.sendto(packet, dest)                    # (re)send the packet
            packets_sent += 1
            if not first_try:
                retransmissions += 1                     # this was a repeat
            first_try = False

            deadline = time.time() + timeout             # start the timer
            while not acked:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break                                # timer expired -> resend
                reply = receive_packet(chan, remaining)
                if reply is None:
                    break                                # timer expired -> resend
                reply_type, reply_seq, _ = reply
                if reply_type == ACK and reply_seq == seq:
                    acked = True                         # the ACK we wanted!

            if time.time() - started > GIVE_UP_SECONDS:
                raise TimeoutError("stop-and-wait: receiver not responding")

    return {"packets_sent": packets_sent, "retransmissions": retransmissions}


def receive(chan, dest, window, linger):
    expected = 0            # the sequence number we are waiting for
    chunks = []             # file pieces received so far, in order
    finished = False        # becomes True once FIN has arrived

    while True:
        # After FIN we hang around `linger` seconds in case our last ACK got lost.
        wait = linger if finished else GIVE_UP_SECONDS
        packet = receive_packet(chan, wait)
        if packet is None:
            if finished:
                return chunks                            # all done
            raise TimeoutError("stop-and-wait: sender went silent")

        packet_type, seq, payload = packet
        if packet_type == ACK:
            continue                                     # not for us
        if seq == expected:                              # the packet we were waiting for
            if packet_type == FIN:
                finished = True
            else:
                chunks.append(payload)
            expected += 1
        if seq < expected:                               # new or duplicate -> ACK it
            chan.sendto(make_packet(ACK, seq), dest)
