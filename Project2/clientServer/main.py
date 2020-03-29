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
configs = {
  0: {
    'playerColor':   'Red',
    'fileSharePort': 8080,
    'socketURL':     'localhost:49506',
    'raftNodeURL':   'localhost:49507',
  },
  1: {
    'playerColor':   'Blue',
    'fileSharePort': 49508,
    'socketURL':     'localhost:49509',
    'raftNodeURL':   'localhost:49510',
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
    'Type': 'Reset'
  })


def gameHasBeenReset():
  # This is called when the raft servers have been reset.
  punchTimeout.stop()
  socket.send({
    'Type': 'Reset'
  })
  print('Reset!')



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


def gameOver(color):
  # This tells the client the game is over and indicates
  # if "you" (meaning the color for this server) has one.
  youWin = color == playerColor
  socket.send({
    'Type':   'GameOver',
    'YouWin': youWin
  })


def canPunchAgain():
  # The timeout for punching has ended. Allow a new punch.
  global noPunching
  global punchCheckIn
  noPunching = False
  print("Can punch again (%0.2fs)" % (time.time() - punchCheckIn))


def punchWasBlocked(color):
  # Adds 2 seconds for a total of 3 seconds for punch timeout.
  print("$s's punch was blocked"%(color))
  if color == playerColor:
    punchTimeout.addTime(punchBlockedWait)


def receivedClientMessage(msg):
  # This method handles all messages from the client socket.
  if msg == 'Reset':
    resetGame()
  elif msg == 'LeftPunch':
    performPunch('Left', 'Right')
  elif msg == 'RightPunch':
    performPunch('Right', 'Left')
  elif msg == 'LeftBlock':
    performBlock('Left', 'Right')
  elif msg == 'RightBlock':
    performBlock('Right', 'Left')
  elif msg == 'TestWin':
    gameOver(True)
  elif msg == 'TestLose':
    gameOver(False)
  else:
    print("Unknown message (1):")
    print(msg)


def receivedRaftMessage(msg):
  # This method handles all messages from the raft server instance.
  msgType = msg['Type']
  if msgType == 'GameOver':
    gameOver(msg['Color'])
  elif msgType == 'PunchBlocked':
    punchWasBlocked(msg['Color'])
  elif msgType == 'GameReset':
    gameHasBeenReset()
  else:
    print("Unknown message (2):")
    print(msg)


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

  socket = clientSocket.clientSocket(receivedClientMessage, socketURL)
  socket.startAndWait()

  # Socket closed so clean up and shut down
  print('Closing...')
  fs.close()
  conn.close()
  punchTimeout.close()


if __name__ == "__main__":
  main()
