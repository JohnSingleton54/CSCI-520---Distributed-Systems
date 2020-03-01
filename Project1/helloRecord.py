#!/usr/bin/env python2

# Example usage:
# - In console 1 call "python ./helloRecord.py 1"
# - In console 2 call "python ./helloRecord.py 2"
# - (optional) In console 3 call "python ./helloRecord.py 3"

import threading
import sys

import connections


hostsAndPorts = {
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


def main(myNum):
  listener = connections.listener(recordMessage, hostsAndPorts[myNum])

  talkers = []
  for num, hostAndPort in hostsAndPorts.items():
    if num != myNum:
      talker = connections.talker(hostAndPort)
      talkers.append(talker)

  while 1:
    print("What would you like to do?")
    print("   1. Send Message")
    print("   2. Show Received Messages")
    print("   3. Exit")
    choice = int(input("Enter your choice: "))
    if choice == 1:
      msg = input("Enter Message: ")
      for talker in talkers:
        talker.send(msg)
      print()

    elif choice == 2:
      print("Messages:")
      recordLock.acquire()
      for msg in record:
        print("  "+msg)
      recordLock.release()
      print()

    elif choice == 3:
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
