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
print('My Node Id is %d' % (myNodeId))

nodeCount = int(sys.argv[2])
print('The Node Count is %d' % (nodeCount))


# Constant values
heartbeatInterval   = 0.1 # Time, in seconds, between an election or a leader's heartbeat message
heartbeatLowerBound = 1.0 # Lowest random time, in seconds, to add to timeout on heartbeat
heartbeatUpperBound = 3.0 # Highest random time, in seconds, to add to timeout on heartbeat

stateNeutral           = 'neutral'
stateStartNewGame      = 'start_new_game'
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

    # VARIABLES USED BY ALL NODE TYPES:
    self.nodeStatus    = statusFollower
    self.dataLock      = threading.Lock()
    self.currentTerm   = 0
    self.leaderNodeId  = -1 # nodeId of who this node thinks is the leader, -1 for not set
    self.votedFor      = -1 # nodeId of who this node has voted for, -1 means not voted yet
    self.pendingEvents = [] # list of dict: {'Type': punch/block, 'Color': Red/Blue, 'Hand': Right/Left}
    self.log           = [] # list of dict: {'Term': <int>, 'Color':  Red/Blue, 'State': <string>, 'Committed': True/False}
    self.leaderTimeout = None

    # VARIABLES USED BY CANDIDATES:
    self.whoVoted = {} # dict: key = nodeId, value = (granted) True/False
    self.electionHeartbeat = None

    # VARIABLES USED BY LEADERS:
    # dict: key = nodeId, value = the index of the next log entry the leader will send to that
    # follower (See the second column on page 7 of the paper and the sendOutLeaderHeartbeat method.)
    self.nextIndex  = {}
    self.matchIndex = {} # The index of highest log entry known to be replicated on server.
    self.leaderHeartbeat = None


  def clientConnected(self, color, conn):
    # Indicates a client has been connected to this raft instance.
    with self.dataLock:
      self.clients[color] = conn
    print('%s client connected' % (color))

    # Update the client with the state.
    self.updateClientsForNewCommits(-1)


  def resetGame(self):
    # The client or another instance has asked to reset the game.
    if self.nodeStatus != statusLeader:
      # We are a follower, send the message to the leader or put it
      # into pending queue to send once the leader has been selected.
      msg = {
        'Type': 'ResetGame',
      }
      if self.leaderNodeId != -1:
        self.sendToNode(self.leaderNodeId, msg)
      else:
        with self.dataLock:
          self.pendingEvents.append(msg)
    else:
      # Write to both that game has been reset and we are starting a new game.
      self.addNewLogEntry('Red',  stateStartNewGame)
      self.addNewLogEntry('Blue', stateStartNewGame)


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
      
      # Write new state to log as an uncommitted entry,
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

      # Write new state to log as an uncommitted entry,
      # the next heartbeat will pick it up and start sharing it.
      self.addNewLogEntry(color, newState)


  def lastLogInfo(self):
    # Gets the last entries on the log.
    with self.dataLock:
      lastLogIndex = len(self.log)-1
      lastLogTerm  = -1
      if lastLogIndex >= 0:
        lastLogTerm = self.log[lastLogIndex]['Term']
      return (lastLogIndex, lastLogTerm)


  def lastCommittedIndex(self):
    # Gets the index of the last committed index in the log.
    with self.dataLock:
      for i in reversed(range(len(self.log))):
        if self.log[i]['Committed']:
          return i
      return -1


  def addNewLogEntry(self, color, state):
    # This will append a new log entry which sets our color (variable) to state (value).
    with self.dataLock:
      self.log.append({
        'Term':      self.currentTerm,
        'Color':     color,
        'State':     state,
        'Committed': False,
      })


  def getLogValue(self, color):
    # This will find the most recent state (value) for the given color (variable).
    with self.dataLock:
      for entry in reversed(self.log):
        if entry['Committed'] and (entry['Color'] == color):
          return entry['State']
      return stateNeutral


  def getLogNewestValue(self, color, lowestIndex):
    # This will find the most recent state (value) for the given color (variable)
    # which is above the given 'lowIndex'. This is used to find recently committed.
    with self.dataLock:
      for entry in reversed(self.log[lowestIndex:]):
        if entry['Committed'] and (entry['Color'] == color):
          return (True, entry['State'])
      return (False, stateNeutral)
  

  #=========================================================
  # Candidate Election (RequestVote) Message Handlers
  #=========================================================

  def sendOutElectionHeartbeat(self):
    # This is the start of a candidate sending out RequestVote.
    # This is called periodically by a timer to send out the
    # messages to all nodes which this candidate thinks hasn't voted yet.
    if self.nodeStatus == statusCandidate:
      lastLogIndex, lastLogTerm = self.lastLogInfo()
      msg = {
        'Type':         'RequestVoteRequest',
        'From':         myNodeId,
        'Term':         self.currentTerm,
        'LastLogIndex': lastLogIndex,
        'LastLogTerm':  lastLogTerm,
      }
      for nodeId in self.senders.keys():
        if not nodeId in self.whoVoted and nodeId != myNodeId:
          self.sendToNode(nodeId, msg)


  def requestVoteRequest(self, fromNodeId, termNum, lastLogIndex, lastLogTerm):
    # This handles a RequestVote Request from another raft instance.
    # Some one has started an election so beat the heart to keep from kicking of another one.
    self.heartbeat()

    # Determine if the node should vote (granted) for the candidate making the request.
    # See page 8, last paragraph of 5.4.1
    granted = False
    if termNum >= self.currentTerm:
      # If term has changed throw out who you voted for so you can vote again and update term.
      if termNum > self.currentTerm:
        self.currentTerm = termNum
        self.votedFor = -1
      # Check that you don't have a more up-to-date log than the candidate.
      curLogIndex, curLogTerm = self.lastLogInfo()
      if (lastLogTerm > curLogTerm) or ((lastLogTerm == curLogTerm) and (lastLogIndex >= curLogIndex)):
        # The candidate has equal or better log so vote for them if you haven't already voted.
        if (self.votedFor == fromNodeId) or (self.votedFor == -1):
          self.votedFor = fromNodeId
          granted = True

    # Tell the candidate this node's decision.
    self.sendToNode(fromNodeId, {
      'Type':    'RequestVoteReply',
      'From':    myNodeId,
      'Term':    self.currentTerm,
      'Granted': granted,
    })


  def requestVoteReply(self, fromNodeId, termNum, granted):
    # This handles a RequestVote Reply from another raft instance.
    if termNum == self.currentTerm:

      # Count how many votes were granted to this node.
      count = 0
      with self.dataLock:
        self.whoVoted[fromNodeId] = granted
        for nodeGranted in self.whoVoted.values():
          if nodeGranted:
            count += 1

      if count > nodeCount/2:
        # Look at me. I'm the leader now.
        self.setAsLeader()

<<<<<<< Updated upstream
=======
# temp notes for Log Replication (JMS):
# - A log entry is committed once the leader that created the entry has replicated it on a majority
# of the servers. These are the entries that are safe to apply to the local state machines.
# - The leader retries AppendEntries RPCs indefinitely (even after it has responded to the client)
# until all followers eventually store all log entries. [JMS: I think this occurs in our current
# implementation.]
>>>>>>> Stashed changes

  #=========================================================
  # Leader Heartbeat (AppendEntries) Message Handlers
  #=========================================================

  # temp notes for Log Replication (JMS):
  # - A log entry is committed once the leader that created the entry has replicated it on a majority
  # of the servers. These are the entries that are safe to apply to the local state machines.
  # - The leader retries AppendEntries RPCs indefinitely (even after it has responded to the client)
  # until all followers eventually store all log entries.


  def sendOutLeaderHeartbeat(self):
    # We are the leader so send out AppendEntries requests.
    # This method is called periodically by a timer.
    # Even empty the AppendEntries works as a heartbeat.
    if self.nodeStatus == statusLeader:

      # Send the sequence of log entries from nextIndex to lastLogIndex, which will in general be
      # different for each follower.
      lastLogIndex, lastLogTerm = self.lastLogInfo()
      leaderCommit = self.lastCommittedIndex()
      for nodeId in self.senders.keys():
        if nodeId == myNodeId:
          # Skip over my nodeId since I'm the leader.
          continue

        if self.nextIndex[nodeId] > lastLogIndex:
          # for a heartbeat
          entries = []
        else:
          # for a proper AppendEntries request
          with self.dataLock:
            entries = self.log[self.nextIndex[nodeId]:]

        prevLogIndex = self.nextIndex[nodeId] - 1
        prevLogTerm  = -1
        if prevLogIndex >= 0:
          prevLogTerm = self.log[prevLogIndex]['Term']

        self.sendToNode(nodeId, {
          'Type':         'AppendEntriesRequest',
          'From':         myNodeId,
          'Term':         self.currentTerm,
          'PrevLogIndex': prevLogIndex,
          'PrevLogTerm':  prevLogTerm,
          'Entries':      entries,
          'LeaderCommit': leaderCommit
        })


  def appendEntriesRequest(self, fromNodeId, termNum, prevLogIndex, prevLogTerm, entries, leaderCommit):
    # This handles an AppendEntries Request from the leader.
    # If entries is empty then this is only for a heartbeat.
    if termNum >= self.currentTerm:

      # Maybe the first from the leader, deal with leader selection.
      if (self.leaderNodeId != fromNodeId) or (termNum > self.currentTerm) or (self.votedFor != -1):
        self.setAsFollower(fromNodeId, termNum)

      # Bump the timer to keep from leader election from being kicked off.
      self.heartbeat()

      # Add and update entries if possible
      if entries:
        # the consistency check (See page 7 paragraph 3 "The second property is guaranteed by...".)
        lastLogIndex, lastLogTerm = self.lastLogInfo()
        if (lastLogIndex != prevLogIndex) or (lastLogTerm != prevLogTerm): # the consistency check fails
          success = False
        else: # the consistency check passes
          success = True
          # update the local log
          with self.dataLock:
            if lastLogIndex != prevLogIndex:
              del self.log[prevLogIndex+1:]
            for entry in entries:
              entry['Committed'] = False
              self.log.append(entry)

        logIndex = len(self.log)-1
        self.sendToNode(fromNodeId, {
          'Type': 'AppendEntriesReply',
          'From': myNodeId,
          'Term': self.currentTerm,
          'Index': logIndex,
          'Success': success
        })

      # Update the committed
      self.commitEntries(leaderCommit)


  def appendEntriesReply(self, fromNodeId, termNum, index, success):
    # This handles an AppendEntries reply from another raft instance.
    if not success:
      self.nextIndex[fromNodeId] -= 1
    else:
      self.nextIndex[fromNodeId] = index + 1
      self.matchIndex[fromNodeId] = index + 1

    # Update leader commits by checking for a majority.
    leaderCommit = self.lastCommittedIndex()
    nextCommit = -1
    for i in range(leaderCommit, len(self.log)):
      if not self.hasMajorityMatch(i):
        break
      nextCommit = i

    if nextCommit > leaderCommit:
      self.commitEntries(nextCommit)


  def hasMajorityMatch(self, index):
    # This checks if the majority of the nodes hav update to the given index.
    count = 1 # Start at 1 since we know the leader has matched itself.
    for nodeId in self.matchIndex.keys():
      if nodeId != myNodeId:
        if index <= self.matchIndex[nodeId]:
          count +=1
    return count >= nodeCount/2


  def commitEntries(self, leaderCommit):
    # Updates the committed logs up to the leaderCommit.
    # This is done for all logs.
    anyNewCommits = False
    lowestIndex = -1
    with self.dataLock:
      for i in range(min(len(self.log), leaderCommit+1)):
        entry = self.log[i]
        if not entry['Committed']:
          if lowestIndex < 0:
            lowestIndex = i
          anyNewCommits = True
          entry['Committed'] = True

    # If there are new commits, persist the log and update the clients.
    if anyNewCommits:
      self.saveLog()
      self.updateClientsForNewCommits(lowestIndex)


  def heartbeat(self):
    # Received a heartbeat from the leader so bump the timeout
    # to keep a new leader election from being kicked off.
    dt = random.random() * (heartbeatUpperBound - heartbeatLowerBound) + heartbeatLowerBound
    self.leaderTimeout.start(dt)
    #print('%d, %d timeout is %0.5fs' % (self.currentTerm, myNodeId, self.leaderTimeout.timeLeft()))


  def leaderHasTimedout(self):
    # This handles when a leader timeout has elapsed making this node think the leader is not responding.
    # If this isn't already the leader, start a new election.
    if self.nodeStatus != statusLeader:
      self.setAsCandidate()


  def setAsCandidate(self):
    # Set this node as a candidate and start a new leader election.
    with self.dataLock:
      self.currentTerm += 1
      self.whoVoted     = {myNodeId: True}
      self.leaderNodeId = -1
      self.votedFor     = myNodeId
      self.nodeStatus   = statusCandidate
      print('%d: %d started election' % (self.currentTerm, myNodeId))
      self.electionHeartbeat.start(0.0)
    # Beat the heart to restart the timeout for this election.
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

      # Initialize all nextIndex values to the index just after the last one in its log.
      logLength = len(self.log)
      for nodeId in self.senders.keys():
        self.nextIndex[nodeId]  = logLength
        self.matchIndex[nodeId] = 0

      # Start the leader heartbeat.
      print('%d: %d is now the leader' % (self.currentTerm, myNodeId))
      self.leaderHeartbeat.start(0.0)

    # Send any messages which were pended during leader election.
    for event in pending:
      self.receiveMessage(event)


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

    # Send any messages which were pended during leader election.
    for event in pending:
      self.receiveMessage(event)


  def updateClientsForNewCommits(self, lowestIndex):
    # This updates the connected clients for the state of the game.
    if len(self.clients) <= 0:
      # No clients so don't bother updating them.
      return

    newRedState, redState = self.getLogNewestValue('Red', lowestIndex)
    newBlueState, blueState = self.getLogNewestValue('Blue', lowestIndex)
    
    # Check for a game reset in both red and blue to know that no other action
    # has been taken, otherwise treat a `stateStartNewGame` as a `stateNeutral`.
    if redState == stateStartNewGame and blueState == stateStartNewGame:
      self.sendToAllClients({
        'Type': 'GameReset',
      })
      return
    if redState == stateStartNewGame:
      redState = stateNeutral
    if blueState == stateStartNewGame:
      blueState = stateNeutral

    # Update the states of the clients.
    if newRedState:
      self.updateColorForNewCommits('Red', 'Blue', redState)
    if newBlueState:
      self.updateColorForNewCommits('Blue', 'Red', blueState)


  def updateColorForNewCommits(self, player, opponent, state):
    # This updates the player and opponent on the state of the player.
    hand      = None
    condition = None
    if state == stateNeutral:
      # Nothing to update
      return
    elif state == stateRightBlock:
      hand      = 'Right'
      condition = 'Block'
    elif state == stateLeftBlock:
      hand      = 'Left'
      condition = 'Block'
    elif state == stateRightPunchMissed:
      hand      = 'Right'
      condition = 'Punch'
    elif state == stateLeftPunchMissed:
      hand      = 'Left'
      condition = 'Punch'
    elif state == stateRightPunchBlocked:
      hand      = 'Right'
      condition = 'Punch'
      self.sendToClient(player, {
        'Type': 'PunchBlocked'
      })
    elif state == stateLeftPunchBlocked:
      hand      = 'Left'
      condition = 'Punch'
      self.sendToClient(player, {
        'Type': 'PunchBlocked'
      })
    elif state == stateRightPunchHit:
      hand      = 'Right'
      condition = 'Punch'
      self.sendToAllClients({
        'Type':  'Hit',
        'Color': opponent
      })
    elif state == stateLeftPunchHit:
      hand      = 'Left'
      condition = 'Punch'
      self.sendToAllClients({
        'Type':   'Hit',
        'Color':  opponent
      })
      
    # Tells the opponent what consition its opponent (the player) is in.
    if hand and condition:
      self.sendToClient(opponent, {
        'Type':      'OpponentChanged',
        'Hand':      hand,
        'Condition': condition
      })


  def __getLogFileName(self):
    # Gets the name of the log file for this node ID.
    return 'log%d.json' % myNodeId


  def saveLog(self):
    # Save the log to the file. For debugging the log are JSON'ed
    # as is including the committed and uncommitted entries.
    with self.dataLock:
      data = json.dumps(self.log)
      
    f = open(self.__getLogFileName(), 'w')
    f.write(data)
    f.close()

  
  def loadLog(self):
    # Loads the log from the file.
    try:
      f = open(self.__getLogFileName(), 'r')
      data = f.read()
      f.close()

      if data:
        log = json.loads(data)
        # (Optional) strip out uncommitted values.
        with self.dataLock:
          self.log = log
    except Exception as e:
      print('Failed to load from log file: %s' % (e))


  def sendToClient(self, color, data):
    # Sends a message to the client with the given color,
    # if that client exists, otherwise this has no effect.
    conn = None
    with self.dataLock:
      if color in self.clients:
        conn = self.clients[color]
    if conn:
      msg = (json.dumps(data)+'#').encode()
      conn.send(msg)


  def sendToAllClients(self, data):
    # Sends a message to the all clients connected to this server,
    # if any clients exist, otherwise this has no effect.
    conns = None
    with self.dataLock:
      conns = self.clients.values()
    msg = (json.dumps(data)+'#').encode()
    for conn in conns:
      conn.send(msg)


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
    elif msgType == 'ResetGame':
      self.resetGame()

    # Handle Raft Messages for RequestVote
    elif msgType == 'RequestVoteRequest':
      self.requestVoteRequest(msg['From'], msg['Term'], msg['LastLogIndex'], msg['LastLogTerm'])
    elif msgType == 'RequestVoteReply':
      self.requestVoteReply(msg['From'], msg['Term'], msg['Granted'])
    
    # Handle Raft Messages for AppendEntries
    elif msgType == 'AppendEntriesRequest':
      self.appendEntriesRequest(msg['From'], msg['Term'], msg['PrevLogIndex'], msg['PrevLogTerm'], msg['Entries'], msg['LeaderCommit'])
    elif msgType == 'AppendEntriesReply':
      self.appendEntriesReply(msg['From'], msg['Term'], msg['Index'], msg['Success'])

    # Handle unknown messages
    else:
      print('Unknown message:', msg)


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
      if self.clients:
        print('  Client(s): ', ', '.join(self.clients.keys()))
      if self.nodeStatus == statusLeader:
        print('  nextIndex: ', self.nextIndex)
        print('  matchIndex:', self.matchIndex)


  def showLog(self):
    # Prints the log in this node.
    with self.dataLock:
      print('Log:')
      for entry in self.log:
        term  = entry['Term']
        color = entry['Color']
        state = entry['State']
        check = 'X' if entry['Committed'] else ' '
        print('   [%s] %d: %s <- %s'%(check, term, color, state))


  def addTestEntries(self):
    # Add in a few test log entries to this nodes log even if they aren't the leader.
    newNums = []
    for i in range(4):
      r = str(random.randint(0, 1000))
      newNums.append(r)
      self.addNewLogEntry('Test', r)
    print('New Test Logs:', ', '.join(newNums))


  def main(self):
    # Setup the listener to start watching for incoming messages.
    self.listener = connections.listener(self.receiveMessage, nodeIdToURL[myNodeId], useMyHost)

    # Setup the collection of connections to talk to the other instances.
    for nodeId, hostAndPort in nodeIdToURL.items():
      if (nodeId != myNodeId) and (nodeId < nodeCount):
        self.senders[nodeId] = connections.sender(hostAndPort)

    # Setup the timers used to keep Raft elections working.
    self.leaderTimeout     = customTimer.customTimer(self.leaderHasTimedout) # Does not repeat
    self.leaderHeartbeat   = customTimer.customTimer(self.sendOutLeaderHeartbeat, heartbeatInterval)
    self.electionHeartbeat = customTimer.customTimer(self.sendOutElectionHeartbeat, heartbeatInterval)

    # Reload the log from a file
    self.loadLog()

    # Start the leader timeout by forcing a heartbeat.
    self.heartbeat()

    # Wait for user input.
    while True:
      print('What would you like to do?')
      print('  1. Timeout')
      print('  2. Stop Heartbeat')
      print('  3. Show Info')
      print('  4. Show Log')
      print('  5. Add Test Entries')
      print('  6. Exit')

      try:
        choice = int(input('Enter your choice: '))
      except:
        print('Invalid choice. Try again.')
        continue

      if choice == 1:
        self.setAsCandidate()
      elif choice == 2:
        self.leaderHeartbeat.stop()
      elif choice == 3:
        self.showInfo()
      elif choice == 4:
        self.showLog()
      elif choice == 5:
        self.addTestEntries()
      elif choice == 6:
        break
      else:
        print('Invalid choice "%s". Try again.' % (choice))

    # Socket closed so clean up and shut down
    print('Closing...')
    for sender in self.senders.values():
      sender.close()
    self.listener.close()
    self.leaderTimeout.close()
    self.leaderHeartbeat.close()
    self.electionHeartbeat.close()


if __name__ == '__main__':
  mainObject().main()
