#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)
# due Apr 6, 2020 by 11:59 PM

# This serves the client files and creates a socket to the client
# so that it can relay the game information into the Raft servers.

# References:
# - https://realpython.com/python-sockets/
# - https://websockets.readthedocs.io/en/stable/intro.html
# - https://python.readthedocs.io/en/stable/library/asyncio-task.html
# - https://docs.python.org/3/library/json.html
# - https://stackabuse.com/serving-files-with-pythons-simplehttpserver-module/

import asyncio
import threading
import websockets
import time
import json
import sys


socketTimeout = 0.5 # in seconds


class clientSocket:
  # This method handles a socket connection from the actual clients running on the browser.
  # This will both listen and send through the same socket.
  #
  # This doesn't differentiate the clients connected to this server since the requirements
  # for the project has one server per player so we simply act like there is only one client.
  # However to handle refreshes and multiple connections this uses a unique connection number
  # to differentiate between the different sockets.


  def __init__(self, handleMethod, socketURL):
    self.handleMethod = handleMethod
    self.socketURL    = socketURL

    self.keepAlive   = True
    self.connNumMax  = 0
    self.receiveLock = threading.Lock()
    self.sendLock    = threading.Lock()
    self.sendQueues  = {}


  async def socketConnected(self, ws, path):
    # When a new socket connection from the client browser,
    # this method is called to handle it in an asynchronous loop.
    self.connNumMax
    connectionNum = self.connNumMax
    self.connNumMax += 1

    with self.sendLock:
      self.sendQueues[connectionNum] = []

    # Loop until the client closes or the server is shutting down.
    while self.keepAlive:
      try:
        # Send any pending messages
        with self.sendLock:
          for data in self.sendQueues[connectionNum]:
            await ws.send(data)
          self.sendQueues[connectionNum] = []

        # Listen for any replies
        data = await asyncio.wait_for(ws.recv(), timeout=socketTimeout)
        if data:
          with self.receiveLock:
            self.handleMethod(data)

      except asyncio.TimeoutError:
        continue
      except websockets.ConnectionClosedOK:
        break

    # Close and cleanup socket
    with self.sendLock:
      del self.sendQueues[connectionNum]
    await ws.close()


  def send(self, msg):
    # This will broadcast this message to all clients via the socket connection.
    with self.sendLock:
      data = json.dumps(msg)
      for connectionNum in self.sendQueues.keys():
        self.sendQueues[connectionNum].append(data)


  def startAndWait(self):
    # This method starts the socket event loop and waits until an interrupt kills it.
    loop  = asyncio.get_event_loop()
    parts = self.socketURL.split(':')
    host  = parts[0]
    port  = int(parts[1])

    try:
      start_server = websockets.serve(self.socketConnected, host, port)
      loop.run_until_complete(start_server)
      loop.run_forever()
    except KeyboardInterrupt:
      pass
    finally:
      loop.stop()
