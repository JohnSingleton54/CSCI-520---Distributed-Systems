#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 1 (Replicated Log Project)
# due M 3/9/2020 by 11:59 PM

# This file contains the code for adding and storing
# a calender in a way which works with a distributed log.

import threading
import json
import math


dayNumberToName = {
  1: "Sunday",
  2: "Monday",
  3: "Tuesday",
  4: "Wednesday",
  5: "Thursday",
  6: "Friday",
  7: "Saturday",
}


class appointment:
  def __init__(self, name, day, start_time, end_time, participants):
    self.name = name
    self.day = day
    self.start_time = start_time
    self.end_time = end_time
    self.participants = participants
    self.conflictName = ""


  def isConflicting(self, other):
    # Appointments do not span multiple days, so if the days do not match then there is no conflict.
    if self.day != other.day:
      return False
    # We only get to the following statement if self.day == other.day.
    elif self.start_time >= other.end_time or self.end_time <= other.start_time:
      return False
    # If the two appointments do not share any participants, then there is no conflict.
    elif not list(set(self.participants) & set(other.participants)):
      return False
    return True


  # Compare by day and start_time. If times match, then check unique names.
  def laterTime(self, other):
    # Sort by first day, then start time, then end time, the tie break same times with name
    return self.day > other.day or \
       (self.day == other.day and self.start_time > other.start_time) or \
       (self.day == other.day and self.start_time == other.start_time and self.end_time > other.end_time) or \
       (self.day == other.day and self.start_time == other.start_time and self.end_time == other.end_time and self.name > other.name)


  def toString(self):
    conflict = ", lost to %s"%(self.conflictName) if self.conflictName else ""
    dayName = dayNumberToName[self.day]

    hours = math.trunc(self.start_time)
    minutes  = math.trunc((self.start_time - hours)*60)
    startTime = "%d:%02d"%(hours, minutes)

    hours = math.trunc(self.end_time)
    minutes  = math.trunc((self.end_time - hours)*60)
    endTime = "%d:%02d"%(hours, minutes)

    return "%s, %s %s-%s, %s%s" % (self.name, dayName, startTime, endTime, self.participants, conflict)


  def toTuple(self):
    # This is used when "dumping" the JSON
    return [self.name, self.day, self.start_time, self.end_time, self.participants]


class calendar:
  def __init__(self, nodeId, loadFile):
    self.__nodeId = nodeId
    self.__appointments = []
    self.__lockCal = threading.Lock()

    if loadFile:
      self.__readAppointmentsFromFile()

 
  def __findByName(self, name):
    for appt in self.__appointments:
      if appt.name == name:
        return appt
    return None

  
  def __updateConflicts(self):
    # First reset all conflicts to False.
    for appt in self.__appointments:
      appt.conflictName = ""
    
    def getName(appt):
      return appt.name

    apptByName = self.__appointments[:]
    apptByName.sort(key = getName)

    # Find all conflicts sorted by name (unique arbitrary),
    # if there are conflicts the first name will win, the second is in conflict.
    # Only conflicts if overlapping times and participants.
    for i in range(len(apptByName)-1, -1, -1):
      first = apptByName[i]
      if not first.conflictName:
        for j in range(i-1, -1, -1):
          second = apptByName[j]
          if not second.conflictName:
            if first.isConflicting(second):
              second.conflictName = first.name


  def getAppointment(self, name):
    with self.__lockCal:
      return self.__findByName(name)


  def insert(self, name, day, start_time, end_time, participants):
    with self.__lockCal:
      appt = appointment(name, day, start_time, end_time, participants)

      # Insert sort new appointment by day and start_time
      found = False
      for i in range(len(self.__appointments)-1, -1, -1):
        if not self.__appointments[i].laterTime(appt):
          self.__appointments.insert(i+1, appt)
          found = True
          break
      if not found:
        self.__appointments.insert(0, appt)

      self.__updateConflicts()
      self.__writeAppointmentsToFile()


  def delete(self, apptName):
    with self.__lockCal:
      appt = self.__findByName(apptName)
      if appt:
        self.__appointments.remove(appt)
        self.__updateConflicts()
        self.__writeAppointmentsToFile()
      else:
        print("Warning: didn't find appointment \"%s\""%(apptName))


  def toString(self):
    parts = []
    with self.__lockCal:
      for appt in self.__appointments:
        parts.append(appt.toString())
    return "\n  ".join(parts)


  def __getAppointmentsFileName(self):
    return "calendar%d.json"%self.__nodeId


  def __readAppointmentsFromFile(self):
    try:
      f = open(self.__getAppointmentsFileName(), "r")
      msg = f.read()
      f.close()

      if msg:
        data = json.loads(msg)
        for entry in data:
          self.insert(entry.name, entry.day, entry.start_time, entry.end_time, entry.participants)
    except Exception as e:
      print("Failed to load from calendar file: %s"%(e))


  def __writeAppointmentsToFile(self):
    tuples = []
    for appt in self.__appointments:
      tuples.append(appt.toTuple())
    msg = json.dumps(tuples)

    f = open(self.__getAppointmentsFileName(), "w")
    f.write(msg)
    f.close()

