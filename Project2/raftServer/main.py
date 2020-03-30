#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)
# due Apr 6, 2020 by 11:59 PM


import sys
import json
import random
import threading

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
heartbeatInterval   = 0.10 # Time, in seconds, between a leader's heartbeat message
heartbeatLowerBound = 0.50 # Lowest random time, in seconds, to add to timeout on heartbeat
heartbeatUpperBound = 1.00 # Highest random time, in seconds, to add to timeout on heartbeat
heartbeatMaximum    = 3.00 # The maximum allowed heatbeat timeout, in seconds.

stateNeutral           = 0
stateRightBlock        = 1 # blocking_with_right
stateLeftBlock         = 2 # blocking_with_left
stateRightPunchMissed  = 3
stateLeftPunchMissed   = 4
stateRightPunchBlocked = 5
stateLeftPunchBlocked  = 6
stateRightPunchHit     = 7
stateLeftPunchHit      = 8


# Communication variables
clients  = {}
listener = None
senders  = {}


# Raft variables
dataLock        = threading.Lock()
currentTerm     = 0
leaderNodeId    = -1
leaderTimeout   = None
leaderHeartbeat = None
votedFor        = -1
logs            = []
whoVotedForMe   = {}


def clientConnected(color, conn):
  # Indicates a client has been connected to this raft instance.
  with dataLock:
    global clients
    clients[color] = conn
  print('%s client connected' % (color))


def resetLog():
  # The client or another instance has asked to reset the game.
  # So reset the logs. If logs are empty, don't resend message.
  # This does not follow typical Raft, it is for testing only.
  needsReset = False
  with dataLock:
    global logs
    if logs:
      logs = []
      needsReset = True
  
  if needsReset:
    print('Reset!')
    sendToAllNodes({
      'Type': 'Reset',
    })
    sendToClient('Red', {
      'Type': 'Reset',
    })
    sendToClient('Blue', {
      'Type': 'Reset',
    })


def clientPunch(color, hand):
  if leaderNodeId != myNodeId:
    # We are a follower, send the message to the leader.
    # TODO: What do we do during leader election
    if leaderNodeId != -1:
      sendToNode(leaderNodeId, {
        'Type':  'ClientPunch',
        'Color': color,
        'Hand':  hand,
      })
  else:
    # We are the leader, deal with the punch
    print('%s punched with %s hand' % (color, hand))
    #
    # TODO: Implement
    #


def clientBlock(color, hand):
  if leaderNodeId != myNodeId:
    # We are a follower, send the message to the leader.
    # TODO: What do we do during leader election
    if leaderNodeId != -1:
      sendToNode(leaderNodeId, {
        'Type':  'ClientBlock',
        'Color': color,
        'Hand':  hand,
      })
  else:
    # We are the leader, deal with the block
    print('%s blocking with %s hand' % (color, hand))
    if hand == 'Right':
      addNewLogEntry(color, stateRightBlock)
    else:
      addNewLogEntry(color, stateLeftBlock)


def lastLogInfo():
  # Gets the last entries on the log.
  with dataLock:
    lastLogIndex = len(logs)-1
    lastLogTerm  = -1
    if lastLogIndex >= 0:
      lastLogTerm = logs[lastLogIndex]['Term']
    return (lastLogIndex, lastLogTerm)


def addNewLogEntry(color, state):
  # This will append a new log entry which sets our color (variable) to state (value).
  global logs
  with dataLock:
    logs.append({
      'Term':  currentTerm,
      'Color': color,
      'State': state,
    })


def getLogValue(color):
  # This will find the most recent state (value) for the given color (variable).
  global logs
  with dataLock:
    for entry in reversed(logs):
      if entry['Color'] == color:
        return entry['State']
    return stateNeutral


def leaderHasTimedOut():
  # The timeout for starting a new election has been reached.
  # Start a new leader election.
  global currentTerm
  global whoVotedForMe
  global leaderNodeId
  global votedFor
  with dataLock:
    currentTerm  += 1
    whoVotedForMe = {}
    leaderNodeId  = -1
    votedFor      = myNodeId

  lastLogIndex, lastLogTerm = lastLogInfo()
  sendToAllNodes({
    'Type': 'RequestVoteRequest',
    'From': myNodeId,
    'Term': currentTerm,
    'LastLogIndex': lastLogIndex,
    'LastLogTerm':  lastLogTerm,
  })
  print('%d started election' % (myNodeId))


def heartbeat():
  # Received a heartbeat from the leader so bump the timeout
  # to keep a new leader election from being kicked off.
  dt = random.random() * (heartbeatLowerBound - heartbeatUpperBound) + heartbeatLowerBound
  leaderTimeout.addTime(dt, heartbeatMaximum)


def sendOutHeartbeat():
  # We are (should be) the leader so send out AppendEntries requests.
  # Even empty the AppendEntries works as a heartbeat.
  if leaderNodeId == myNodeId:
    leaderHeartbeat.addTime(heartbeatInterval)
    entries = []
    #
    # TODO: Determine the entries to be sending
    #       Also add "prevLogIndex" and "prevLogTerm"
    #
    sendToAllNodes({
      'Type':    'AppendEntriesRequest',
      'From':    myNodeId,
      'Term':    currentTerm,
      'Entries': entries,
    })


def requestVoteRequest(fromNodeID, termNum, lastLogIndex, lastLogTerm):
  # This handles a RequestVote Request from another raft instance.
  global currentTerm
  global votedFor
  global logs

  # Someone is trying to start an election so beat the heart to keep from everyone timing out.
  heartbeat()

  # Determine if the node should vote (granted) for the candidate making the request.
  granted = False
  if termNum >= currentTerm:
    currentTerm = termNum
    curLogIndex, curLogTerm = lastLogInfo()
    if (lastLogTerm > curLogTerm) or ((lastLogTerm == curLogTerm) and (lastLogIndex >= curLogIndex)):
      if votedFor == fromNodeID:
        granted = True
      elif votedFor == -1:
        votedFor = fromNodeID
        granted  = True

  # Tell the candidate this node's decision.
  if granted:
    print('%d voted for %d' % (myNodeId, fromNodeID))
  else:
    print('%d did not vote for %d' % (myNodeId, fromNodeID))

  sendToNode(fromNodeID, {
    'Type':    'RequestVoteReply',
    'From':    myNodeId,
    'Term':    currentTerm,
    'Granted': granted,
  })


def requestVoteReply(fromNodeID, termNum, granted):
  # This handles a RequestVote Reply from another raft instance.
  global currentTerm
  global votedFor
  global whoVotedForMe
  global leaderNodeId
  if granted and (termNum == currentTerm):
    whoVotedForMe[fromNodeID] = True

  if len(whoVotedForMe) > nodeCount/2:
    # Look at me. I'm the leader now.
    votedFor = -1
    leaderNodeId = myNodeId
    leaderTimeout.stop()
    print('%d is now the leader' % (myNodeId))
    leaderHeartbeat.addTime(0.0)


def appendEntriesRequest(fromNodeID, termNum, entries):
  # This handles a AppendEntries Request from the leader.
  # If entries is empty then this is only for a heartbeat.
  global leaderNodeId
  global whoVotedForMe
  global votedFor
  global currentTerm
  if termNum >= currentTerm:

    # Maybe the first from the leader, deal with leader selection.
    leaderHeartbeat.stop()
    leaderNodeId  = fromNodeID
    whoVotedForMe = {}
    votedFor      = -1
    currentTerm   = termNum

    # Bump the timer to keep from leader election from being kicked off.
    heartbeat()
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
  # Broadcasts a message to all raft server instances other than this node.
  for nodeId in senders.keys():
    if nodeId != myNodeId:
      senders[nodeId].send(data)


def receiveMessage(msg, conn):
  # This method handles all messages from the client server instance(s).
  msgType = msg['Type']

  # Handle client messages (or messages repeated by another instance on behalf of the client)
  if msgType == 'ClientConnected':
    clientConnected(msg['Color'], conn)
  elif msgType == 'ClientPunch':
    clientPunch(msg['Color'], msg['Hand'])
  elif msgType == 'ClientBlock':
    clientBlock(msg['Color'], msg['Hand'])
  elif msgType == 'Reset':
    resetLog()

  # Handle Raft messages
  elif msgType == 'RequestVoteRequest':
    requestVoteRequest(msg['From'], msg['Term'], msg['LastLogIndex'], msg['LastLogTerm'])
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


def showStatus():
  # Prints the current status of this node
  print("My Node Id: %d" % (myNodeId))
  print("Node Count: %d" % (nodeCount))
  print('Leader Id:  %d' % (leaderNodeId))
  print('Term Num:   %d' % (currentTerm))
  if 'Red' in clients:
    print('Has Red Client')
  if 'Blue' in clients:
    print('Has Blue Client')


def showLogs():
  #
  # TODO: Implement
  #
  print("Implement")


def main():
  global listener
  global senders
  global leaderTimeout
  global leaderHeartbeat

  # Setup the listener to start watching for incoming messages.
  listener = connections.listener(receiveMessage, nodeIdToURL[myNodeId], useMyHost)

  # Setup the collection of connections to talk to the other instances.
  for nodeId, hostAndPort in nodeIdToURL.items():
    if (nodeId != myNodeId) and (nodeId < nodeCount):
      sender = connections.sender(hostAndPort)
      senders[nodeId] = sender

  # Setup the timeout used to start elections of a leader.
  leaderTimeout = customTimer.customTimer(leaderHasTimedOut)

  # Setup the timeout which is used by the leader to send out heartbeats.
  leaderHeartbeat = customTimer.customTimer(sendOutHeartbeat)

  # Wait for user input.
  while True:
    print("What would you like to do?")
    print("  1. Timeout")
    print("  2. Stop Heartbeat")
    print("  3. Show Status")
    print("  4. Show Log")
    print("  5. Exit")

    try:
      choice = int(input("Enter your choice: "))
    except:
      print("Invalid choice. Try again.")
      continue

    if choice == 1:
      leaderTimeout.stop()
      leaderHasTimedOut()
    elif choice == 2:
      leaderHeartbeat.stop()
    elif choice == 3:
      showStatus()
    elif choice == 4:
      showLogs()
    elif choice == 5:
      break
    else:
      print("Invalid choice \"%s\". Try again." % (choice))

  # Socket closed so clean up and shut down
  print('Closing...')
  for sender in senders.values():
    sender.close()
  listener.close()
  leaderTimeout.close()
  leaderHeartbeat.close()


if __name__ == "__main__":
  main()
