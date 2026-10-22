# rto.py  (Owner: Vedant Bhatnagar)
# RTO = Retransmission TimeOut = how long we wait for an ACK before resending.
# Instead of a fixed number, we LEARN it from measured round-trip times (RTT).
#
# Jacobson/Karels:
#   srtt   = smoothed average RTT
#   rttvar = smoothed "how much RTT wobbles"
#   rto    = srtt + 4 * rttvar
# Karn's algorithm:
#   (a) never take an RTT sample from a packet that was retransmitted
#       (we can't tell which transmission the ACK belongs to)
#   (b) when a timeout happens, double the RTO (back off)


class RTOEstimator:
    ALPHA = 0.125           # weight of the new sample for srtt   (1/8)
    BETA = 0.25             # weight of the new sample for rttvar (1/4)
    MIN_RTO = 0.05          # never go below 50 ms
    MAX_RTO = 2.0           # never go above 2 s

    def __init__(self, initial_rto, adaptive=True):
        self.value = initial_rto        # the current RTO in seconds
        self.adaptive = adaptive        # if False, RTO stays fixed
        self.srtt = None
        self.rttvar = None

    def update(self, sample):
        # Called with a fresh RTT measurement (Karn rule (a) is enforced by the caller).
        if not self.adaptive:
            return
        if self.srtt is None:           # very first sample
            self.srtt = sample
            self.rttvar = sample / 2
        else:
            self.rttvar = (1 - self.BETA) * self.rttvar + self.BETA * abs(self.srtt - sample)
            self.srtt = (1 - self.ALPHA) * self.srtt + self.ALPHA * sample
        rto = self.srtt + 4 * self.rttvar
        self.value = min(max(rto, self.MIN_RTO), self.MAX_RTO)

    def backoff(self):
        # Karn rule (b): a timeout happened, so wait longer next time.
        if not self.adaptive:
            return
        self.value = min(self.value * 2, self.MAX_RTO)
