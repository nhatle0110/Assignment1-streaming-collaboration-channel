"""
daemon.users  [Owner: TV4 - Member 4]

User account store backed by db/users.json with salted PBKDF2-SHA256 hashes.
"""
import hashlib
import hmac
import json
import os
import re
import secrets

ITERATIONS = 100_000
USERNAME = re.compile(r"[a-z0-9_]{2,32}")


def _hash(password, salt):
    # TODO (TV4): hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    raise NotImplementedError


class UserStore:
    def __init__(self, path):
        # TODO (TV4): load JSON user table from path if present
        raise NotImplementedError

    def exists(self, username):
        # TODO (TV4): return True if username is in store
        raise NotImplementedError

    def verify(self, username, password):
        # TODO (TV4): constant-time verify PBKDF2 hash with stored salt
        raise NotImplementedError

    def add(self, username, password):
        # TODO (TV4): validate USERNAME, generate 16-byte salt, store hash (False if duplicate)
        raise NotImplementedError

    def save(self):
        # TODO (TV4): write user table to JSON file
        raise NotImplementedError
