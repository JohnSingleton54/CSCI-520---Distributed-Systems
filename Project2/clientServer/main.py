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


# TODO: Needs to be set these from command line arguments
playerColor      = 'Blue'
fileSharePort    = 8080
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
        self.path = 'clientFiles/index.html'
      elif self.path == '/config.json':
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


def sendToClients(msg):
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
  print('Use Ctrl+C to close server (Does not work unless webpage is open)')
  print('For testing open https://localhost:%d'%(fileSharePort))
  loop = asyncio.get_event_loop()
  try:
    threading.Thread(target=runFileServer).start()
    # TODO: Start any other game update threads here as needed

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
