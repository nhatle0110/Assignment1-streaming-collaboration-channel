"""
streaprous_socket.wire  [Owner: TV3 - Vo Minh Tri]

Packet format (15-byte header), DATA/ACK/JSON encoding, and per-stream
reassembly (MessageStream) to avoid head-of-line blocking (Kurose 3.8).
"""
import json
import struct
from enum import IntEnum

MAGIC = 0xC0DE
VERSION = 1
HEADER = struct.Struct("!HBBBIIH")
HEADER_SIZE = HEADER.size           # 15 bytes
MAX_DATAGRAM = 1200
SEGMENT_SIZE = 1000
NONCE_SIZE = 16
FIN = 0x01

CONTROL_STREAM = 0
CHAT_STREAM = 1
FIRST_FILE_STREAM = 2

HEARTBEAT_INTERVAL = 5.0
HEARTBEAT_TIMEOUT = 15.0
AUTH_DEADLINE = 10.0

MAX_MESSAGE = 64 * 1024
RCV_BUFFER = 64 * SEGMENT_SIZE      # RcvBuffer for flow control (Kurose 3.5.5)

_DATA = struct.Struct("!IQ")
_ACK = struct.Struct("!HIB")
_FRAME = struct.Struct("!I")


class PacketType(IntEnum):
    HELLO = 1
    HELLO_ACK = 2
    DATA = 3
    ACK = 4
    PING = 5
    PONG = 6
    CLOSE = 7
    DISCOVER = 8


class CloseReason(IntEnum):
    NORMAL = 0
    TIMEOUT = 1
    PROTOCOL_ERROR = 2
    SERVER_SHUTDOWN = 3


class PacketError(ValueError):
    """Invalid CCP datagram."""


class Header:
    def __init__(self, raw):
        # TODO (TV3): unpack 15-byte header into type, flags, connection_id, seq, raw
        raise NotImplementedError


def pack_header(ptype, flags, connection_id, seq, length):
    # TODO (TV3): pack MAGIC, VERSION, ptype, flags, connection_id, seq, length
    raise NotImplementedError


def unpack(datagram):
    # TODO (TV3): validate size, MAGIC, VERSION, length, ptype; return (Header, body)
    raise NotImplementedError


def is_file_stream(stream_id):
    # TODO (TV3): return True if stream_id >= FIRST_FILE_STREAM
    raise NotImplementedError


def encode_data(stream_id, offset, data):
    # TODO (TV3): pack stream_id(4) + offset(8) + data
    raise NotImplementedError


def decode_data(payload):
    # TODO (TV3): unpack (stream_id, offset, data)
    raise NotImplementedError


def encode_ack(rwnd, rcv_base, seqs):
    # TODO (TV3): pack rwnd(2) + rcv_base(4) + count(1) + seq(4)*count
    raise NotImplementedError


def decode_ack(payload):
    # TODO (TV3): unpack (rwnd, rcv_base, seqs)
    raise NotImplementedError


def encode_message(msg_type, payload, msg_id):
    # TODO (TV3): length-prefixed UTF-8 JSON frame {"type", "payload", "id"}
    raise NotImplementedError


def decode_message(frame):
    # TODO (TV3): parse UTF-8 JSON bytes into dict
    raise NotImplementedError


class MessageStream:
    """Per-stream byte reassembly & frame extraction (no head-of-line blocking)."""

    def __init__(self):
        # TODO (TV3): init _next, _early, buffered (bytes waiting in _early), _buffer
        raise NotImplementedError

    def feed(self, offset, data):
        # TODO (TV3): buffer out-of-order up to RCV_BUFFER, fill gaps, extract frames
        raise NotImplementedError

    def _append(self, data):
        # TODO (TV3): append in-order bytes to _buffer and advance _next
        raise NotImplementedError
