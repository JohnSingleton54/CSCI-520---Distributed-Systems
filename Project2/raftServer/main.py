#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)

# due Apr 6, 2018 by 11:59 PM (HI JOHN, I'm a conflict!!!)

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
heartbeatInterval   = 0.10 # Time, in seconds, between an election or a leader's heartbeat message
heartbeatLowerBound = 0.50 # Lowest random time, in seconds, to add to timeout on heartbeat
heartbeatUpperBound = 1.50 # Highest random time, in seconds, to add to timeout on heartbeat
heartbeatMaximum    = 5.00 # The maximum allowed heatbeat timeout, in seconds.

stateNeutral           = 'neutral'
stateRightBlock        = 'blocking_with_right'
stateLeftBlock         = 'blocking_with_left'
stateRightPunchMissed  = 'right_punch_missed'
stateLeftPunchMissed   = 'left_punch_missed'
stateRightPunchBlocked = 'right_punch_blocked'
stateLeftPunchBlocked  = 'left_punch_blocked'
stateRightPunchHit     = 'right_punch_hit'
stateLeftPunchHit      = 'left_punch_hit'

statusFollower  = 'Follower'
statusCandidate = 'Candidate'
statusLeader    = 'Leader'


class mainObject:
  def __init__(self):

    # Communication variables
    self.clients  = {}
    self.listener = None
    self.senders  = {}

    # Raft variables
    self.nodeStatus    = statusFollower
    self.dataLock      = threading.Lock()
    self.currentTerm   = 0
    self.leaderNodeId  = -1
    self.votedFor      = -1
    self.pendingEvents = []
    self.logs          = []
    self.whoVoted      = {}
    self.leaderTimeout     = None
    self.leaderHeartbeat   = None
    self.electionHeartbeat = None


  def clientConnected(self, color, conn):
    # Indicates a client has been connected to this raft instance.
    with self.dataLock:
      self.clients[color] = conn
    print('%s client connected' % (color))


  def resetLog(self):
    # The client or another instance has asked to reset the game.
    # So reset the logs. If logs are empty, don't resend message.
    # This does not follow typical Raft, it is for testing only.
    needsReset = False
    with self.dataLock:
      if self.logs:
        self.logs = []
        needsReset = True
    
    if needsReset:
      print('Reset!')
      self.sendToAllNodes({
        'Type': 'Reset',
      })
      self.sendToClient('Red', {
        'Type': 'Reset',
      })
      self.sendToClient('Blue', {
        'Type': 'Reset',
      })


  def clientPunch(self, color, hand):
    if self.nodeStatus != statusLeader:
      # We are a follower, send the message to the leader or put it
      # into pending queue to send once the leader has been selected.
      msg = {
        'Type':  'ClientPunch',
        'Color': color,
        'Hand':  hand,
      }
      if self.leaderNodeId != -1:
        self.sendToNode(self.leaderNodeId, msg)
      else:
        with self.dataLock:
          self.pendingEvents.append(msg)
    else:
      # We are the leader, deal with the punch.
      print('%s punched with %s hand' % (color, hand))

      # Find out what state the opponent is at.
      opponentState = self.getLogValue('Blue' if color == 'Red' else 'Red')

      # Find the new state of this player.
      if (hand == 'Left') and (opponentState == stateRightBlock):
        newState = stateLeftPunchBlocked
      elif (hand == 'Right') and (opponentState == stateLeftBlock):
        newState = stateRightPunchBlocked
      else:
        # Check if the 10% possibility hit has happened.
        hit = random.random() <= 0.1
        if hand == 'Left':
          newState = stateLeftPunchHit if hit else stateLeftPunchMissed
        else:
          newState = stateRightPunchHit if hit else stateRightPunchMissed
      
      # Write new state to logs as an uncommitted entry,
      # the next heartbeat will pick it up and start sharing it.
      self.addNewLogEntry(color, newState)


  def clientBlock(self, color, hand):
    if self.nodeStatus != statusLeader:
      # We are a follower, send the message to the leader or put it
      # into pending queue to send once the leader has been selected.
      msg = {
        'Type':  'ClientBlock',
        'Color': color,
        'Hand':  hand,
      }
      if self.leaderNodeId != -1:
        self.sendToNode(self.leaderNodeId, msg)
      else:
        with self.dataLock:
          self.pendingEvents.append(msg)
    else:
      # We are the leader, deal with the block
      print('%s blocking with %s hand' % (color, hand))
      newState = stateLeftBlock if hand == 'Left' else stateRightBlock

      # Write new state to logs as an uncommitted entry,
      # the next heartbeat will pick it up and start sharing it.
      self.addNewLogEntry(color, newState)


  def lastLogInfo(self):
    # Gets the last entries on the log.
    with self.dataLock:
      lastLogIndex = len(self.logs)-1
      lastLogTerm  = -1
      if lastLogIndex >= 0:
        lastLogTerm = self.logs[lastLogIndex]['Term']
      return (lastLogIndex, lastLogTerm)


  def addNewLogEntry(self, color, state):
    # This will append a new log entry which sets our color (variable) to state (value).
    with self.dataLock:
      self.logs.append({
        'Term':      self.currentTerm,
        'Color':     color,
        'State':     state,
        'Committed': False,
      })


  def getLogValue(self, color):
    # This will find the most recent state (value) for the given color (variable).
    with self.dataLock:
      for entry in reversed(self.logs):
        if entry['Committed'] and (entry['Color'] == color):
          return entry['State']
      return stateNeutral


  def sendOutElectionHeartbeat(self):
    # Periodically send out the message to all nodes which haven't replied.
    lastLogIndex, lastLogTerm = self.lastLogInfo()
    msg = {
      'Type':         'RequestVoteRequest',
      'From':         myNodeId,
      'Term':         self.currentTerm,
      'LastLogIndex': lastLogIndex,
      'LastLogTerm':  lastLogTerm,
    }
    for nodeId in self.senders.keys():
      if not nodeId in self.whoVoted:
        self.sendToNode(nodeId, msg)
    self.electionHeartbeat.addTime(heartbeatInterval)


  def sendOutLeaderHeartbeat(self):
    # We are (should be) the leader so send out AppendEntries requests.
    # Even empty the AppendEntries works as a heartbeat.
    if self.nodeStatus == statusLeader:
      self.leaderHeartbeat.addTime(heartbeatInterval)
      entries = []
      #
      # TODO: Determine the entries to be sending
      #       Also add "prevLogIndex" and "prevLogTerm"
      #
      self.sendToAllNodes({
        'Type':    'AppendEntriesRequest',
        'From':    myNodeId,
        'Term':    self.currentTerm,
        'Entries': entries,
      })


  def requestVoteRequest(self, fromNodeID, termNum, lastLogIndex, lastLogTerm):
    # This handles a RequestVote Request from another raft instance.
    # Some one has started an election so beat the heart to keep from kicking of another one.
    self.heartbeat()

    # Determine if the node should vote (granted) for the candidate making the request.
    granted = False
    if termNum >= self.currentTerm:
      self.currentTerm = termNum
      curLogIndex, curLogTerm = self.lastLogInfo()
      if (lastLogTerm > curLogTerm) or ((lastLogTerm == curLogTerm) and (lastLogIndex >= curLogIndex)):
        if (self.votedFor == fromNodeID) or (self.votedFor == -1):
          self.votedFor = fromNodeID
          granted = True

    # Tell the candidate this node's decision.
    self.sendToNode(fromNodeID, {
      'Type':    'RequestVoteReply',
      'From':    myNodeId,
      'Term':    self.currentTerm,
      'Granted': granted,
    })


  def requestVoteReply(self, fromNodeID, termNum, granted):
    # This handles a RequestVote Reply from another raft instance.
    if termNum == self.currentTerm:

      # Count how many votes were granted to this node.
      count = 0
      with self.dataLock:
        self.whoVoted[fromNodeID] = granted
        for nodeGranted in self.whoVoted.values():
          if nodeGranted:
            count += 1

      if count > nodeCount/2:
        # Look at me. I'm the leader now.
        self.setAsLeader()


  def appendEntriesRequest(self, fromNodeID, termNum, entries):
    # This handles a AppendEntries Request from the leader.
    # If entries is empty then this is only for a heartbeat.
    if termNum >= self.currentTerm:

      # Maybe the first from the leader, deal with leader selection.
      if (self.leaderNodeId != fromNodeID) or (termNum > self.currentTerm) or (self.votedFor != -1):
        self.setAsFollower(fromNodeID, termNum)

      # Bump the timer to keep from leader election from being kicked off.
      self.heartbeat()
      if entries:
        # Apply the entries
        #
        # TODO: Implement
        #
        pass


  def appendEntriesReply(self, fromNodeID, termNum, success):
    # This handles a AppendEntries Reply from another raft instance.
    #
    # TODO: Implement
    # once a state had been committed we need to update the client
    # about the state change, for things like opponents state and end game hits.
    #
    pass


  def heartbeat(self):
    # Received a heartbeat from the leader so bump the timeout
    # to keep a new leader election from being kicked off.
    dt = random.random() * (heartbeatUpperBound - heartbeatLowerBound) + heartbeatLowerBound
    self.leaderTimeout.addTime(dt, heartbeatMaximum)
    #print('%d, %d timeout is %0.5fs' % (self.currentTerm, myNodeId, self.leaderTimeout.timeLeft()))


  def setAsCandidate(self):
    # Set this node as a candidate and start a new leader election.
    # This usually happens when the timeout for starting a new election has been reached.
    with self.dataLock:
      self.currentTerm += 1
      self.whoVoted     = {myNodeId: True}
      self.leaderNodeId = -1
      self.votedFor     = myNodeId
      self.nodeStatus   = statusCandidate
      print('%d: %d started election' % (self.currentTerm, myNodeId))
      self.electionHeartbeat.addTime(0.0)
    self.heartbeat()


  def setAsLeader(self):
    # Set this node as the leader and start sending out heartbeats.
    pending = []
    with self.dataLock:
      self.leaderTimeout.stop()
      self.electionHeartbeat.stop()
      pending = self.pendingEvents
      self.votedFor      = -1
      self.whoVoted      = {}
      self.leaderNodeId  = myNodeId
      self.nodeStatus    = statusLeader
      self.pendingEvents = []
      self.leaderHeartbeat.addTime(0.0)
      print('%d: %d is now the leader' % (self.currentTerm, myNodeId))
    for event in pending:
      receiveMessage(event)


  def setAsFollower(self, newLeader, newTerm):
    # Set this node as a follower, update leader and term values.
    pending = []
    with self.dataLock:
      self.leaderHeartbeat.stop()
      self.electionHeartbeat.stop()
      pending = self.pendingEvents
      self.pendingEvents = []
      self.leaderNodeId  = newLeader
      self.whoVoted      = {}
      self.votedFor      = -1
      self.currentTerm   = newTerm
      self.nodeStatus    = statusFollower
      print('%d: %d is now the leader' % (self.currentTerm, self.leaderNodeId))
    for event in pending:
      self.receiveMessage(event)


  def tellClientPunchBlocked(self, color):
    # Sends a message to the client to tell it to delay punches longer
    # because the punch was blocked.
    self.sendToClient(color, {
      'Type': 'PunchBlocked',
      'Color': color,
    })


  def tellClientGameover(self, color):
    # Tell the client(s) that the game is over.
    self.sendToClient('Red', {
      'Type':  'GameOver',
      'Color': color,
    })
    self.sendToClient('Blue', {
      'Type':  'GameOver',
      'Color': color,
    })


  def sendToClient(self, color, data):
    # Sends a message to the client with the given color,
    # if that client exists, otherwise this has no effect.
    conn = None
    with self.dataLock:
      if color in self.clients:
        conn = self.clients[color]
    if conn:
        conn.send(json.dumps(data).encode())


  def sendToNode(self, nodeId, data):
    # Sends a message to the raft server instance with the given node ID,
    # if a server with that ID exists, otherwise this has no effect.
    conn = None
    with self.dataLock:
      if nodeId in self.senders:
        conn = self.senders[nodeId]
    if conn:
      conn.send(data)


  def sendToAllNodes(self, data):
    # Broadcasts a message to all raft server instances other than this node.
    conns = []
    with self.dataLock:
      for nodeId in self.senders.keys():
        if nodeId != myNodeId:
          conns.append(self.senders[nodeId])
    for conn in conns:
      conn.send(data)


  def receiveMessage(self, msg, conn):
    # This method handles all messages from the client server instance(s).
    msgType = msg['Type']

    # Handle client messages (or messages repeated by another instance on behalf of the client)
    if msgType == 'ClientConnected':
      self.clientConnected(msg['Color'], conn)
    elif msgType == 'ClientPunch':
      self.clientPunch(msg['Color'], msg['Hand'])
    elif msgType == 'ClientBlock':
      self.clientBlock(msg['Color'], msg['Hand'])
    elif msgType == 'Reset':
      self.resetLog()

    # Handle Raft messages
    elif msgType == 'RequestVoteRequest':
      self.requestVoteRequest(msg['From'], msg['Term'], msg['LastLogIndex'], msg['LastLogTerm'])
    elif msgType == 'RequestVoteReply':
      self.requestVoteReply(msg['From'], msg['Term'], msg['Granted'])
    elif msgType == 'AppendEntriesRequest':
      self.appendEntriesRequest(msg['From'], msg['Term'], msg['Entries'])
    elif msgType == 'AppendEntriesReplay':
      self.appendEntriesReply(msg['From'], msg['Term'], msg['Success'])

    # Handle unknown messages
    else:
      print("Unknown message: ")
      print(msg)


  def showInfo(self):
    # Prints the current status of this node.
    with self.dataLock:
      print('Information:')
      print('  My Node Id: %d' % (myNodeId))
      print('  Node Count: %d' % (nodeCount))
      print('  Status:     %s' % (self.nodeStatus))
      print('  Leader Id:  %d' % (self.leaderNodeId))
      print('  Term Num:   %d' % (self.currentTerm))
      print('  Timeout:    %0.5fs' % (self.leaderTimeout.timeLeft()))
      print('  Client(s): ', end=' ')
      for client in self.clients:
          print(client, end=' ')
      print()


  def showLogs(self):
    # Prints the logs in this node.
    with self.dataLock:
      print('Logs:')
      for entry in self.logs:
        term  = entry['Term']
        color = entry['Color']
        state = entry['State']
        check = 'X' if entry['Committed'] else ' '
        print('   [%s] %d: %s <- %s'%(check, term, color, state))


  def main(self):
    # Setup the listener to start watching for incoming messages.
    self.listener = connections.listener(self.receiveMessage, nodeIdToURL[myNodeId], useMyHost)

    # Setup the collection of connections to talk to the other instances.
    for nodeId, hostAndPort in nodeIdToURL.items():
      if (nodeId != myNodeId) and (nodeId < nodeCount):
        self.senders[nodeId] = connections.sender(hostAndPort)

    # Setup the timers used to keep Raft elections working.
    self.leaderTimeout     = customTimer.customTimer(self.setAsCandidate)
    self.leaderHeartbeat   = customTimer.customTimer(self.sendOutLeaderHeartbeat)
    self.electionHeartbeat = customTimer.customTimer(self.sendOutElectionHeartbeat)

    # Start the leader timeout by forcing a heartbeat.
    self.heartbeat()

    # Wait for user input.
    while True:
      print("What would you like to do?")
      print("  1. Timeout")
      print("  2. Stop Heartbeat")
      print("  3. Show Info")
      print("  4. Show Log")
      print("  5. Exit")

      try:
        choice = int(input("Enter your choice: "))
      except:
        print("Invalid choice. Try again.")
        continue

      if choice == 1:
        self.setAsCandidate()
      elif choice == 2:
        self.leaderHeartbeat.stop()
      elif choice == 3:
        self.showInfo()
      elif choice == 4:
        self.showLogs()
      elif choice == 5:
        break
      else:
        print("Invalid choice \"%s\". Try again." % (choice))

    # Socket closed so clean up and shut down
    print('Closing...')
    for sender in self.senders.values():
      sender.close()
    self.listener.close()
    self.leaderTimeout.close()
    self.leaderHeartbeat.close()
    self.electionHeartbeat.close()


if __name__ == "__main__":
  mainObject().main()
