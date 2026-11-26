"""
streaprous_socket.reliable  [Shared by 4 members]

- TV1 (Le Minh Nhat): Reliability sender, RTT/TimeoutInterval (3.5.3), Karn, fast retransmit
- TV2 (Minh Quoc):    Congestion control - Slow Start & TCP CUBIC (3.7, RFC 8312)
- TV3 (Vo Minh Tri):  Reliability receiver, ACK, multi-stream scheduling (3.4.4, 3.8)
- TV4 (Member 4):     Flow control - rwnd from RcvBuffer & 3-window check (3.5.5)
"""
from collections import deque
from dataclasses import dataclass

from .wire import (FIN, RCV_BUFFER, SEGMENT_SIZE, PacketType, decode_ack,
                   decode_data, encode_ack, encode_data)

# ---- Constants ----
WINDOW = RCV_BUFFER // SEGMENT_SIZE     # TV4: N = 64 segments
MAX_RETRIES = 8                         # TV1
FAST_RETRANSMIT = 3                     # TV1: 3 later ACKs -> resend early
INITIAL_TIMEOUT = 1.0                   # TV1: TimeoutInterval initial (3.5.3)
MIN_TIMEOUT = 0.2                       # TV1
MAX_TIMEOUT = 4.0                       # TV1
CUBIC_C = 0.4                           # TV2: RFC 8312 (cited in Kurose p. 272)
CUBIC_BETA = 0.7                        # TV2: RFC 8312


# ---- TV1: Data structures ----

class ConnectionFailed(ConnectionError):
    """Raised when one packet exceeds MAX_RETRIES resends."""


@dataclass
class Outgoing:
    type: PacketType
    seq: int
    payload: bytes
    flags: int = 0


@dataclass(eq=False)
class Segment:
    seq: int
    stream_id: int
    offset: int
    data: bytes
    fin: bool
    sent_at: float = 0.0
    sent_order: int = 0
    retries: int = 0
    later_acks: int = 0


# ---- TV2: Congestion control (Slow Start + TCP CUBIC) ----

class Cubic:
    """Congestion window (cwnd) in packets."""

    def __init__(self):
        # TODO (TV2): init cwnd=1.0, ssthresh=WINDOW, w_max=WINDOW, epoch=None, k=0.0
        raise NotImplementedError

    def on_ack(self, now):
        # TODO (TV2): slow start (+1/ACK), then CUBIC W(t)=C*(t-K)^3+Wmax,
        #             cap <= 1.5*cwnd (RFC 9438), floor >= AIMD (+1/cwnd), cap <= WINDOW
        raise NotImplementedError

    def on_fast_retransmit(self, now):
        # TODO (TV2): w_max = cwnd; cwnd = ssthresh = max(2.0, cwnd * CUBIC_BETA); _start_curve(now)
        raise NotImplementedError

    def _start_curve(self, now):
        # TODO (TV2): epoch = now; k = (max(0.0, w_max - cwnd) / CUBIC_C) ** (1 / 3)
        raise NotImplementedError

    def on_timeout(self):
        # TODO (TV2): w_max = cwnd; ssthresh = max(2.0, cwnd * CUBIC_BETA); cwnd = 1.0; epoch = None
        raise NotImplementedError


# ---- Shared transport state machine ----

class ReliableConnection:
    """Selective Repeat + RTT/Timeout + Flow Control + CUBIC + Streams."""

    def __init__(self, on_stream_data, buffered_bytes):
        # TODO (TV1/TV2/TV3/TV4): init sender, cubic, RTT/timeout, queues/sources, receiver & rwnd_limit
        raise NotImplementedError

    # ---- TV3: Stream queues ----

    def send_stream(self, stream_id, data):
        # TODO (TV3): split data into SEGMENT_SIZE chunks and append to _queues[stream_id]
        raise NotImplementedError

    def enqueue_segment(self, stream_id, offset, data, fin):
        # TODO (TV3): append relayed file segment (offset, data, fin) to _queues[stream_id]
        raise NotImplementedError

    def cancel_stream(self, stream_id):
        # TODO (TV3): drop queued segments and file source for stream_id
        raise NotImplementedError

    def _next_segment(self):
        # TODO (TV3): pick next segment from lowest stream_id first (control -> chat -> files)
        raise NotImplementedError

    # ---- TV4: Flow control & lazy file source helpers ----

    def attach_source(self, stream_id, segments):
        # TODO (TV4): register file segment iterator read only when window is open
        raise NotImplementedError

    def queued_segments(self, stream_id):
        # TODO (TV4): number of segments queued on stream_id (used by server relay backlog)
        raise NotImplementedError

    def acked_bytes(self, stream_id):
        # TODO (TV4): total ACKed payload bytes on stream_id
        raise NotImplementedError

    def stream_pending(self, stream_id):
        # TODO (TV4): True if stream still has queued, unread, or in-flight segments
        raise NotImplementedError

    def receive_window(self):
        # TODO (TV4): free = (RCV_BUFFER - _buffered_bytes()) // SEGMENT_SIZE; clamp with rwnd_limit
        raise NotImplementedError

    def _window_open(self):
        # TODO (TV4): in_flight < max(1, min(int(cwnd), peer_rwnd)) and next_seq < send_base + WINDOW
        raise NotImplementedError

    # ---- TV3: Receiving DATA / dispatching ACK ----

    def on_packet(self, ptype, seq, flags, payload, now):
        # TODO (TV3): dispatch ACK to _on_ack; accept DATA in [rcv_base-WINDOW, rcv_base+WINDOW-1],
        #             ACK duplicates without redelivering, slide rcv_base, deliver to stream
        raise NotImplementedError

    # ---- TV1 (+ TV2 cwnd / TV4 peer_rwnd): Processing ACKs & RTT ----

    def _on_ack(self, rwnd, rcv_base, seqs, now):
        # TODO (TV4): update self.peer_rwnd = rwnd
        # TODO (TV1): remove ACKed segments from in_flight, Karn sample_rtt, _reset_timeout,
        #             increment later_acks and collect lost (>= FAST_RETRANSMIT)
        # TODO (TV2): call self.cubic.on_ack(now) and _congestion_event(lost, now, timeout=False)
        raise NotImplementedError

    def _sample_rtt(self, sample):
        # TODO (TV1): EstimatedRTT = 0.875*Est + 0.125*Sample; DevRTT = 0.75*Dev + 0.25*|Sample-Est|
        raise NotImplementedError

    def _reset_timeout(self):
        # TODO (TV1): TimeoutInterval = clamp(EstimatedRTT + 4*DevRTT, MIN_TIMEOUT, MAX_TIMEOUT)
        raise NotImplementedError

    # ---- TV2: Congestion event (cut once per loss burst) ----

    def _congestion_event(self, lost, now, timeout):
        # TODO (TV2): ignore if max(seq) < _recovery_seq; update _recovery_seq = next_seq;
        #             call cubic.on_timeout() or cubic.on_fast_retransmit(now)
        raise NotImplementedError

    # ---- Poll loop (TV1 resends, TV4 new data, TV3 ACKs) & transmit (TV1) ----

    def poll(self, now):
        # TODO (TV1): check expired -> double timeout, call _congestion_event(timeout=True), resend lost+expired
        # TODO (TV4): while _window_open(), pull _next_segment() and transmit
        # TODO (TV3): if _ack_due, emit ACK(receive_window(), rcv_base, sorted(_received))
        raise NotImplementedError

    def _transmit(self, segment, now):
        # TODO (TV1): stamp sent_at, sent_order, reset later_acks, return Outgoing(DATA)
        raise NotImplementedError
