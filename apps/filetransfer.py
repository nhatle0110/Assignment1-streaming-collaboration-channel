"""
apps.filetransfer  [Owner: TV2 - Minh Quoc]

Chunked file reading (iter_segments, driven lazily by the send window) and
offset-based file reassembly with SHA-256 verification (FileReceiver).
"""
import hashlib
import os

from streaprous_socket.wire import SEGMENT_SIZE


def file_info(path):
    # TODO (TV2): compute (size_bytes, sha256_hex) of path in streaming chunks
    raise NotImplementedError


def iter_segments(path, size):
    # TODO (TV2): yield (offset, chunk, fin) of at most SEGMENT_SIZE bytes (empty file -> one empty FIN)
    raise NotImplementedError


class FileReceiver:
    """Writes received segments at their offsets into a .part file and verifies SHA-256."""

    def __init__(self, file_id, filename, size, sha256, download_dir):
        # TODO (TV2): sanitize filename, create downloads/.parts/<file_id>.part, init received tracking
        raise NotImplementedError

    def on_data(self, offset, data, fin):
        # TODO (TV2): seek(offset) & write(data), update received bytes; return True when FIN + all bytes received
        raise NotImplementedError

    def finish(self):
        # TODO (TV2): close .part file, verify SHA-256, move to downloads/<filename> (or delete on mismatch)
        raise NotImplementedError

    def abort(self):
        # TODO (TV2): close and delete incomplete .part file
        raise NotImplementedError
