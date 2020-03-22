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

import http.server
import socketserver
import threading
import asyncio
import websockets
import base64
import time
import json
import sys

import connections


# The configurations for the two client servers.
configs = {
  0: {
    'playerColor':      'Red',
    'fileSharePort':    8080,
    'clientSocketHost': 'localhost',
    'clientSocketPort': 8081,
  },
  1: {
    'playerColor':      'Blue',
    'fileSharePort':    8082,
    'clientSocketHost': 'localhost',
    'clientSocketPort': 8083,
  },
}


# List all the raft servers
raftServerHostsAndPorts = [
  "localhost:8084",
  "localhost:8085",
  "localhost:8086",
  "localhost:8087",
  "localhost:8088",
]


# Setup the constant configurations for this server.
playerConfig     = configs[int(sys.argv[1])]
playerColor      = playerConfig['playerColor']
fileSharePort    = playerConfig['fileSharePort']
clientSocketHost = playerConfig['clientSocketHost']
clientSocketPort = playerConfig['clientSocketPort']


# Setup global constants
fileServerTimeout = 0.5 # in seconds
socketTimeout = 0.5 # in seconds


# Setup global game state variables
keepAlive = True
connectionMax = 0
receiveLock = threading.Lock()
sendLock = threading.Lock()
sendQueues = {}


def runFileServer():
  # This serves the files (html, javascript, css, png, ico, and json) needed for the browser pages.
  class ClientRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
      if self.path == '/':
        # Make the default URL run index.html
        self.path = 'clientFiles/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

      elif self.path == '/config.json':
        # Construct and serve a json config file. This file provides all the information
        # the client will need to configure itself and create a socket back to this server.
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        data = json.dumps({
          'PlayerColor': playerColor,
          'SocketHost': clientSocketHost,
          'SocketPort': clientSocketPort,
        })
        self.wfile.write(bytes(data, "utf8"))
        return

      else:
        # For all other files, fetch and serve those files.
        # The files are in their own folder so that no one can ask there server to server
        # this (main.py) file (not like it really matters here since we don't have any private in it).
        self.path = 'clientFiles/' + self.path
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

  fileServer = socketserver.TCPServer(("", fileSharePort), ClientRequestHandler)
  while keepAlive:
    try:
      fileServer.timeout = fileServerTimeout
      fileServer.handle_request()
    except:
      continue


async def socketConnected(ws, path):
  # This method handles a socket connection from the actual clients running on the browser.
  # This will both listen and send through the same socket.
  # This doesn't differentiate the clients connected to this server since the requirements
  # for the project has one server per player so we simply act like there is only one client.
  # However to handle refreshes and multiple connections this uses a unique connection number
  # to differentiate between the different sockets.
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
      data = await asyncio.wait_for(ws.recv(), timeout=socketTimeout)
      if data:
        with receiveLock:
          receivedClientMessage(data)

    except asyncio.TimeoutError:
      continue

  # Close and cleanup socket
  with sendLock:
    del sendQueues[connectionNum]
  ws.close()


def sendToClients(msg):
  # This will broadcast this message to all clients via the socket connection.
  with sendLock:
    data = json.dumps(msg)
    for connectionNum in sendQueues.keys():
      sendQueues[connectionNum].append(data)


def indicateReady():
  # Let the other client server know we are ready so that we can get past
  # the "Wait" state. If other has already said it is ready then send the
  # "Fight" message. This is also used to reset after a game over.
  # TODO: Implement
  return


def performPunch(right):
  # Check that the player can punch at this point. Perform a punch, log it, and check
  # for opponent blocking. Determine if the hit landed for a game over.
  # TODO: Implement
  sendToClients({
    'Type': 'PlayerChanged',
    'Hand': 'Left' if right else 'Right',
    'Condition': 'Punch',
  })


def performBlock(right):
  # Perform a block and log it.
  # TODO: Implement
  sendToClients({
    'Type': 'PlayerChanged',
    'Hand': 'Left' if right else 'Right',
    'Condition': 'Block',
  })


def receivedClientMessage(msg):
  # This method handles all messages from the client socket.
  if msg == 'Ready':
    indicateReady()
  elif msg == 'LeftPunch':
    performPunch(True)
  elif msg == 'RightPunch':
    performPunch(False)
  elif msg == 'LeftBlock':
    performBlock(True)
  elif msg == 'RightBlock':
    performBlock(False)
  elif msg == 'TestWin':
    sendToClients({
      'Type': 'GameOver',
      'YouWin': True
    })
  elif msg == 'TestLose':
    sendToClients({
      'Type': 'GameOver',
      'YouWin': False
    })
  elif msg == 'TestNoWait':
    sendToClients({
      'Type': 'Fight'
    })


def main():
  # Kicks off the file server thread, the Raft server threads,
  # and starts the main event loop to handle the socket.
  print('Use Ctrl+C to close server (Does not work unless webpage is open)')
  print('For testing open https://localhost:%d'%(fileSharePort))
  loop = asyncio.get_event_loop()
  try:
    threading.Thread(target=runFileServer).start()

    # TODO: Start any other game update threads here as needed
    #senders = []
    #for hostAndPort in raftServerHostsAndPorts:
    #  sender = connections.sender(hostAndPort)
    #  senders.append(sender)

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
