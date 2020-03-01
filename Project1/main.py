#!/usr/bin/env python2.7

# Example usage:
# - In console 1 call "python ./main.py 1"
# - In console 2 call "python ./main.py 2"
# - (optional) In console 3 call "python ./main.py 3"

import threading
import sys

import connections


useMyHost = True
nodeIdToHostsAndPorts = {
  1: "127.0.0.1:8080",
  2: "127.0.0.1:8181",
  3: "127.0.0.1:8282",
}


record = []
recordLock = threading.Lock()
def recordMessage(message):
  recordLock.acquire()
  record.append(message)
  recordLock.release()


def main(myNodeId):
  global useMyHost
  global nodeIdToHostsAndPorts

  print("My Node Id is %d" % (myNodeId))

  # Setup the connection to listen to
  listener = connections.listener(recordMessage, nodeIdToHostsAndPorts[myNodeId], useMyHost)

  # Setup the collection of connections to talk to the other instances
  talkers = []
  for nodeId, hostAndPort in nodeIdToHostsAndPorts.items():
    if nodeId != myNodeId:
      talker = connections.talker(hostAndPort)
      talkers.append(talker)

  # Start main loop and wait for user input
  # while the listeners and talkers keep running in their own threads.
  while 1:
    print("What would you like to do?")
    print("   1. Send Message")
    print("   2. Show Received Messages")
    print("   3. Exit")
    choice = int(raw_input("Enter your choice: "))

    if choice == 1: # Send Message
      msg = raw_input("Enter Message: ")
      for talker in talkers:
        talker.send(msg)
      print("")

    elif choice == 2: # Show Received Messages
      print("Messages:")
      recordLock.acquire()
      for msg in record:
        print("  %s"%(msg))
      recordLock.release()
      print("")

    elif choice == 3: # Exit
      print("Closing")
      for talker in talkers:
        talker.close()
      listener.close()
      break

    else:
      print("Unknown choice \"%s\". Try again." % (choice))


if __name__ == "__main__":
  myNum = int(sys.argv[1])
  main(myNum)
