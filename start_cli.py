#!/usr/bin/env python3
"""
start_cli  [Owner: TV1 - Le Minh Nhat]

Entry point for the CollabNet terminal client:
    python start_cli.py --host <ip> --server-key cert/server_public.pem --username alice
"""
import sys

from apps.cli import main

if __name__ == "__main__":
    sys.exit(main())
