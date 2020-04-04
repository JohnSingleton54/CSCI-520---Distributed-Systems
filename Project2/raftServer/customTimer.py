#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)
# due Apr 6, 2020 by 11:59 PM


import threading
import time


checkTimeoutTime = 0.01 # in seconds


class customTimer:
  # This is a timer which will a method after a specificed amount of time.

  def __init__(self, onTimedOut, repeatDuration=None):
    # `onTimedOut` is the method to call when the timer has elapsed a duration.
    # `repeatDuration` is the amount of time to automatically reset the timer
    # to after a method call. Set to None to not repeat.
    self.__onTimedOut = onTimedOut
    self.__repeatDur  = repeatDuration
    self.__doneTime   = None
    self.__keepAlive  = True
    self.__lock = threading.Lock()
    threading.Thread(target=self.__run).start()


  def __run(self):
    # Periodically check if the time is done.
    while self.__keepAlive:
      timedOut = False
      with self.__lock:
        if self.__doneTime:
          if time.time() > self.__doneTime:
            self.__doneTime = None
            timedOut = True
            if self.__repeatDur:
              self.__doneTime = time.time() + self.__repeatDur
      if timedOut:
        self.__onTimedOut()
      time.sleep(checkTimeoutTime)


  def timeLeft(self):
    # Gets the amount of time left before the next time the method is called.
    with self.__lock:
      if not self.__doneTime:
        return -1.0
      return self.__doneTime-time.time()


  def start(self, duration):
    # Starts the timer to run the given amount of duration before it calls the method.
    with self.__lock:
      now = time.time()
      self.__doneTime = now + duration


  def stop(self):
    # Stops the current timeout without closing the whole timer thread.
    self.__doneTime = None


  def close(self):
    # Stops the timeout and closes the timer thread.
    self.__keepAlive = False
