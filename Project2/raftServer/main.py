#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)
# due Apr 6, 2020 by 11:59 PM


import sys
import json
import random

import connections
import customTimer


# The configurations for the raft servers.
useMyHost = True
nodeIdToURL = {
  0: 'localhost:49507',
  1: 'localhost:49510',
  2: 'localhost:49511',
  3: 'localhost:49512',
  4: 'localhost:49513',
}


myNodeId = int(sys.argv[1])
print("My Node Id is %d" % (myNodeId))

nodeCount = int(sys.argv[2])
print("The Node Count is %d" % (nodeCount))


# Constant values
beatLowerBound = 1.0 # Lowest random time, in seconds, to add to timeout on heart beat
beatUpperBound = 3.0 # Highest random time, in seconds, to add to timeout on heart beat


# Global variables
clients  = {}
listener = None
senders  = {}
currentLeader = -1
leaderTimeout = None


def clientConnected(color, conn):
  # Indicates a client has been connected to this raft instance.
  global clients
  clients[color] = conn
  print('%s client connected'%(color))


def resetEverything():
  # The client has asked to reset the game.
  # So reset variables
  #
  # TODO: Implement
  #
  print('Reset!')


def clientPunch(color, hand):
  # Client has punched
  #
  # TODO: Implement
  #
  print('%s punched with %s hand'%(color, hand))


def clientBlock(color, hand):
  # Client has blocked
  #
  # TODO: Implement
  #
  print('%s blocking with %s hand' % (color, hand))


def leaderHasTimedOut():
  # The timeout for starting a new election has been reached.
  # Start a new leader election
  #
  # TODO: Implement
  #
  print('Start election')


def heartBeat():
  # Received a heart beat from the leader so bump the timeout
  # to keep a new leader election from being kicked off.
  dt = random.Random() * (beatLowerBound - beatUpperBound) + beatLowerBound
  leaderTimeout.addTime(dt)


def requestVoteRequest(fromNodeID, termNum):
  # This handles a RequestVote Request from another raft instance.
  #
  # TODO: Implement
  #
  pass


def requestVoteReply(fromNodeID, termNum, granted):
  # This handles a RequestVote Reply from another raft instance.
  #
  # TODO: Implement
  #
  pass


def appendEntriesRequest(fromNodeID, termNum, entries):
  # This handles a AppendEntries Request from the leader.
  # If entries is empty then this is only for a heartbeat.
  # Check that the node it is from is the current leader, otherwise ignore.
  if fromNodeID == currentLeader:
    heartBeat()
    if entries:
      # Apply the entries
      #
      # TODO: Implement
      #
      pass


def appendEntriesReply(fromNodeID, termNum, success):
  # This handles a AppendEntries Reply from another raft instance.
  #
  # TODO: Implement
  #
  pass


def tellClientPunchBlocked(color):
  # Sends a message to the client to tell it to delay punches longer
  # because the punch was blocked.
  sendToClient(color, {
    'Type': 'PunchBlocked',
    'Color': color,
  })


def tellClientGameover(color):
  # Tell the client(s) that the game is over.
  sendToClient('Red', {
    'Type':  'GameOver',
    'Color': color,
  })
  sendToClient('Blue', {
    'Type':  'GameOver',
    'Color': color,
  })


def sendToClient(color, data):
  # Sends a message to the client with the given color,
  # if that client exists, otherwise this has no effect.
  if color in clients:
    conn = clients[color]
    conn.send(json.dumps(data).encode())


def sendToNode(nodeId, data):
  # Sends a message to the raft server instance with the given node ID,
  # if a server with that ID exists, otherwise this has no effect.
  if nodeId in senders:
    senders[nodeId].send(data)


def sendToAllNodes(data):
  # Broadcasts a message to all raft server instances.
  for nodeId in senders.keys():
    senders[nodeId].send(data)


def receiveMessage(msg, conn):
  # This method handles all messages from the client server instance(s).
  msgType = msg['Type']

  # Handle client messages
  if msgType == 'ClientConnected':
    clientConnected(msg['Color'], conn)
  elif msgType == 'ClientPunch':
    clientPunch(msg['Color'], msg['Hand'])
  elif msgType == 'ClientBlock':
    clientBlock(msg['Color'], msg['Hand'])
  elif msgType == 'Reset':
    resetEverything()

  # Handle Raft messages
  elif msgType == 'RequestVoteRequest':
    requestVoteRequest(msg['From'], msg['Term']) # TODO: Add in log index stuff
  elif msgType == 'RequestVoteReply':
    requestVoteReply(msg['From'], msg['Term'], msg['Granted'])
  elif msgType == 'AppendEntriesRequest':
    appendEntriesRequest(msg['From'], msg['Term'], msg['Entries'])
  elif msgType == 'AppendEntriesReplay':
    appendEntriesReply(msg['From'], msg['Term'], msg['Success'])

  # Handle unknown messages
  else:
    print("Unknown message: ")
    print(msg)


def main():
  global listener
  global senders
  global leaderTimeout

  # Setup the listener to start watching for incoming messages.
  listener = connections.listener(receiveMessage, nodeIdToURL[myNodeId], useMyHost)

  # Setup the collection of connections to talk to the other instances.
  for nodeId, hostAndPort in nodeIdToURL.items():
    if (nodeId != myNodeId) and (nodeId < nodeCount):
      sender = connections.sender(hostAndPort)
      senders[nodeId] = sender

  # Setup the timeout used to start elections of a leader.
  leaderTimeout = customTimer.customTimer(leaderHasTimedOut)

  # Keep server alive and wait
  input("Press Enter to Exit\n")

  # Socket closed so clean up and shut down
  print('Closing...')
  for sender in senders.values():
    sender.close()
  listener.close()
  leaderTimeout.close()


if __name__ == "__main__":
  main()
