#!/usr/bin/env python2

# links:
# https://www.tutorialspoint.com/python/python_multithreading.htm
# https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
# https://pypi.org/project/multitasking/

import threading
import time
import socket
import sys

timeToDie = False
lock = threading.Lock()

def criticalPrint(text):
  global lock
  lock.acquire()
  print(text)
  lock.release()

class incomingSocketThread (threading.Thread):
  def __init__(self, host, port):
    threading.Thread.__init__(self)
    self.host = host
    self.port = port
  def run(self):
    global timeToDie
    criticalPrint("Listening to %s %s"%(self.host, self.port))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((self.host, self.port))
    criticalPrint("About to Listen")
    s.listen(0)
    criticalPrint("About to Accept")
    conn, addr = s.accept()
    criticalPrint("Accepted")
    while not timeToDie:
      data = conn.recv(1024)
      if data:
        criticalPrint("%s says %s"%(addr, data.decode()))
      time.sleep(1)
    criticalPrint("Closing Listener")
    conn.close()

class outgoingSocketThread (threading.Thread):
  def __init__(self, host, port):
    threading.Thread.__init__(self)
    self.host = host
    self.port = port
  def run(self):
    global timeToDie
    criticalPrint("Talking out to %s %s"%(self.host, self.port))
    connected = False
    while (not connected) and (not timeToDie):
      criticalPrint("Trying to Connect")
      try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        criticalPrint("Connected")
        connected = True
        while not timeToDie:
          criticalPrint("Sending Bump")
          s.sendall('Bump')
          time.sleep(5)
        criticalPrint("Closing Talker")
        s.close()
      except Exception as e:
        criticalPrint("Failed to Connect, Retrying in 2 secs")
        time.sleep(2) # Wait a little bit until the listener is there

class userInputThread (threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
  def run(self):
    global timeToDie
    while 1:
      criticalPrint("What would you like to do?")
      criticalPrint("   1. Say Hello")
      criticalPrint("   2. Say Goodbye")
      criticalPrint("   3. Exit")
      choice = input("Enter your choice: ")
      if choice == 1:
        criticalPrint("Hello")
      elif choice == 2:
        criticalPrint("Goodbye")
      elif choice == 3:
        # Stop other thread
        criticalPrint("TimeToDie")
        timeToDie = True
        break
      else:
        criticalPrint("Unknown choice \"%s\". Try again."%(choice))

def main(args):
  # Create new threads
  threads = [
    incomingSocketThread(args[1], int(args[2])),
    outgoingSocketThread(args[3], int(args[4])),
    userInputThread()
  ]

  # Start new Threads
  for t in threads:
    t.start()

  # Wait until all threads are done
  for t in threads:
    t.join()
  criticalPrint("Quitting")

if __name__ == "__main__":
    main(sys.argv)