#!/usr/bin/env python3

import socket
import time

# From: https://realpython.com/python-sockets/

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hello, world')
    print('Sent')
    time.sleep(5)
    data = s.recv(1024)
    print('Received', repr(data))
    time.sleep(5)
