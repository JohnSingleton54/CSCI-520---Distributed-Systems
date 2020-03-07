#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 1 (Replicated Log Project)
# due M 3/9/2020 by 11:59 PM

# Example usage:
# - In console 1 call "python ./main.py 0 2"
# - In console 2 call "python ./main.py 1 2"

import threading
import sys
import time

import connections
import ourCalendar
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
reloadFromFiles = True


myNodeId = int(sys.argv[1])
print("My Node Id is %d" % (myNodeId))

nodeCount = int(sys.argv[2])
print("The Node Count is %d" % (nodeCount))


class mainLoopObject:
  def __init__(self):
    self.timeToDie = False
    self.sendMessages = True

    # Create shared calendar and distributed log.
    self.cal = ourCalendar.calendar(myNodeId, reloadFromFiles)
    self.log = distributedLog.distributedLog(self.cal, myNodeId, nodeCount, reloadFromFiles)

    # Setup the listener to start watching for incoming messages.
    self.listener = connections.listener(self.log.receiveMessage, nodeIdToHostsAndPorts[myNodeId], useMyHost)

    # Setup the collection of connections to talk to the other instances.
    self.senders = []
    self.senderIDs = []
    for nodeId, hostAndPort in nodeIdToHostsAndPorts.items():
      if (nodeId != myNodeId) and (nodeId < nodeCount):
        sender = connections.sender(hostAndPort)
        self.senders.append(sender)
        self.senderIDs.append(nodeId)

    self.shareLogThread = threading.Thread(target=self.shareLog)
    self.shareLogThread.start()


  def shareLog(self):
    # This is run in a thread to periodically update other threads
    # with this node's log and time table.
    while not self.timeToDie:
      if self.sendMessages:
        for i in range(len(self.senders)):
          nodeId = self.senderIDs[i]
          msg = self.log.getSendMessage(nodeId)
          if msg:
            self.senders[i].send(msg)
      time.sleep(5)


  def insertNewAppointment(self):
    name = raw_input("Enter Name: ")

    day          = int(raw_input("Enter Day (1-7): "))
    start_parts  = raw_input("Enter Start Time (e.g., '13:30'): ").split(':')
    hours        = int(start_parts[0])
    minutes      = int(start_parts[1])
    start_time   = hours + minutes / 60.0
    end_parts    = raw_input("Enter End Time (e.g., '14:30'): ").split(':')
    hours        = int(end_parts[0])
    minutes      = int(end_parts[1])
    end_time     = hours + minutes / 60.0
    part_parts   = raw_input("Enter Participants (e.g., '0 1 3'): ").split(' ')
    participants = [int(participant) for participant in part_parts]

    self.log.insert(name, day, start_time, end_time, participants)


  def deleteAppointment(self):
    name = raw_input("Enter Name: ")
    appt = self.cal.getAppointment(name)
    if appt != None:
      if myNodeId in appt.participants:
        self.log.delete(name)
      else:
        print("You may not delete a appointment that you are not participating in.")
    else:
      print("No appointment by that name was found.")


  def showAllAppointments(self):
    print("Appointments:")
    appts = self.cal.toString()
    if appts:
      print("  "+appts)
    else:
      print("  <None>")


  def showTimeTable(self):
    print("TimeTable:")
    print("  "+self.log.timeTableToString())


  def showLogs(self):
    print("Logs:")
    logs = self.log.logsToString()
    if logs:
      print("  "+logs)
    else:
      print("  <None>")


  def toggleSendingMessages(self):
    self.sendMessages = not self.sendMessages


  def showMessage(self):
    nodeId = int(raw_input("Enter Node Id: "))
    msg = self.log.getSendMessage(nodeId)
    if msg:
      print("  "+msg)
    else:
      print("  <None>")


  def close(self):
    print("Closing")
    self.timeToDie = True
    for sender in self.senders:
      sender.close()
    self.listener.close()
    self.shareLogThread.join()


  def run(self):
    # Start main loop and wait for user input.
    # while the listeners and senders keep running in their own threads.
    while not self.timeToDie:
      print("")
      print("What would you like to do?")
      print("  1. Insert Appointment")
      print("  2. Delete Appointment")
      print("  3. Show All Appointments")
      print("  4. Show Time Table")
      print("  5. Show Logs")
      if self.sendMessages:
        print("  6. Stop Sending Messages")
      else:
        print("  6. Start Sending Messages")
      print("  7. Show Message")
      print("  8. Exit")

      try:
        choice = int(raw_input("Enter your choice: "))
      except:
        print("Invalid choice. Try again.")
        continue

      try:
        if   choice == 1:
          self.insertNewAppointment()
        elif choice == 2:
          self.deleteAppointment()
        elif choice == 3:
          self.showAllAppointments()
        elif choice == 4:
          self.showTimeTable()
        elif choice == 5:
          self.showLogs()
        elif choice == 6:
          self.toggleSendingMessages()
        elif choice == 7:
          self.showMessage()
        elif choice == 8:
          self.close()
        else:
          print("Invalid choice \"%s\". Try again." % (choice))
      except:
        print("Invalid input. Try again")


if __name__ == "__main__":
  mainLoopObject().run()
