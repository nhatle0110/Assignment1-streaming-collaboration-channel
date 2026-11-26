#!/usr/bin/env python3
"""
start_chatapp  [Owner: TV1 - Le Minh Nhat]

Entry point for the browser Web Agent (Linux + root, non-loopback LAN IP):
    sudo .venv/bin/python start_chatapp.py --http-ip <LAN_IP> --http-port 8080 \\
        --server <SERVER_IP>:9000 --server-key cert/server_public.pem
"""
import argparse

from apps import create_chatapp
from apps.agent import Agent
from start_backend import setup_rst_block
from streaprous_socket.udp_connection import discover_server

SERVER_PORT = 9000


def main():
    # TODO (TV1): parse --http-ip, --http-port, --server, --server-key, --download-dir;
    #             create Agent, call setup_rst_block(http_ip, http_port), start create_chatapp(...)
    raise NotImplementedError


if __name__ == "__main__":
    main()
