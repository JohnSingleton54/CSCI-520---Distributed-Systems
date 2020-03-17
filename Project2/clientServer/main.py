#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)
# due Apr 6, 2020 by 11:59 PM

# This file serves the client files and creates a socket to the client
# so that it can relay the game information into the Raft servers.

# References:
# - https://realpython.com/python-sockets/
# - https://docs.python.org/2/library/socketserver.html

import http.server
import socketserver
import threading

PORT = 8080
keepAlive = True

def runFileServer():
    class ClientRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            print(self.path)
            if self.path == '/':
                self.path = 'index.html'
            self.path = 'clientFiles/' + self.path
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    fileServer = socketserver.TCPServer(("", PORT), ClientRequestHandler)
    while keepAlive:
        try:
            fileServer.timeout = 0.5 # in seconds
            fileServer.handle_request()
        except:
            pass

threading.Thread(target=runFileServer).start()
raw_input("Press Enter to continue...")
keepAlive = False
