#!/usr/bin/env python2

import threading
import time

class channelThread (threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
  def run(self):
    global timeToDie
    while not timeToDie:
      print("Bump")
      time.sleep(2)

class userInputThread (threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
  def run(self):
    global timeToDie
    while 1:
      print("What would you like to do?")
      print("   1. Say Hello")
      print("   2. Say Goodbye")
      print("   3. Exit")
      choice = input("Enter your choice: ")
      if choice == 1:
        print("Hello")
      elif choice == 2:
        print("Goodbye")
      elif choice == 3:
        # Stop other thread
        timeToDie = True
        break
      else:
        print("Unknown choice \"{}\". Try again.".format(choice))

# Create new threads
timeToDie = False
thread1 = channelThread()
thread2 = userInputThread()

# Start new Threads
thread1.start()
thread2.start()

# Wait until all threads are done
thread1.join()
thread2.join()
print("Quitting")
