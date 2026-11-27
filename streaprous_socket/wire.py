"""
streaprous_socket.wire  [Owner: TV3 - Vo Minh Tri]

Everything CCP (CollabNet Channel Protocol) puts on the wire. All numbers are big-endian.

    header      magic(2) version(1) type(1) flags(1) connection_id(4) seq(4) length(2)
    HELLO       Rc(16) || RSA-OAEP(server public key, master secret)(256)     not encrypted
    HELLO_ACK   Rs(16) || HMAC-SHA256(Ms, "server finished" || Rc || Rs)(32)  not encrypted
    DATA        stream_id(4) offset(8) data(<= 1000)                          encrypted
    ACK         rwnd(2) rcv_base(4) count(1) seq(4) x count                    encrypted
    PING, PONG  empty                                                          encrypted
    CLOSE       reason(1)                                                      encrypted
    DISCOVER    empty; the server answers with the same 15 bytes              not encrypted

`seq` is the DATA sequence number (0 in every other packet). The FIN flag marks
the last segment of a file (End-of-Message). Streams 0 and 1 carry JSON
messages, each framed as length(4) || UTF-8 JSON.
"""
import json
import struct
from enum import IntEnum

MAGIC = 0xC0DE
VERSION = 1
HEADER = struct.Struct("!HBBBIIH")
HEADER_SIZE = HEADER.size          # 15
MAX_DATAGRAM = 1200                # far below a 1500-byte Ethernet MTU: no IP fragmentation
SEGMENT_SIZE = 1000                # stream bytes per DATA packet
NONCE_SIZE = 16                    # Rc, Rs
FIN = 0x01                         # flags: last segment of a file

CONTROL_STREAM = 0                 # login, user list, presence, errors, file negotiation
CHAT_STREAM = 1                    # MSG / MSG_DELIVER
FIRST_FILE_STREAM = 2              # one stream per accepted file transfer from here on

HEARTBEAT_INTERVAL = 5.0           # send PING after this long without sending
HEARTBEAT_TIMEOUT = 15.0           # peer is dead after this long without receiving
AUTH_DEADLINE = 10.0               # time allowed between HELLO and a successful login

MAX_MESSAGE = 64 * 1024            # largest JSON message
RCV_BUFFER = 64 * SEGMENT_SIZE     # RcvBuffer: bytes a connection keeps waiting for a gap (3.5.5)

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
    """A datagram that is not CCP; the receiver drops it."""


class Header:
    def __init__(self, raw):
        _, _, ptype, self.flags, self.connection_id, self.seq, _ = HEADER.unpack(raw)
        self.type = PacketType(ptype)
        self.raw = raw                         # authenticated by the packet MAC


def pack_header(ptype, flags, connection_id, seq, length):
    return HEADER.pack(MAGIC, VERSION, ptype, flags, connection_id, seq, length)


def unpack(datagram):
    """Split a datagram into (Header, body). PacketError if it is not a CCP packet."""
    if not HEADER_SIZE <= len(datagram) <= MAX_DATAGRAM:
        raise PacketError("bad size")
    magic, version, ptype, _, _, _, length = HEADER.unpack_from(datagram)
    if magic != MAGIC or version != VERSION or length != len(datagram) - HEADER_SIZE \
            or ptype not in PacketType._value2member_map_:
        raise PacketError("not a CCP packet")
    return Header(datagram[:HEADER_SIZE]), datagram[HEADER_SIZE:]


def is_file_stream(stream_id):
    return stream_id >= FIRST_FILE_STREAM


# ---- DATA / ACK payloads (inside encrypted packets, so already authenticated) ----

def encode_data(stream_id, offset, data):
    return _DATA.pack(stream_id, offset) + data


def decode_data(payload):
    stream_id, offset = _DATA.unpack_from(payload)
    return stream_id, offset, payload[_DATA.size:]


def encode_ack(rwnd, rcv_base, seqs):
    """seqs: the packets received above rcv_base (at most the window, 64)."""
    return _ACK.pack(rwnd, rcv_base, len(seqs)) + struct.pack(f"!{len(seqs)}I", *seqs)


def decode_ack(payload):
    rwnd, rcv_base, count = _ACK.unpack_from(payload)
    return rwnd, rcv_base, struct.unpack_from(f"!{count}I", payload, _ACK.size)


# ---- JSON messages on streams 0 and 1 ----

def encode_message(msg_type, payload, msg_id):
    """One frame: length(4) || {"type", "payload", "id"} as UTF-8 JSON."""
    body = json.dumps({"type": msg_type, "payload": payload, "id": msg_id},
                      ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _FRAME.pack(len(body)) + body


def decode_message(frame):
    return json.loads(frame.decode("utf-8"))


class MessageStream:
    """Receive side of stream 0 or 1: put segments back in offset order and cut frames.

    Every stream has its own MessageStream, so a missing chat segment never holds
    back the control stream or a file (no head-of-line blocking between streams).
    """

    def __init__(self):
        self._next = 0          # offset of the next byte we need
        self._early = {}        # offset -> data, segments that arrived after a gap
        self.buffered = 0       # bytes in _early: what this stream takes from RCV_BUFFER
        self._buffer = bytearray()

    def feed(self, offset, data):
        """Add a segment; return the complete frame bodies. PacketError on a bad frame."""
        if offset > self._next:
            # A sender that respects rwnd never fills the buffer; beyond it, drop.
            if offset not in self._early and self.buffered + len(data) <= RCV_BUFFER:
                self._early[offset] = data
                self.buffered += len(data)
            return []
        self._append(data[self._next - offset:])
        while self._next in self._early:
            data = self._early.pop(self._next)
            self.buffered -= len(data)
            self._append(data)

        frames = []
        while len(self._buffer) >= _FRAME.size:
            (length,) = _FRAME.unpack_from(self._buffer)
            if not 0 < length <= MAX_MESSAGE:
                raise PacketError(f"bad frame length {length}")
            if len(self._buffer) < _FRAME.size + length:
                break
            frames.append(bytes(self._buffer[_FRAME.size:_FRAME.size + length]))
            del self._buffer[:_FRAME.size + length]
        return frames

    def _append(self, data):
        self._buffer += data
        self._next += len(data)
