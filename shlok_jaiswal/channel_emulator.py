# channel_emulator.py  (Owner: Shlok Jaiswal)
# A fake "bad network". It wraps a normal UDP socket. Every packet we SEND goes
# through it first, and it may: drop it, duplicate it, corrupt it, or delay it.
# A seed makes the randomness repeatable (same seed -> same behaviour).
# Delayed packets wait in a 'waiting room' (a heap sorted by release time); one
# background thread sends each packet when its time comes, so equal delays stay in order.

import heapq
import random
import threading
import time

REORDER_EXTRA_DELAY = 0.02      # a "reordered" packet is delayed 20 ms extra, so later packets overtake it


class ChannelSocket:
    def __init__(self, sock, loss=0.0, duplicate=0.0, reorder=0.0,
                 corrupt=0.0, delay=0.0, jitter=0.0, seed=None):
        self.sock = sock                    # the real UDP socket underneath
        self.loss = loss                    # probability (0 to 1) a packet is dropped
        self.duplicate = duplicate          # probability a packet is sent twice
        self.reorder = reorder              # probability a packet is delayed extra
        self.corrupt = corrupt              # probability a byte in the packet is damaged
        self.delay = delay                  # fixed one-way delay in seconds
        self.jitter = jitter                # random extra delay between 0 and jitter seconds
        self.rng = random.Random(seed)      # our own random generator (seeded = repeatable)
        self.dropped = 0                    # counters for reporting
        self.corrupted = 0
        self.duplicated = 0
        self.waiting = []                   # the waiting room: (release_time, number, packet, addr)
        self.counter = 0                    # tie-breaker so equal release times keep sending order
        self.closed = False
        self.lock = threading.Condition()   # lets the worker sleep until something arrives
        threading.Thread(target=self._worker, daemon=True).start()

    def sendto(self, data, addr):
        if self.rng.random() < self.loss:   # roll the dice: lose the packet?
            self.dropped += 1
            return

        copies = 1
        if self.rng.random() < self.duplicate:
            copies = 2                      # send the same packet twice
            self.duplicated += 1

        for _ in range(copies):
            packet = data
            if self.rng.random() < self.corrupt:
                packet = self._damage(data)
                self.corrupted += 1
            wait = self.delay + self.rng.uniform(0, self.jitter)
            if self.rng.random() < self.reorder:
                wait += REORDER_EXTRA_DELAY
            self._deliver(packet, addr, wait)

    def _damage(self, data):
        broken = bytearray(data)
        position = self.rng.randrange(len(broken))   # pick a random byte
        broken[position] ^= 0xFF                     # flip all its bits
        return bytes(broken)

    def _deliver(self, packet, addr, wait):
        if wait <= 0:
            self._raw_send(packet, addr)             # no delay -> send right now
            return
        with self.lock:
            heapq.heappush(self.waiting, (time.time() + wait, self.counter, packet, addr))
            self.counter += 1                        # put the packet in the waiting room
            self.lock.notify()                       # wake the worker

    def _worker(self):
        while True:
            with self.lock:
                if self.closed:
                    return
                if not self.waiting:
                    self.lock.wait()                 # nothing to send: sleep
                    continue
                release, _, packet, addr = self.waiting[0]   # the packet due first
                now = time.time()
                if release > now:
                    self.lock.wait(release - now)    # not due yet: sleep until it is
                    continue
                heapq.heappop(self.waiting)          # due now: take it out
            self._raw_send(packet, addr)             # send outside the lock

    def _raw_send(self, packet, addr):
        try:
            self.sock.sendto(packet, addr)
        except OSError:
            pass                                     # socket already closed, ignore

    # The three methods below just pass through to the real socket.
    def recvfrom(self, size):
        return self.sock.recvfrom(size)

    def settimeout(self, seconds):
        self.sock.settimeout(seconds)

    def close(self):
        with self.lock:
            self.closed = True                       # tell the worker to stop
            self.lock.notify()
        self.sock.close()
def test_stats(seed=42, loss=0.2, duplicate=0.1, corrupt=0.05, reorder=0.1, delay=0.01, jitter=0.005):
    """
    Comprehensive stats test: sends multiple packets and reports all channel metrics.
    Demonstrates that the channel emulator correctly tracks and reports its behavior.
    """
    import socket

    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.bind(("127.0.0.1", 0))
    receiver_addr = receiver.getsockname()
    receiver.settimeout(2)

    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    chan = ChannelSocket(
        sock=sender,
        loss=loss,
        duplicate=duplicate,
        reorder=reorder,
        corrupt=corrupt,
        delay=delay,
        jitter=jitter,
        seed=seed
    )

    num_packets = 20
    print(f"=== Channel Stats Test ===")
    print(f"Seed: {seed}")
    print(f"Parameters: loss={loss}, dup={duplicate}, corrupt={corrupt}, reorder={reorder}, delay={delay}s, jitter={jitter}s")
    print(f"Sending {num_packets} packets...\n")

    for i in range(num_packets):
        msg = f"Packet-{i:02d}".encode()
        chan.sendto(msg, receiver_addr)

    received = []
    try:
        while True:
            data, _ = receiver.recvfrom(4096)
            received.append(data)
    except socket.timeout:
        pass

    print(f"--- Results ---")
    print(f"Packets sent (original): {num_packets}")
    print(f"Packets received: {len(received)}")
    print(f"Dropped by channel: {chan.dropped}")
    print(f"Duplicated by channel: {chan.duplicated}")
    print(f"Corrupted by channel: {chan.corrupted}")
    print(f"Total delivered (including duplicates): {len(received)}")

    sender.close()
    receiver.close()
    chan.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test the channel emulator")
    parser.add_argument("--mode", choices=["quick", "stats"], default="quick",
                        help="quick = single packet test, stats = comprehensive multi-packet test")
    parser.add_argument("--loss", type=float, default=0.2)
    parser.add_argument("--duplicate", type=float, default=0.0)
    parser.add_argument("--corrupt", type=float, default=0.0)
    parser.add_argument("--reorder", type=float, default=0.0)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--jitter", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.mode == "stats":
        test_stats(
            seed=args.seed,
            loss=args.loss,
            duplicate=args.duplicate,
            corrupt=args.corrupt,
            reorder=args.reorder,
            delay=args.delay,
            jitter=args.jitter
        )
    else:
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver.bind(("127.0.0.1", 0))
        receiver_addr = receiver.getsockname()
        receiver.settimeout(2)

        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        chan = ChannelSocket(sock=sender, loss=args.loss, duplicate=args.duplicate,
                             corrupt=args.corrupt, seed=args.seed)

        message = b"Hello, this is a test packet from Shlok Jaiswal"
        print(f"Sent: {message}")

        chan.sendto(message, receiver_addr)

        try:
            received, _ = receiver.recvfrom(4096)
            print(f"Received: {received}")
            print(f"Intact: {received == message}")
        except socket.timeout:
            print("Packet was dropped by the channel (expected with high loss)")

        print(f"Dropped: {chan.dropped}, Duplicated: {chan.duplicated}, Corrupted: {chan.corrupted}")
        sender.close()
        receiver.close()
        chan.close()