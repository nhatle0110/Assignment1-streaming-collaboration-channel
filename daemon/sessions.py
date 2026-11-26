"""
daemon.sessions  [Owner: TV4 - Member 4]

Server-side Session state and thread-safe SessionTable (max 256 sessions).
Cross-thread work is posted via session.post() to avoid cross-session locks.
"""
import queue
import secrets
import threading
import time

from streaprous_socket.reliable import ReliableConnection

MAX_SESSIONS = 256


class Session:
    def __init__(self, address, rc, keys, on_stream_data):
        # TODO (TV4): init address, rc, keys, streams={}, ReliableConnection with buffered_bytes callback,
        #             inbox Queue, timestamps, auth state
        raise NotImplementedError

    def post(self, work):
        # TODO (TV4): put callable or (header, body) into inbox if not closed
        raise NotImplementedError


class SessionTable:
    def __init__(self):
        # TODO (TV4): init lock and maps by connection_id, address, username
        raise NotImplementedError

    def add(self, session):
        # TODO (TV4): assign unique connection_id, enforce MAX_SESSIONS, replace old session on same address
        raise NotImplementedError

    def by_address(self, address):
        # TODO (TV4): lookup session by UDP (ip, port)
        raise NotImplementedError

    def lookup(self, connection_id, address):
        # TODO (TV4): lookup session by connection_id and verify matching address
        raise NotImplementedError

    def by_user(self, username):
        # TODO (TV4): lookup authenticated session by username
        raise NotImplementedError

    def all(self):
        # TODO (TV4): snapshot list of all sessions
        raise NotImplementedError

    def online(self):
        # TODO (TV4): snapshot list of authenticated sessions
        raise NotImplementedError

    def login(self, session, username):
        # TODO (TV4): mark session authenticated; return "ALREADY_ONLINE" if username is taken else None
        raise NotImplementedError

    def remove(self, session):
        # TODO (TV4): remove session once (return True if removed)
        raise NotImplementedError

    def _remove_locked(self, session):
        # TODO (TV4): internal cleanup while holding lock
        raise NotImplementedError
