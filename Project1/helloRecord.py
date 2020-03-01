#!/usr/bin/env python2

# Example usage:
# - In console 1 call "python ./helloRecord.py 127.0.0.1 8080 127.0.0.1 8181"
# - In console 2 call "python ./helloRecord.py 127.0.0.1 8181 127.0.0.1 8080"

import threading
import sys

import connections

record = []
recordLock = threading.Lock()
def recordMessage(message):
  recordLock.acquire()
  record.append(message)
  recordLock.release()


def main(args):
  host1 = args[1]
  port1 = int(args[2])
  listener = connections.listener(recordMessage, host1, port1)

  host2 = args[3]
  port2 = int(args[4])
  talker = connections.talker(host2, port2)

  while 1:
    print("What would you like to do?")
    print("   1. Send Message")
    print("   2. Show Received Messages")
    print("   3. Exit")
    choice = int(input("Enter your choice: "))
    if choice == 1:
      msg = input("Enter Message: ")
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
      talker.close()
      listener.close()
      break

    else:
      print("Unknown choice \"%s\". Try again." % (choice))

if __name__ == "__main__":
    main(sys.argv)
