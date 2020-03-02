#!/usr/bin/env python


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
    return "%s, %s, %s, %s, %s, %s" % (self.name, self.day, self.start_time, self.end_time, self.participants, self.conflicted)

class calendar:
  def __init__(self):
    self.entries = []

  def insert(self, name, day, start_time, end_time, participants):
    apt = appointment(name, day, start_time, end_time, participants)
    self.entries.append(apt)
    # TODO Check for conflicts

  def delete(self, aptName):
    for apt in self.entries:
      if apt.name == aptName:
        self.entries.remove(apt)

  def show(self):
    for apt in self.entries:
      print(apt.toString())
