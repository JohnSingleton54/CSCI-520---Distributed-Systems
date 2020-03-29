#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)
# due Apr 6, 2020 by 11:59 PM


import threading
import time


checkTimeoutTime = 0.025 # in seconds


class customTimer:
  # This is a timer which can be bumped to run longer.

  def __init__(self, onTimedOut):
    self.onTimedOut = onTimedOut
    self.doneTime = None
    self.keepAlive = True
    threading.Thread(target=self.__run).start()


  def __run(self):
    # Periodically check if the time is done.
    while self.keepAlive:
      if self.doneTime:
        now = time.time()
        if now > self.doneTime:
          self.doneTime = None
          self.onTimedOut()
      time.sleep(checkTimeoutTime)


  def addTime(self, duration):
    # Adds the duration in seconds. If the time is up this will start
    # a new timeout. If timeout has happened yet, this will increase the timeout.
    if not self.doneTime:
      self.doneTime = time.time() + duration
    else:
      self.doneTime += duration


  def stop(self):
    # Stops the current timeout without closing the whole timer thread.
    self.doneTime = None


  def close(self):
    # Stops the timeout and closes the timer thread.
    self.keepAlive = False
