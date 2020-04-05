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


  def __init__(self, onConnect, handleMethod, socketURL, useMyHost):
    self.__onConnect    = onConnect
    self.__handleMethod = handleMethod
    self.__socketURL    = socketURL
    self.__useMyHost    = useMyHost

    self.__keepAlive   = True
    self.__connNumMax  = 0
    self.__receiveLock = threading.Lock()
    self.__sendLock    = threading.Lock()
    self.__sendQueues  = {}


  async def __socketConnected(self, ws, path):
    # When a new socket connection from the client browser,
    # this method is called to handle it in an asynchronous loop.
    connectionNum = self.__connNumMax
    self.__connNumMax += 1

    with self.__sendLock:
      self.__sendQueues[connectionNum] = []

    with self.__receiveLock:
      self.__onConnect()

    # Loop until the client closes or the server is shutting down.
    while self.__keepAlive:
      try:
        # Send any pending messages
        with self.__sendLock:
          for data in self.__sendQueues[connectionNum]:
            await ws.send(data)
          self.__sendQueues[connectionNum] = []

        # Listen for any replies
        data = await asyncio.wait_for(ws.recv(), timeout=socketTimeout)
        if data:
          with self.__receiveLock:
            self.__handleMethod(data)

      except asyncio.TimeoutError:
        continue
      except websockets.ConnectionClosedOK:
        break

    # Close and cleanup socket
    with self.__sendLock:
      del self.__sendQueues[connectionNum]
    await ws.close()


  def send(self, msg):
    # This will broadcast this message to all clients via the socket connection.
    with self.__sendLock:
      data = json.dumps(msg)
      for connectionNum in self.__sendQueues.keys():
        self.__sendQueues[connectionNum].append(data)


  def startAndWait(self):
    # This method starts the socket event loop and waits until an interrupt kills it.
    loop  = asyncio.get_event_loop()
    parts = self.__socketURL.split(':')
    host  = parts[0] if self.__useMyHost else ''
    port  = int(parts[1])

    try:
      start_server = websockets.serve(self.__socketConnected, host, port)
      loop.run_until_complete(start_server)
      loop.run_forever()
    except KeyboardInterrupt:
      pass
    finally:
      self.__keepAlive = False
      loop.stop()
