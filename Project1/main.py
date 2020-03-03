#!/usr/bin/env python

# Example usage:
# - In console 1 call "python ./main.py 0 2"
# - In console 2 call "python ./main.py 1 2"

import threading
import sys
import time

import connections
import sharedCalendar
import distributedLog


useMyHost = True
nodeIdToHostsAndPorts = {
  0: "127.0.0.1:8080",
  1: "127.0.0.1:8081",
  2: "127.0.0.1:8082",
  3: "127.0.0.1:8083",
  4: "127.0.0.1:8084",
  5: "127.0.0.1:8085",
}


myNodeId = int(sys.argv[1])
print("My Node Id is %d" % (myNodeId))

nodeCount = int(sys.argv[2])
print("The Node Count is %d" % (nodeCount))


class mainLoopObject:
  def __init__(self):
    self.timeToDie = False

    # Create shared calendar and distributed log.
    self.cal = sharedCalendar.calendar()
    self.log = distributedLog.distributedLog(self.cal, myNodeId, nodeCount)

    # Setup the listener to start watching for incoming messages.
    self.listener = connections.listener(self.log.receiveMessage, nodeIdToHostsAndPorts[myNodeId], useMyHost)

    # Setup the collection of connections to talk to the other instances.
    self.talkers = []
    self.talkerIDs = []
    for nodeId, hostAndPort in nodeIdToHostsAndPorts.items():
      if (nodeId != myNodeId) and (nodeId < nodeCount):
        talker = connections.talker(hostAndPort)
        self.talkers.append(talker)
        self.talkerIDs.append(nodeId)

    self.shareLogThread = threading.Thread(target=self.shareLog)
    self.shareLogThread.start()


  def shareLog(self):
    # This is run in a thread to periodically update other threads
    # with this node's log and time table.
    while not self.timeToDie:
      for i in range(len(self.talkers)):
        nodeId = self.talkerIDs[i]
        msg = self.log.getSendMessage(nodeId)
        if msg:
          self.talkers[i].send(msg)
      time.sleep(5)


  def insertNewEntry(self):
    name = raw_input("Enter Name: ")

    # TODO: Get actual input values
    day          = "Mon" #raw_input("Enter Day: ")
    start_time   = "12:00" #raw_input("Enter Start Time: ")
    end_time     = "13:00" #raw_input("Enter End Time: ")
    participants = [myNodeId] #raw_input("Enter Participants: ")

    # TODO: Before appending to log, check for conflicts with local calendar
    self.log.insert(name, day, start_time, end_time, participants)
    print("")


  def deleteEntry(self):
    name = raw_input("Enter Name: ")

    # TODO: Before appending to log, check if that event exists
    self.log.delete(name)
    print("")


  def showAllEvents(self):
    print("Calendar:")
    events = self.cal.toString()
    if events:
      print(events)
    else:
      print("<No events>")
    print("")


  def close(self):
    print("Closing")
    self.timeToDie = True
    for talker in self.talkers:
      talker.close()
    self.listener.close()
    self.shareLogThread.join()


  def run(self):
    # Start main loop and wait for user input
    # while the listeners and talkers keep running in their own threads.
    while not self.timeToDie:
      print("What would you like to do?")
      print("  1. Insert Event")
      print("  2. Delete Event")
      print("  3. Show All Events")
      print("  4. Exit")
      choice = int(raw_input("Enter your choice: "))
      if choice == 1:
        self.insertNewEntry()
      elif choice == 2:
        self.deleteEntry()
      elif choice == 3:
        self.showAllEvents()
      elif choice == 4:
        self.close()
      else:
        print("Unknown choice \"%s\". Try again." % (choice))


if __name__ == "__main__":
  mainLoopObject().run()
