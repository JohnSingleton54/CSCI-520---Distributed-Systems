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

import sys
import time

import clientSocket
import fileServer
import connections
import customTimer


# The configurations for the two client servers.
useMyHost = False
configs = {
  0: {
    'playerColor':   'Red',
    'fileSharePort': 8181,
    'socketURL':     'ec2-54-202-2-253.us-west-2.compute.amazonaws.com:8080',
    'raftNodeURL':   '35.155.81.205:8080',
  },
  1: {
    'playerColor':   'Blue',
    'fileSharePort': 8181,
    'socketURL':     'ec2-54-202-2-253.us-west-2.compute.amazonaws.com:8080',
    'raftNodeURL':   '54.244.147.5:8080',
  },
}


# Setup the constant configurations for this server.
playerConfig  = configs[int(sys.argv[1])]
playerColor   = playerConfig['playerColor']
fileSharePort = playerConfig['fileSharePort']
socketURL     = playerConfig['socketURL']
raftNodeURL   = playerConfig['raftNodeURL']


# Constant values
punchWait        = 1.0 # Is the amount of time, in seconds, to wait after a punch before player can punch again.
punchBlockedWait = 2.0 # Additional time, in seconds, over punch wait to wait after a punch was blocked


# Global values
socket = None
conn   = None
noPunching   = False
punchTimeout = None
punchCheckIn = time.time()


def resetGame():
  # This is called when a client has requested a reset or everything.
  conn.send({
    'Type': 'ResetGame'
  })


def gameHasBeenReset():
  # This is called when the raft servers have been reset.
  punchTimeout.stop()
  socket.send({
    'Type': 'GameReset'
  })
  print('Game Reset!')


def performPunch(hand, otherHand):
  # Check that the player can punch at this point. Perform a punch, log it, and check
  # for opponent blocking. Determine if the hit landed for a game over.
  global noPunching
  global punchCheckIn
  if noPunching:
    # Punches aren't allowed right now so don't allow it
    return

  # Perform a punch.
  noPunching = True
  punchCheckIn = time.time()
  punchTimeout.addTime(punchWait)
  socket.send({
    'Type':    'PlayerChanged',
    hand:      'Punch',
    otherHand: 'Neutral'
  })
  conn.send({
    'Type':  'ClientPunch',
    'Color': playerColor,
    'Hand':  hand
  })


def performBlock(hand, otherHand):
  # Perform a block and log it.
  socket.send({
    'Type':    'PlayerChanged',
    hand:      'Block',
    otherHand: 'Neutral'
  })
  conn.send({
    'Type':  'ClientBlock',
    'Color': playerColor,
    'Hand':  hand
  })


def hit(color):
  # This tells the client the game is over and indicates who got hit.
  socket.send({
    'Type':  'Hit',
    'Color': color
  })


def canPunchAgain():
  # The timeout for punching has ended. Allow a new punch.
  global noPunching
  global punchCheckIn
  noPunching = False
  print('Can punch again (%0.2fs)' % (time.time() - punchCheckIn))


def punchWasBlocked():
  # Adds 2 seconds for a total of 3 seconds for punch timeout.
  print('punch was blocked')
  punchTimeout.addTime(punchBlockedWait)


def opponentChanged(hand, condition):
  # Updates the shown condition of a opponent punching or blocking.
  otherHand = 'Left' if hand == 'Right' else 'Right'
  socket.send({
    'Type':    'OpponentChanged',
    hand:      condition,
    otherHand: 'Neutral'
  })


def clientSocketConnected():
  # Handles when the browser socket had connected.
  # Send the client connected message again to get client state.
  conn.send({
    'Type':  'ClientConnected',
    'Color': playerColor
  })


def receivedClientMessage(msg):
  # This method handles all messages from the client socket.
  if msg == 'ResetGame':
    resetGame()
  elif msg == 'LeftPunch':
    performPunch('Left', 'Right')
  elif msg == 'RightPunch':
    performPunch('Right', 'Left')
  elif msg == 'LeftBlock':
    performBlock('Left', 'Right')
  elif msg == 'RightBlock':
    performBlock('Right', 'Left')
  else:
    print('Unknown message from client:', msg)


def receivedRaftMessage(msg):
  # This method handles all messages from the raft server instance.
  msgType = msg['Type']
  if msgType == 'Hit':
    hit(msg['Color'])
  elif msgType == 'PunchBlocked':
    punchWasBlocked()
  elif msgType == 'OpponentChanged':
    opponentChanged(msg['Hand'], msg['Condition'])
  elif msgType == 'GameReset':
    gameHasBeenReset()
  else:
    print('Unknown message from raft:', msg)


def raftConnected():
  # Let the raft server instance this just connected
  # to know that this are a client connection.
  conn.send({
    'Type':  'ClientConnected',
    'Color': playerColor
  })


def main():
  global socket
  global conn
  global punchTimeout

  # Kicks off the file server thread, the Raft server threads,
  # and starts the main event loop to handle the socket.
  print('Use Ctrl+C to close server (Does not work unless webpage is open)')
  print('For testing open http://localhost:%d'%(fileSharePort))

  fs = fileServer.fileServer(fileSharePort, playerColor, socketURL)
  conn = connections.connection(raftConnected, receivedRaftMessage, raftNodeURL)
  punchTimeout = customTimer.customTimer(canPunchAgain)

  socket = clientSocket.clientSocket(clientSocketConnected, receivedClientMessage, socketURL, useMyHost)
  socket.startAndWait()

  # Socket closed so clean up and shut down
  print('Closing...')
  fs.close()
  conn.close()
  punchTimeout.close()


if __name__ == '__main__':
  main()
