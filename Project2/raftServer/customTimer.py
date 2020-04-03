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
    self.__lock = threading.Lock()
    threading.Thread(target=self.__run).start()


  def __run(self):
    # Periodically check if the time is done.
    while self.__keepAlive:
      timedOut = False
      with self.__lock:
        if self.__doneTime:
          now = time.time()
          if now > self.__doneTime:
            self.__doneTime = None
            timedOut = True
      if timedOut:
        self.__onTimedOut()
      time.sleep(checkTimeoutTime)


  def setTime(self, duration):
    # Sets the duration in seconds.
    with self.__lock:
      now = time.time()
      self.__doneTime = now + duration


  def addTime(self, duration, maximum = None):
    # Adds the duration in seconds. If the time is up this will start
    # a new timeout. If timeout has happened yet, this will increase the timeout.
    with self.__lock:
      now = time.time()
      if not self.__doneTime:
        self.__doneTime = now + duration
      else:
        self.__doneTime += duration
      if maximum:
        self.__doneTime = min(self.__doneTime-now, maximum) + now


  def timeLeft(self):
    # Gets the amount of time left before the time out.
    with self.__lock:
      if not self.__doneTime:
        return -1.0
      return self.__doneTime-time.time()


  def stop(self):
    # Stops the current timeout without closing the whole timer thread.
    self.__doneTime = None


  def close(self):
    # Stops the timeout and closes the timer thread.
    self.__keepAlive = False
