# selective_repeat.py  (Owner: Vedant Bhatnagar)
# Selective Repeat: like Go-Back-N, but
#   * every packet gets its OWN ACK and its OWN timer,
#   * the receiver BUFFERS out-of-order packets,
#   * on timeout only the one missing packet is resent (not the whole window).

import time
from packet import make_packet, receive_packet, DATA, ACK, FIN, GIVE_UP_SECONDS
from rto import RTOEstimator


def send(chan, dest, chunks, window, timeout, adaptive=True):
    items = [(DATA, c) for c in chunks] + [(FIN, b"")]
    total = len(items)
    packets = [make_packet(t, seq, p) for seq, (t, p) in enumerate(items)]

    rto = RTOEstimator(timeout, adaptive)   # adaptive timeout (Jacobson/Karels + Karn)
    acked = [False] * total                 # has packet i been acknowledged?
    sent_at = [0.0] * total                 # when packet i was last sent
    resent = [False] * total                # was packet i ever retransmitted?

    base = 0                                # oldest unacknowledged packet
    next_seq = 0                            # next new packet to send
    packets_sent = 0
    retransmissions = 0
    last_progress = time.time()

    while base < total:
        # 1) Send new packets while the window has room.
        while next_seq < total and next_seq < base + window:
            chan.sendto(packets[next_seq], dest)
            sent_at[next_seq] = time.time()
            packets_sent += 1
            next_seq += 1

        # 2) Wait for an ACK until the earliest packet timer would expire.
        earliest = min(sent_at[s] + rto.value for s in range(base, next_seq) if not acked[s])
        wait = max(0.001, earliest - time.time())
        reply = receive_packet(chan, wait)

        if reply is not None:
            reply_type, seq, _ = reply
            if reply_type == ACK and base <= seq < next_seq and not acked[seq]:
                acked[seq] = True                       # mark just this packet as done
                last_progress = time.time()
                if not resent[seq]:                     # Karn (a): only clean samples
                    rto.update(time.time() - sent_at[seq])
                while base < total and acked[base]:     # slide window over finished packets
                    base += 1

        # 3) Resend ONLY the packets whose own timer has expired.
        now = time.time()
        timed_out = False
        for seq in range(base, next_seq):
            if not acked[seq] and now - sent_at[seq] >= rto.value:
                chan.sendto(packets[seq], dest)
                sent_at[seq] = now
                resent[seq] = True
                packets_sent += 1
                retransmissions += 1
                timed_out = True
        if timed_out:
            rto.backoff()                               # Karn (b): double the RTO

        if now - last_progress > GIVE_UP_SECONDS:
            raise TimeoutError("selective-repeat: receiver not responding")

    return {"packets_sent": packets_sent, "retransmissions": retransmissions,
            "final_rto": rto.value}


def receive(chan, dest, window, linger):
    rcv_base = 0            # lowest sequence number not yet delivered
    buffer = {}             # out-of-order packets waiting: seq -> (type, payload)
    chunks = []
    finished = False

    while True:
        wait = linger if finished else GIVE_UP_SECONDS
        packet = receive_packet(chan, wait)
        if packet is None:
            if finished:
                return chunks
            raise TimeoutError("selective-repeat: sender went silent")

        packet_type, seq, payload = packet
        if packet_type == ACK:
            continue

        if rcv_base <= seq < rcv_base + window:         # inside our receive window
            buffer[seq] = (packet_type, payload)        # keep it (even if out of order)
            chan.sendto(make_packet(ACK, seq), dest)    # ACK this exact packet
            while rcv_base in buffer:                   # deliver everything now in order
                stored_type, stored_payload = buffer.pop(rcv_base)
                if stored_type == FIN:
                    finished = True
                else:
                    chunks.append(stored_payload)
                rcv_base += 1
        elif seq < rcv_base:                            # old packet: our ACK was lost
            chan.sendto(make_packet(ACK, seq), dest)    # so ACK again
