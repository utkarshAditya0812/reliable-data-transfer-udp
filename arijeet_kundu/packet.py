# packet.py  (Owner: Arijeet Kundu)
# Defines the packet format, sequence numbers, and a safe "receive one packet" helper.
#
# Packet layout (7 byte header + payload):
#   [ type 1 byte ][ sequence number 4 bytes ][ checksum 2 bytes ][ payload ... ]

import socket
import struct
import time
from checksum import calculate_checksum, verify_checksum

DATA = 1                   # packet carries a piece of the file
ACK = 2                    # packet is an acknowledgement
FIN = 3                    # packet says "this was the last one"

HEADER_FORMAT = "!BIH"     # ! = network byte order, B = 1 byte, I = 4 bytes, H = 2 bytes
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)   # = 7
BUFFER_SIZE = 4096         # max bytes we read from the socket at once
GIVE_UP_SECONDS = 20       # if nothing useful happens for this long, stop with an error


def make_packet(packet_type, seq, payload=b""):
    # The checksum covers type + sequence number + payload.
    body = struct.pack("!BI", packet_type, seq) + payload
    checksum = calculate_checksum(body)
    header = struct.pack(HEADER_FORMAT, packet_type, seq, checksum)
    return header + payload


def parse_packet(raw):
    # Returns (type, seq, payload) if the packet is good, or None if it is damaged.
    if len(raw) < HEADER_SIZE:                      # too short to even hold a header
        return None
    packet_type, seq, checksum = struct.unpack(HEADER_FORMAT, raw[:HEADER_SIZE])
    payload = raw[HEADER_SIZE:]
    body = struct.pack("!BI", packet_type, seq) + payload
    if not verify_checksum(body, checksum):         # data was corrupted -> throw away
        return None
    return packet_type, seq, payload


def receive_packet(sock, timeout):
    # Wait up to `timeout` seconds for ONE good packet.
    # Returns (type, seq, payload), or None if time ran out.
    # Corrupted packets are silently discarded (they count as "lost").
    deadline = time.time() + timeout
    while True:
        remaining = deadline - time.time()          # how much waiting time is left
        if remaining <= 0:
            return None
        sock.settimeout(remaining)
        try:
            raw, _ = sock.recvfrom(BUFFER_SIZE)
        except socket.timeout:                      # nothing arrived in time
            return None
        except ConnectionResetError:                # Windows quirk, just ignore it
            continue
        parsed = parse_packet(raw)
        if parsed is not None:                      # good packet -> give it back
            return parsed
