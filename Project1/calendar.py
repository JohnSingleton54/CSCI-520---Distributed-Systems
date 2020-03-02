#!/usr/bin/env python

import threading

class appointment:
  def __init__(self, name, day, start_time, end_time, participants):
    self.name = name
    self.day = day
    self.start_time = start_time
    self.end_time = end_time
    self.participants = participants
    self.conflicted = False

  def overlap(self, other):
    if self.day != other.day:
      return False
    # TODO Finish
    return True

  def toString(self):
    return "%s, %s %s-%s, %s%s" % (self.name, self.day, self.start_time,
      self.end_time, self.participants, ", conflicted" if self.conflicted else "")

class calendar:
  def __init__(self):
    self.entries = []
    self.lock = threading.Lock()

  def insert(self, name, day, start_time, end_time, participants):
    self.lock.acquire()
    apt = appointment(name, day, start_time, end_time, participants)
    self.entries.append(apt)
    self.lock.release()

  def delete(self, aptName):
    self.lock.acquire()
    for apt in self.entries:
      if apt.name == aptName:
        self.entries.remove(apt)
    self.lock.release()

  def toString(self):
    self.lock.acquire()
    parts = []
    for apt in self.entries:
      parts.append(apt.toString())
    self.lock.release()
    return "\n".join(parts)
