#!/usr/bin/env python

# To run the unit-test:
# - In console 1 call "python -m unittest -v"

import unittest

import ourCalendar
import distributedLog


class TestDistributedLogs(unittest.TestCase):

  def test_localOps(self):
    # Checks that we can insert and delete from our local calendar.
    # Checks time table, the log, and the calendar.
    cal = ourCalendar.calendar(0)
    log = distributedLog.distributedLog(cal, 0, 3)
    # self.assertEqual(cal.toString(), "")
    self.assertEqual(log.logsToString(), "jhgf")
    # self.assertEqual(log.timeTableToString(), "[[0, 0, 0], [0, 0, 0], [0, 0, 0]]")

    # log.insert("Meetup", "Tues", "13:00", "14:00", [0, 1])
    # self.assertEqual(len(cal.__appointments), 1)
    # self.assertEqual(cal.__appointments[0].toString(), "Meetup, Tues 13:00-14:00, [0, 1]")
    # self.assertEqual(len(log.__log), 1)
    # self.assertEqual(log.__log[0].toString(), "1, 0, Insert, ['Meetup', 'Tues', '13:00', '14:00', [0, 1]]")
    # self.assertEqual(log.timeTableToString(), "[[1, 0, 0], [0, 0, 0], [0, 0, 0]]")

    # log.delete("Meetup")
    # self.assertEqual(len(cal.__appointments), 0)
    # self.assertEqual(len(log.__log), 2)
    # self.assertEqual(log.__log[0].toString(), "1, 0, Insert, ['Meetup', 'Tues', '13:00', '14:00', [0, 1]]")
    # self.assertEqual(log.__log[1].toString(), "2, 0, Delete, ['Meetup']")
    # self.assertEqual(log.timeTableToString(), "[[2, 0, 0], [0, 0, 0], [0, 0, 0]]")


  # def test_messageSendAndReceive(self):
  #   # Tests node 0 creating three logs and sending a message with that information
  #   # to the other two nodes
  #   cal0 = ourCalendar.calendar(0)
  #   log0 = distributedLog.distributedLog(cal0, 0, 3)
  #   log0.insert("Meeting", "Mon", "12:00", "13:00", [0, 1])
  #   log0.insert("Meetup", "Tues", "13:00", "14:00", [0, 1])
  #   log0.delete("Meetup")
  #   self.assertEqual(len(cal0.entries), 1)
  #   self.assertEqual(cal0.entries[0].toString(), "Meeting, Mon 12:00-13:00, [0, 1]")
  #   self.assertEqual(log0.timeTableToString(), "[[3, 0, 0], [0, 0, 0], [0, 0, 0]]")

  #   msg1 = log0.getSendMessage(1)
  #   cal1 = ourCalendar.calendar(1)
  #   log1 = distributedLog.distributedLog(cal1, 1, 3)
  #   log1.receiveMessage(msg1)
  #   self.assertEqual(len(cal1.entries), 1)
  #   self.assertEqual(cal1.entries[0].toString(), "Meeting, Mon 12:00-13:00, [0, 1]")
  #   self.assertEqual(log1.timeTableToString(), "[[3, 0, 0], [3, 0, 0], [0, 0, 0]]")

  #   msg2 = log0.getSendMessage(1)
  #   cal2 = ourCalendar.calendar(2)
  #   log2 = distributedLog.distributedLog(cal2, 2, 3)
  #   log2.receiveMessage(msg2)
  #   self.assertEqual(len(cal2.entries), 1)
  #   self.assertEqual(cal2.entries[0].toString(), "Meeting, Mon 12:00-13:00, [0, 1]")
  #   self.assertEqual(log2.timeTableToString(), "[[3, 0, 0], [0, 0, 0], [3, 0, 0]]")


  # def test_logTrimming(self):
  #   # Test that the logs get trimmed based on what is "known" about the other processes.
  #   cal = ourCalendar.calendar(0)
  #   log = distributedLog.distributedLog(cal, 0, 3)
  #   log.insert("Meeting", "Mon", "12:00", "13:00", [0, 1])
  #   log.insert("Meetup", "Tues", "13:00", "14:00", [0, 1])
  #   log.delete("Meetup")
  #   self.assertEqual(len(log.log), 3)
  #   self.assertEqual(log.log[0].toString(), "1, 0, Insert, ['Meeting', 'Mon', '12:00', '13:00', [0, 1]]")
  #   self.assertEqual(log.log[1].toString(), "2, 0, Insert, ['Meetup', 'Tues', '13:00', '14:00', [0, 1]]")
  #   self.assertEqual(log.log[2].toString(), "3, 0, Delete, ['Meetup']")
  #   self.assertEqual(log.timeTableToString(), "[[3, 0, 0], [0, 0, 0], [0, 0, 0]]")

  #   # Make the log think the other two nodes have gotten the first two logs
  #   # by sending a message with no logs, just a time table update.
  #   fakeMsg = "[1, [], [[2, 0, 0], [2, 0, 0], [2, 0, 0]]]"
  #   log.receiveMessage(fakeMsg)
  #   self.assertEqual(len(log.log), 1)
  #   self.assertEqual(log.log[0].toString(), "3, 0, Delete, ['Meetup']")
  #   self.assertEqual(log.timeTableToString(), "[[3, 0, 0], [2, 0, 0], [2, 0, 0]]")

  #   # Make the log think the other two nodes have gotten the third message.
  #   fakeMsg = "[1, [], [[3, 0, 0], [3, 0, 0], [3, 0, 0]]]"
  #   log.receiveMessage(fakeMsg)
  #   self.assertEqual(len(log.log), 0)
  #   self.assertEqual(log.timeTableToString(), "[[3, 0, 0], [3, 0, 0], [3, 0, 0]]")


if __name__ == '__main__':
  unittest.main()
