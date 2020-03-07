#!/usr/bin/env python

import threading
import json


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
    elif not list(set(self.participants) and set(other.participants)):
      return False
    return True


  # Compare by day and start_time. If times match, then check unique names.
  def laterTime(self, other):
    return self.day > other.day or (self.day == other.day and self.start_time > other.start_time) or \
       (self.day == other.day and self.start_time == other.start_time and self.name > other.name)


  def toString(self):
    conflict = ", lost to %s"%(self.conflictName) if self.conflictName else ""
    return "%s, %s %s-%s, %s%s" % (self.name, self.day, self.start_time, self.end_time, self.participants, conflict)


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

    # TODO: John, we should discuss this and probably come up with a better method.
    # Find all conflicts, if there are conflicts the latest time will win, the older is in conflict.
    for i in range(len(self.__appointments)-1, -1, -1):
      newer = self.__appointments[i]
      if not newer.conflictName:
        for j in range(i-1, -1, -1):
          older = self.__appointments[j]
          if not older.conflictName:
            if newer.isConflicting(older):
              older.conflictName = newer.name


  def hasAppointment(self, name):
    with self.__lockCal:
      return self.__findByName(name) != None


  def insert(self, name, day, start_time, end_time, participants):
    with self.__lockCal:
      appt = appointment(name, day, start_time, end_time, participants)

      # Insert sort new appointment by day and start_time
      found = False
      for i in range(len(self.__appointments)-1, -1, -1):
        if self.__appointments[i].lateTime(appt):
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


  def __readAppointmentsFromFile(self):
    try:
      f = open("calendar%d.txt"%self.__nodeId, "r")
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

    f = open("calendar%d.txt"%self.__nodeId, "w")
    f.write(msg)
    f.close()

