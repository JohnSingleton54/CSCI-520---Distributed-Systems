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

import SimpleHTTPServer
import SocketServer
import threading
import socket
import base64

fileSharePort = 8080
clientSocketHost = 'localhost'
clientSocketPort = 8081

keepAlive = True
receiveLock = threading.Lock()
sendLock = threading.Lock()
sendQueues = {}


def runFileServer():
  class ClientRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
      if self.path == '/':
        self.path = 'index.html'
      self.path = 'clientFiles/' + self.path
      return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

  fileServer = SocketServer.TCPServer(("", fileSharePort), ClientRequestHandler)
  while keepAlive:
    try:
      fileServer.timeout = 0.5 # in seconds
      fileServer.handle_request()
    except:
      continue


def startClientSocket():
  # This method runs in a separete thread to listen for new connections.
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.bind((clientSocketHost, clientSocketPort))
  sock.listen(1)
  while keepAlive:
    try:
      sock.settimeout(1)
      conn, addr = sock.accept()
      thread = threading.Thread(target=socketConnected, args=(conn, addr))
      thread.start()
    except socket.timeout:
      continue
  sock.close()


def socketConnected(conn, addr):
  # This method handles a connection from a talker and listens to it.
  with sendLock:
    sendQueues[addr] = []
  #sendToClients("Hi from %s"%(str(addr)))
  conn.settimeout(1)
  while keepAlive:
    try:
      # Send any pending messages
      with sendLock:
        for data in sendQueues[addr]:
          conn.send(data)
        sendQueues[addr] = []
      # Listen for any replies
      data = conn.recv(4096)
      if data:
        with receiveLock:
          msg = base64.b64decode(data)
          receivedClientMessage(msg)
    except socket.timeout:
      continue
  # Close and cleanup socket
  with sendLock:
    del sendQueues[addr]
  conn.close()


def receivedClientMessage(msg):
  print('msg: "%s"'%(msg))


def sendToClients(msg):
  with sendLock:
    data = base64.b64encode(msg)
    for addr in sendQueues.keys():
      sendQueues[addr].append(data)


def main():
  threading.Thread(target=runFileServer).start()
  threading.Thread(target=startClientSocket).start()
  raw_input("Press Enter to continue...")
  global keepAlive
  keepAlive = False


if __name__ == "__main__":
  main()
