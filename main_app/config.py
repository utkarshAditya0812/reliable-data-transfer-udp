# config.py  - shared default settings
HOST = "127.0.0.1"          # everything runs on this computer
PAYLOAD_SIZE = 1024         # file bytes carried in each packet
DEFAULT_TIMEOUT = 0.1       # seconds to wait for an ACK before resending
DEFAULT_WINDOW = 8          # window size for GBN and SR
LINGER = 1.0                # receiver waits this long after FIN (in case last ACK was lost)
DEFAULT_DELAY = 0.01        # one-way network delay (10 ms)
DEFAULT_JITTER = 0.0        # extra random delay (0 = off, so reordering only happens when we ask for it)
