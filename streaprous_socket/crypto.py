"""
streaprous_socket.crypto  [Owner: TV4 - Member 4]

t-tls style security (Kurose ch. 8): RSA-2048 OAEP key exchange, 4 derived
session keys (Kc, Ks, Mc, Ms), AES-256-CBC + HMAC-SHA256, replay protection.
"""
import hashlib
import hmac
import os
import secrets
import struct
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import MGF1, OAEP
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .wire import NONCE_SIZE, Header, pack_header

MASTER_SECRET_SIZE = 32
RSA_BITS = 2048
IV_SIZE = 16
MAC_SIZE = 32
HELLO_SIZE = NONCE_SIZE + RSA_BITS // 8
HELLO_ACK_SIZE = NONCE_SIZE + MAC_SIZE
_OAEP = OAEP(mgf=MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


class CryptoError(Exception):
    """Bad MAC, invalid padding, or replayed packet."""


def create_server_key(private_path, public_path):
    # TODO (TV4): generate RSA-2048 key pair and save PEM files
    raise NotImplementedError


def load_private_key(path):
    # TODO (TV4): load PEM private key
    raise NotImplementedError


def load_public_key(path):
    # TODO (TV4): load PEM public key
    raise NotImplementedError


def new_master_secret(public_key):
    # TODO (TV4): generate 32-byte MS and encrypt with server public_key (OAEP); return (ms, enc)
    raise NotImplementedError


def open_master_secret(private_key, encrypted):
    # TODO (TV4): decrypt MS with server private_key (OAEP)
    raise NotImplementedError


@dataclass
class SessionKeys:
    send_key: bytes
    send_mac: bytes
    recv_key: bytes
    recv_mac: bytes
    server_mac: bytes
    send_counter: int = 0
    recv_counter: int = 0


def derive_keys(master, rc, rs, is_server):
    # TODO (TV4): KDF using HMAC-SHA256(master, label || rc || rs) -> Kc, Ks, Mc, Ms
    raise NotImplementedError


def finished_tag(keys, rc, rs):
    # TODO (TV4): HMAC-SHA256(keys.server_mac, b"server finished" + rc + rs)
    raise NotImplementedError


def seal(keys, ptype, flags, connection_id, seq, payload):
    # TODO (TV4): increment send_counter, AES-256-CBC encrypt (counter || payload),
    #             pack header, append HMAC-SHA256 over (header || iv || ciphertext)
    raise NotImplementedError


def unseal(keys, header: Header, body):
    # TODO (TV4): verify HMAC (constant-time), decrypt AES-CBC, reject counter <= recv_counter
    raise NotImplementedError
