#!/usr/bin/env python

class appointment:
  def __init__(self, name, day, start_time, end_time, participants):
    self.name = name
    self.day = day
    self.start_time = start_time
    self.end_time = end_time
    self.participants = participants

  def overlap(self, other):
    if self.day != other.day:
      return False
    # TODO Finish
    return True
