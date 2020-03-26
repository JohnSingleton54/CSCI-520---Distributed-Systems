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

import clientSocket
import fileServer
import connections


# The configurations for the two client servers.
configs = {
  0: {
    'playerColor':   'Red',
    'fileSharePort': 8080,
    'socketURL':     'localhost:8081',
    'raftNodeURL':   'localhost:8084',
  },
  1: {
    'playerColor':   'Blue',
    'fileSharePort': 8082,
    'socketURL':     'localhost:8083',
    'raftNodeURL':   'localhost:8085',
  },
}


# Setup the constant configurations for this server.
playerConfig  = configs[int(sys.argv[1])]
playerColor   = playerConfig['playerColor']
fileSharePort = playerConfig['fileSharePort']
socketURL     = playerConfig['socketURL']
raftNodeURL   = playerConfig['raftNodeURL']


# Global values
socket = None
noPunching = False


def resetGame():
  # TODO: Implement
  socket.send({
    'Type': 'Reset'
  })


def performPunch(hand, otherHand):
  # Check that the player can punch at this point. Perform a punch, log it, and check
  # for opponent blocking. Determine if the hit landed for a game over.
  global noPunching
  if noPunching:
    # Punches aren't allowed right now so don't allow it
    return
  #noPunching = True #TODO: Uncomment out
 
  # Tell client to show player punching.
  socket.send({
      'Type': 'PlayerChanged',
      hand: 'Punch',
  })

  # TODO: Implement



def performBlock(hand, otherHand):
  # Perform a block and log it.
  # TODO: Implement
  socket.send({
    'Type': 'PlayerChanged',
    hand: 'Block',
  })


def gameOver(youWin):
  # This tells the client the game is over and indicates
  # if "you" (meaning the color for this server) has one.
  socket.send({
    'Type':  'GameOver',
    'YouWin': youWin,
  })


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


def main():
  # Kicks off the file server thread, the Raft server threads,
  # and starts the main event loop to handle the socket.
  print('Use Ctrl+C to close server (Does not work unless webpage is open)')
  print('For testing open https://localhost:%d'%(fileSharePort))

  fs = fileServer.fileServer(fileSharePort, playerColor, socketURL)

  global socket
  socket = clientSocket.clientSocket(receivedClientMessage, socketURL)
  socket.startAndWait()

  # Socket closed so clean up and shut down
  fs.close()


if __name__ == "__main__":
  main()
