#!/usr/bin/env python2

# From: https://docs.python.org/2/library/socket.html#example 
# Echo client program
import socket

HOST = '35.XXX.XXX.214'    # The remote host
PORT = 8080              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.sendall('Hello, world')
data = s.recv(1024)
s.close()
print ('Received', repr(data))
