#!/usr/bin/env python

import Project1.appointment

class calendar:
  def __init__(self):
    entries = []

  def add(self, apt):
    self.entries.append(apt)
    # TODO Check for conflicts

  def remove(self, aptName):
    for apt in self.entries:
      if apt.name == aptName:
        self.entries.remove(apt)

  def show(self):
    # Print something
    pass