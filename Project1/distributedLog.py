#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 1 (Replicated Log Project)
# due M 3/9/2020 by 11:59 PM

# This file contains the code for using a distributed log as defined by
# Gene Wuu and Arthur Bernstein,
# "Review of Efficient Solutions to the Replicated Log and Dictionary Problems"

import json
import threading

import ourCalendar


InsertOpType = "Insert"
DeleteOpType = "Delete"


class record:
  def __init__(self, time, nodeId, opType, opArgs):
    self.time = time
    self.nodeId = nodeId
    self.opType = opType
    self.opArgs = opArgs

  def toString(self):
    if self.opType == InsertOpType:
      return "Insert: time=%d, nodeId=%d, name=%s, day=%s, start_time=%s, end_time=%s, participants=%s"%(self.time,
        self.nodeId, self.opArgs[0], self.opArgs[1], self.opArgs[2], self.opArgs[3], self.opArgs[4])
    else:
      return "Delete: time=%d, nodeId=%d, name=%s"%(self.time, self.nodeId, self.opArgs[0])


  def toTuple(self):
    # This is used when "dumping" the JSON
    return [self.time, self.nodeId, self.opType, self.opArgs]


class distributedLog:
  def __init__(self, calendar, nodeId, nodeCount, loadFile):
    self.__calendar = calendar
    self.__nodeId = nodeId
    self.__nodeCount = nodeCount
    self.__log = []
    self.__lockLog = threading.Lock()

    self.__timeTable = []
    for i in range(nodeCount):
      self.__timeTable.append([0] * nodeCount)
    
    if loadFile:
      self.__readLogsFromFile()


  def __getClock(self):
    return self.__timeTable[self.__nodeId][self.__nodeId]


  def __incClock(self):
    self.__timeTable[self.__nodeId][self.__nodeId] += 1


  def __hasRec(self, eR, k):
    # Checks the time table to determine if the given record is known by k.
    # hasrec(Ti, eR, k) = Ti[k, eR.node] >= eR.time
    return self.__timeTable[k][eR.nodeId] >= eR.time


  def __allHasRec(self, eR):
    # This is for handling "(all j in [n]) not hasrec(Ti, eR, j)}" as part of __trimLogs.
    # This will return true if everyone knows about this record, false if one or more don't know about it.
    for j in range(self.__nodeCount):
      if not self.__hasRec(eR, j):
        return False
    return True


  def insert(self, name, day, start_time, end_time, participants):
    with self.__lockLog:
      self.__oper(InsertOpType, [name, day, start_time, end_time, participants])


  def delete(self, name):
    with self.__lockLog:
      self.__oper(DeleteOpType, [name])


  def __oper(self, opType, opArgs):
    # Ti[i, i] := clock
    self.__incClock()
    r = record(self.__getClock(), self.__nodeId, opType, opArgs)

    # Li = Li union {<"oper(p)", Ti[i,i], i>}
    self.__log.append(r)

    # perform the operation oper(p)
    self.__perform(r)

    # both the log and clock changed so rewrite the log file
    self.__writeLogsToFile()


  def __addTempLog(self, newLogs, eR):
    # check that we do NOT add the insert item and deletion at the same time
    # if a log with the same name exists already we can assume it is an insert and deletion
    for log in newLogs:
      if log.opArgs[0] == eR.opArgs[0]:
        newLogs.remove(log)
        return newLogs

    newLogs.append(eR)
    return newLogs


  def getSendMessage(self, k):
    with self.__lockLog:
      # NP := {eR|eR in Li and not hasRec(Ti, eR, k)}
      newLogs = []
      for eR in self.__log:
        if not self.__hasRec(eR, k):
          newLogs = self.__addTempLog(newLogs, eR)

      # so we can use json we need to get the new logs as a tuples
      newTuples = []
      for log in newLogs:
        newTuples.append(log.toTuple())

      # send the mssage <NP, Ti> to Nk
      msg = [self.__nodeId, newTuples, self.__timeTable]
    return json.dumps(msg)


  def receiveMessage(self, message):
    with self.__lockLog:
      # Decode the message from a string
      # let m = <NPk, Tk>
      data = json.loads(message)
      otherNodeId = data[0]
      otherTimeTable = data[2]
      newRecords = []
      logChanged = False

      # Li := Li union NPk
      for logTuple in data[1]:
        time = int(logTuple[0])
        nodeId = int(logTuple[1])
        opType = str(logTuple[2])
        opArgs = logTuple[3]
        r = record(time, nodeId, opType, opArgs)
        if not self.__hasRec(r, self.__nodeId):
          self.__log.append(r)
          newRecords.append(r)
          logChanged = True

      # update the time with the message's time table
      timeChanged = self.__updateTimeTable(otherTimeTable, otherNodeId)

      # remove all logs which everyone knows about
      logChanged = self.__trimLogs() or logChanged

      # if the log or time has changed, rewrite the file for the log
      if logChanged or timeChanged:
        self.__writeLogsToFile()

      # apply all new records
      for r in newRecords:
        self.__perform(r)


  def __updateTimeTable(self, otherTimeTable, otherNodeId):
    changed = False
    # (all x in [n]) do Ti[i, x] := max{Ti[i, x], Tk[k, x]}
    for x in range(self.__nodeCount):
      if otherTimeTable[otherNodeId][x] > self.__timeTable[self.__nodeId][x]:
        self.__timeTable[self.__nodeId][x] = otherTimeTable[otherNodeId][x]
        changed = True
    
    # (all x in [n])(all y in [n]) do Ti[x, y] = max(Ti[x, y], Tk[x, y])
    for x in range(self.__nodeCount):
      for y in range(self.__nodeCount):
        if otherTimeTable[x][y] > self.__timeTable[x][y]:
          self.__timeTable[x][y] = otherTimeTable[x][y]
          changed = True
    
    return changed


  def __trimLogs(self):
    # PLi := {eR|eR in (PLi union NE) and (all j in [n]) not hasrec(Ti, eR, j)}
    newLog = []
    for r in self.__log:
      if not self.__allHasRec(r):
        newLog.append(r)
    changed = len(self.__log) != len(newLog)
    self.__log = newLog
    return changed


  def __perform(self, r):
    if r.opType == InsertOpType:
      self.__calendar.insert(r.opArgs[0], r.opArgs[1], r.opArgs[2], r.opArgs[3], r.opArgs[4])
    else:
      self.__calendar.delete(r.opArgs[0])


  def __getLogsFileName(self):
    return "logs%d.json"%self.__nodeId


  def __readLogsFromFile(self):
    try:
      f = open(self.__getLogsFileName(), "r")
      data = f.read()
      f.close()

      if data:
        self.receiveMessage(data)
    except Exception as e:
      print("Failed to load from log file: %s"%(e))


  def __writeLogsToFile(self):
    tuples = []
    for log in self.__log:
      tuples.append(log.toTuple())
    data = json.dumps([self.__nodeId, tuples, self.__timeTable])

    f = open(self.__getLogsFileName(), "w")
    f.write(data)
    f.close()


  def logsToString(self):
    with self.__lockLog:
      parts = []
      for r in self.__log:
        parts.append(r.toString())
    return "\n  ".join(parts)


  def timeTableToString(self):
    with self.__lockLog:
      return str(self.__timeTable)
