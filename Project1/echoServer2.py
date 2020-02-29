#!/usr/bin/env python2

# From: https://docs.python.org/2/library/socket.html#example
# Echo server program
import socket

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 8080
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print('Connected by', addr)
while 1:
    data = conn.recv(1024)
    if not data: break
    conn.sendall(data)
conn.close()
