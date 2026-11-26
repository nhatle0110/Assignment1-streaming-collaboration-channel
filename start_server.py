#!/usr/bin/env python3
"""
start_server  [Owner: TV3 - Vo Minh Tri]

Entry point for the central CollabNet CCP/UDP server:
    python start_server.py --port 9000
"""
from daemon.ccpserver import main

if __name__ == "__main__":
    main()
