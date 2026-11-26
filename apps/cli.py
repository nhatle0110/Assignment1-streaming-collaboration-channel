"""
apps.cli  [Owner: TV1 - Le Minh Nhat]

Terminal client built on top of apps.agent.Agent.
"""
import argparse
import getpass
import sys
import threading

from streaprous_socket.udp_connection import discover_server

from .agent import Agent

HELP = """Commands:
  /broadcast <text>         message everyone
  /private <user> <text>    private message
  /users                    online users
  /send <user> <path>       offer a file
  /accept <id>              accept an incoming file (the first characters of the id are enough)
  /reject <id>              reject an incoming file
  /files                    list transfers
  /net                      RTT, resent share, congestion window
  /quit                     log out"""


class CliClient:
    """Converts Agent events to terminal lines and user commands to Agent calls."""

    def __init__(self, agent):
        # TODO (TV1): init state (me, users, transfers, net, auth_done, disconnected, _next)
        raise NotImplementedError

    def pump_events(self, timeout=0.5):
        # TODO (TV1): poll agent events and format non-empty output lines
        raise NotImplementedError

    def handle_event(self, ev):
        # TODO (TV1): format auth_ack, conn, user_list, presence, msg, file_incoming, file, error, net
        raise NotImplementedError

    def _file_line(self, ev):
        # TODO (TV1): format file transfer state / progress change
        raise NotImplementedError

    def run_command(self, line):
        # TODO (TV1): handle /broadcast, /private, /users, /send, /accept, /reject, /files, /net (timeout_ms), /quit
        raise NotImplementedError

    @staticmethod
    def _result(result):
        # TODO (TV1): return None if ok else "[error] <code>"
        raise NotImplementedError


def main():
    # TODO (TV1): parse args (--host, --port, --server-key, --username, --download-dir),
    #             read password (use getpass only when sys.stdin.isatty()), login, run printer + input loop
    raise NotImplementedError
