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
    self.__onTimedOut = onTimedOut
    self.__doneTime = None
    self.__keepAlive = True
    threading.Thread(target=self.__run).start()


  def __run(self):
    # Periodically check if the time is done.
    while self.__keepAlive:
      if self.__doneTime:
        now = time.time()
        if now > self.__doneTime:
          self.__doneTime = None
          self.__onTimedOut()
      time.sleep(checkTimeoutTime)


  def addTime(self, duration):
    # Adds the duration in seconds. If the time is up this will start
    # a new timeout. If timeout has happened yet, this will increase the timeout.
    if not self.__doneTime:
      self.__doneTime = time.time() + duration
    else:
      self.__doneTime += duration


  def stop(self):
    # Stops the current timeout without closing the whole timer thread.
    self.__doneTime = None


  def close(self):
    # Stops the timeout and closes the timer thread.
    self.__keepAlive = False
