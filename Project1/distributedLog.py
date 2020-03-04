#!/usr/bin/env python

import json
import threading

import sharedCalendar


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
  def __init__(self, calendar, nodeId, nodeCount):
    self.nodeId = nodeId
    self.nodeCount = nodeCount
    self.timeTable = []
    for i in range(nodeCount):
      self.timeTable.append([0] * nodeCount)
    self.log = []
    self.calendar = calendar
    self.lock = threading.Lock()


  def __getClock(self):
    return self.timeTable[self.nodeId][self.nodeId]


  def __incClock(self):
    self.timeTable[self.nodeId][self.nodeId] += 1


  def __hasRec(self, eR, k):
    # Checks the time table to determine if the given record is known by k.
    # hasrec(Ti, eR, k) = Ti[k, eR.node] >= eR.time
    return self.timeTable[k][eR.nodeId] >= eR.time


  def __allHasRec(self, eR):
    # This is for handling "(all j in [n]) not hasrec(Ti, eR, j)}" as part of __trimLogs.
    # This will return true if everyone knows about this record, false if one or more don't know about it.
    for j in range(self.nodeCount):
      if not self.__hasRec(eR, j):
        return False
    return True


  def insert(self, name, day, start_time, end_time, participants):
    self.lock.acquire()
    self.__oper(InsertOpType, [name, day, start_time, end_time, participants])
    self.lock.release()


  def delete(self, name):
    self.lock.acquire()
    self.__oper(DeleteOpType, [name])
    self.lock.release()


  def __oper(self, opType, opArgs):
    # Ti[i, i] := clock
    self.__incClock()
    r = record(self.__getClock(), self.nodeId, opType, opArgs)
    # Li = Li union {<"oper(p)", Ti[i,i], i>}
    self.log.append(r)
    # perform the operation oper(p)
    self.__perform(r)


  def __addTempLog(self, newLogs, eR):
    # check that we do NOT add the insert item and deletion at the same time
    if eR.opType == DeleteOpType:
      for log in newLogs:
        if log.opArgs[0] == eR.opArgs[0]:
          newLogs.remove(log)
          return newLogs

    newLogs.append(eR)
    return newLogs


  def getSendMessage(self, k):
    self.lock.acquire()
    # NP := {eR|eR in Li and not hasRec(Ti, eR, k)}
    newLogs = []
    for eR in self.log:
      if not self.__hasRec(eR, k):
        newLogs = self.__addTempLog(newLogs, eR)

    # so we can use json we need to get the new logs as a tuples
    newTuples = []
    for log in newLogs:
      newTuples.append(log.toTuple())

    # send the mssage <NP, Ti> to Nk
    msg = [self.nodeId, newTuples, self.timeTable]
    self.lock.release()
    return json.dumps(msg)


  def receiveMessage(self, message):
    self.lock.acquire()
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
      opType = str(nl[2])
      opArgs = nl[3]
      r = record(time, nodeId, opType, opArgs)
      if not self.__hasRec(r, self.nodeId):
        self.log.append(r)
        newRecords.append(r)
    # update the time with the message's time table
    self.__updateTimeTable(otherTimeTable, otherNodeId)
    # remove all logs which everyone knows about
    self.__trimLogs()
    # apply all new records
    for r in newRecords:
      self.__perform(r)
    self.lock.release()


  def __updateTimeTable(self, otherTimeTable, otherNodeId):
    # (all x in [n]) do Ti[i, x] := max{Ti[i, x], Tk[k, x]}
    for x in range(self.nodeCount):
      self.timeTable[self.nodeId][x] = max(self.timeTable[self.nodeId][x], otherTimeTable[otherNodeId][x])
    # (all x in [n])(all y in [n]) do Ti[x, y] = max(Ti[x, y], Tk[x, y])
    for x in range(self.nodeCount):
      for y in range(self.nodeCount):
        self.timeTable[x][y] = max(self.timeTable[x][y], otherTimeTable[x][y])


  def __trimLogs(self):
    # PLi := {eR|eR in (PLi union NE) and (all j in [n]) not hasrec(Ti, eR, j)}
    newLog = []
    for r in self.log:
      if not self.__allHasRec(r):
        newLog.append(r)
    self.log = newLog


  def __perform(self, r):
    if r.opType == InsertOpType:
      self.calendar.insert(r.opArgs[0], r.opArgs[1], r.opArgs[2], r.opArgs[3], r.opArgs[4])
    else:
      self.calendar.delete(r.opArgs[0])


  def logsToString(self):
    self.lock.acquire()
    parts = []
    for r in self.log:
      parts.append(r.toString())
    self.lock.release()
    return "\n  ".join(parts)


  def timeTableToString(self):
    self.lock.acquire()
    result = str(self.timeTable)
    self.lock.release()
    return result
