#!/usr/bin/env python

import threading


class appointment:
  def __init__(self, name, day, start_time, end_time, participants):
    self.name = name
    self.day = day
    self.start_time = start_time
    self.end_time = end_time
    self.participants = participants
    self.conflictName = ""


  def isConflicting(self, other):
    if self.day != other.day:
      return False
    # TODO Finish determining if the times overlap,
    #      Also check that at least one participant is in both.
    return True


  def earlierTime(self, other):
    # TODO Finish comparing by day and start_time
    #      If times match then check unique names
    return True


  def toString(self):
    conflict = ", lost to %s"%(self.conflictName) if self.conflictName else ""
    return "%s, %s %s-%s, %s%s" % (self.name, self.day, self.start_time, self.end_time, self.participants, conflict)


class calendar:
  def __init__(self, nodeId):
    self.nodeId = nodeId
    self.appointments = []
    self.lock = threading.Lock()


  def __findByName(self, name):
    for appt in self.appointments:
      if appt.name == name:
        return appt
    return None

  
  def __updateConflicts(self):
    # First reset all conflicts to False.
    for appt in self.appointments:
      appt.conflictName = ""

    # TODO: John, we should discuss this and probably come up with a better method.
    # Find all conflicts, if there are conflicts the latest time will win, the older is in conflict.
    for i in range(len(self.appointments)-1, -1, -1):
      newer = self.appointments[i]
      if not newer.conflictName:
        for j in range(i-1, -1, -1):
          older = self.appointments[j]
          if not older.conflictName:
            if newer.isConflicting(older):
              older.conflictName = newer.name


  def hasAppointment(self, name):
    self.lock.acquire()
    hasAppt = self.__findByName(name) != None
    self.lock.release()
    return hasAppt


  def insert(self, name, day, start_time, end_time, participants):
    self.lock.acquire()
    appt = appointment(name, day, start_time, end_time, participants)

    # Insert sort new appointment by day and start_time
    found = False
    for i in range(len(self.appointments)-1, -1, -1):
      if self.appointments[i].earlierTime(appt):
        self.appointments.insert(i+1, appt)
        found = True
        break
    if not found:
      self.appointments.insert(0, appt)

    self.__updateConflicts()
    self.__writeAppointmentsToFile()
    self.lock.release()


  def delete(self, apptName):
    self.lock.acquire()
    appt = self.__findByName(apptName)
    if appt:
      self.appointments.remove(appt)
      self.__updateConflicts()
      self.__writeAppointmentsToFile()
    else:
      print("Warning: didn't find appointment \"%s\""%(apptName))
    self.lock.release()


  def appointmentsToString(self):
    self.lock.acquire()
    parts = []
    for appt in self.appointments:
      parts.append(appt.toString())
    self.lock.release()
    return "\n  ".join(parts)


  def __writeAppointmentsToFile(self):
    f = open("calendar%d.txt"%self.nodeId, "w")
    for appt in self.appointments:
      f.write(appt.toString()+"\n")
    f.close()

