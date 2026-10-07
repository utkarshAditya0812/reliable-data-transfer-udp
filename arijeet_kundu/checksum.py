# checksum.py  (Owner: Arijeet Kundu)
# A checksum is a small number computed from the data.
# If even one byte changes on the way, the number changes -> we detect corruption.


def calculate_checksum(data):
    total = 0                    # running sum starts at zero
    for byte in data:            # go through every byte of the data
        total += byte            # add the byte's value (0-255) to the sum
    return total % 65536         # keep only 16 bits so it fits in 2 bytes


def verify_checksum(data, received_checksum):
    # Recompute the checksum and compare with the one that came with the packet.
    return calculate_checksum(data) == received_checksum
