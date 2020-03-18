#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)
# due Apr 6, 2020 by 11:59 PM

# This file serves the client files and creates a socket to the client
# so that it can relay the game information into the Raft servers.

# References:
# - https://realpython.com/python-sockets/
# - https://websockets.readthedocs.io/en/stable/intro.html
# - https://python.readthedocs.io/en/stable/library/asyncio-task.html

import http.server
import socketserver
import threading
import asyncio
import websockets
import base64
import time

fileSharePort = 8080
clientSocketHost = 'localhost'
clientSocketPort = 8081

keepAlive = True
connectionMax = 0
receiveLock = threading.Lock()
sendLock = threading.Lock()
sendQueues = {}


def runFileServer():
  class ClientRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
      if self.path == '/':
        self.path = 'index.html'
      self.path = 'clientFiles/' + self.path
      return http.server.SimpleHTTPRequestHandler.do_GET(self)

  fileServer = socketserver.TCPServer(("", fileSharePort), ClientRequestHandler)
  while keepAlive:
    try:
      fileServer.timeout = 0.5 # in seconds
      fileServer.handle_request()
    except:
      continue


async def socketConnected(ws, path):
  # This method handles a connection from a talker and listens to it.
  global connectionMax
  connectionNum = connectionMax
  connectionMax += 1

  with sendLock:
    sendQueues[connectionNum] = []

  while keepAlive:
    try:
      # Send any pending messages
      with sendLock:
        for data in sendQueues[connectionNum]:
          await ws.send(data)
        sendQueues[connectionNum] = []

      # Listen for any replies
      data = await asyncio.wait_for(ws.recv(), timeout=1.0)
      if data:
        with receiveLock:
          receivedClientMessage(data)

    except asyncio.TimeoutError:
      continue

  # Close and cleanup socket
  with sendLock:
    del sendQueues[connectionNum]
  ws.close()


def receivedClientMessage(msg):
  print('received: "%s"' % (msg))


def sendToClients(msg):
  with sendLock:
    for connectionNum in sendQueues.keys():
      sendQueues[connectionNum].append(msg)


def startPinger():
  # TODO: REMOVE, this is just for testing the webpage can hear us.
  while keepAlive:
    sendToClients('ping')
    time.sleep(1.0)


def main():
  print('Use Ctrl+C to close server (Does not work unless webpage is open)')
  print('For testing open https://localhost:%d'%(fileSharePort))
  loop = asyncio.get_event_loop()
  try:
    threading.Thread(target=runFileServer).start()
    threading.Thread(target=startPinger).start()
    start_server = websockets.serve(socketConnected, clientSocketHost, clientSocketPort)
    loop.run_until_complete(start_server)
    loop.run_forever()
  except KeyboardInterrupt:
    pass
  finally:
    loop.stop()
    global keepAlive
    keepAlive = False


if __name__ == "__main__":
  main()
