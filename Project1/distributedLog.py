#!/usr/bin/env python

import json


InsertOpType = "Insert"
DeleteOpType = "Delete"


class record:
  def __init__(self, time, nodeId, opType, opArgs):
    self.time = time
    self.nodeId = nodeId
    self.opType = opType
    self.opArgs = opArgs

  def toString(self):
    return "%d, %d, %s, %s"%(self.time, self.nodeId, self.opType, self.opArgs)
  
  def toTuple(self):
    # This is used when "dumping" the JSON
    return [self.time, self.nodeId, self.opType, self.opArgs]


class distributedLog:
  def __init__(self, nodeId, nodeCount):
    self.nodeId = nodeId
    self.nodeCount = nodeCount
    self.timeTable = []
    for i in range(nodeCount):
      self.timeTable.append([0] * nodeCount)
    self.log = []

  def getClock(self):
    return self.timeTable[self.nodeId][self.nodeId]

  def incClock(self):
    self.timeTable[self.nodeId][self.nodeId] += 1

  def hasRec(self, k, eR):
    # Checks the time table to determine if the given record is known by k.
    # hasrec(Ti, eR, k) = Ti[k, eR.node] >= eR.time
    return self.timeTable[k][eR.nodeId] >= eR.time

  def insert(self, name, day, start_time, end_time, participants):
    self.__oper(InsertOpType, [name, day, start_time, end_time, participants])

  def delete(self, name):
    self.__oper(DeleteOpType, [name])

  def __oper(self, opType, opArgs):
    # Ti[i, i] := clock
    self.incClock()
    r = record(self.getClock(), self.nodeId, opType, opArgs)
    # Li = Li union {<"oper(p)", Ti[i,i], i>}
    self.log.append(r)
    # perform the operation oper(p)
    self.perform(r)

  def getSendMessage(self, k):
    # NP := {eR|eR in Li and not hasRec(Ti, eR, k)}
    newLogs = []
    for eR in self.log:
      if not self.hasRec(k, eR):
        newLogs.append(eR.toTuple())
    # send the mssage <NP, Ti> to Nk
    msg = [self.nodeId, newLogs, self.timeTable]
    return json.dumps(msg)
    
  def receiveMessage(self, message):
    # Decode the message from a string
    # let m = <NPk, Tk>
    data = json.loads(message)
    otherNodeId = data[0]
    otherTimeTable = data[2]
    newRecords = []
    # Li := Li union NPk
    for nl in data[1]:
      time = int(nl[0])
      nodeId = int(nl[1])
      opType = nl[2].encode('ascii')
      opArgs = nl[3]
      r = record(time, nodeId, opType, opArgs)
      if not self.hasRec(self.nodeId, r):
        self.log.append(r)
        newRecords.append(r)
    # (all x in [n]) do Ti[i, x] := max{Ti[i, x], Tk[k, x]}
    for x in range(self.nodeCount):
      self.timeTable[self.nodeId][x] = max(self.timeTable[self.nodeId][x], otherTimeTable[otherNodeId][x])
    # (all x in [n])(all y in [n]) do Ti[x, y] = max(Ti[x, y], Tk[x, y])
    for x in range(self.nodeCount):
      for y in range(self.nodeCount):
        self.timeTable[x][y] = max(self.timeTable[x][y], otherTimeTable[x][y])
    # remove all logs which everyone knows about
    self.trimLogs()
    # apply all new records
    for r in newRecords:
      self.perform(r)
 
  def trimLogs():
    # PLi := {eR|eR in (PLi union NE) and (all j in [n]) not hasrec(Ti, eR, j)}

    
    # TODO: Implement
    pass

  def perform(self, r):
    print("Perform: %s, %s"%(r.opType, r.opArgs))
    # TODO: Implement
    pass

  def printLogs(self):
    for r in self.log:
      print(r.toString())



#### Just for testing
# log0 = distributedLog(0, 3)
# log0.insert("Meeting", "Mon", "12:00", "13:00", [0, 1])
# log0.insert("Meetup", "Tues", "13:00", "14:00", [0, 1])
# log0.delete("Meetup")
# msg = log0.getSendMessage(1)

# print("========================")
# print(msg)
# print("========================")

# log1 = distributedLog(1, 3)
# log1.receiveMessage(msg)
# log1.printLogs()
