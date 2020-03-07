#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 1 (Replicated Log Project)
# due M 3/9/2020 by 11:59 PM

# To run the unit-test:
# - In console 1 call "python -m unittest -v"

import unittest

import ourCalendar
import distributedLog


class TestDistributedLogs(unittest.TestCase):

  def test_localOps(self):
    # Checks that we can insert and delete from our local calendar.
    # Checks time table, the log, and the calendar.
    cal = ourCalendar.calendar(0, False)
    log = distributedLog.distributedLog(cal, 0, 3, False)
    self.assertEqual(cal.toString(), "")
    self.assertEqual(log.logsToString(), "")
    self.assertEqual(log.timeTableToString(), "[[0, 0, 0], [0, 0, 0], [0, 0, 0]]")

    log.insert("Meetup", "Tues", "13:00", "14:00", [0, 1])
    self.assertEqual(cal.toString(), "Meetup, Tues 13:00-14:00, [0, 1]")
    self.assertEqual(log.logsToString(),
      "Insert: time=1, nodeId=0, name=Meetup, day=Tues, start_time=13:00, end_time=14:00, participants=[0, 1]")
    self.assertEqual(log.timeTableToString(), "[[1, 0, 0], [0, 0, 0], [0, 0, 0]]")

    log.delete("Meetup")
    self.assertEqual(cal.toString(), "")
    self.assertEqual(log.logsToString(),
      "Insert: time=1, nodeId=0, name=Meetup, day=Tues, start_time=13:00, end_time=14:00, participants=[0, 1]\n" +
      "  Delete: time=2, nodeId=0, name=Meetup")
    self.assertEqual(log.timeTableToString(), "[[2, 0, 0], [0, 0, 0], [0, 0, 0]]")


  def test_messageSendAndReceive(self):
    # Tests node 0 creating three logs and sending a message
    # with that information to the other two nodes.
    cal0 = ourCalendar.calendar(0, False)
    log0 = distributedLog.distributedLog(cal0, 0, 3, False)
    log0.insert("Meeting", "Mon", "12:00", "13:00", [0, 1])
    log0.insert("Meetup", "Tues", "13:00", "14:00", [0, 1])
    log0.delete("Meetup")
    self.assertEqual(cal0.toString(), "Meeting, Mon 12:00-13:00, [0, 1]")
    self.assertEqual(log0.timeTableToString(), "[[3, 0, 0], [0, 0, 0], [0, 0, 0]]")

    msg1 = log0.getSendMessage(1)
    cal1 = ourCalendar.calendar(1, False)
    log1 = distributedLog.distributedLog(cal1, 1, 3, False)
    log1.receiveMessage(msg1)
    self.assertEqual(cal1.toString(), "Meeting, Mon 12:00-13:00, [0, 1]")
    self.assertEqual(log1.timeTableToString(), "[[3, 0, 0], [3, 0, 0], [0, 0, 0]]")

    msg2 = log0.getSendMessage(1)
    cal2 = ourCalendar.calendar(2, False)
    log2 = distributedLog.distributedLog(cal2, 2, 3, False)
    log2.receiveMessage(msg2)
    self.assertEqual(cal2.toString(), "Meeting, Mon 12:00-13:00, [0, 1]")
    self.assertEqual(log2.timeTableToString(), "[[3, 0, 0], [0, 0, 0], [3, 0, 0]]")


  def test_logTrimming(self):
    # Test that the logs get trimmed based on what is "known" about the other processes.
    cal = ourCalendar.calendar(0, False)
    log = distributedLog.distributedLog(cal, 0, 3, False)
    log.insert("Meeting", "Mon", "12:00", "13:00", [0, 1])
    log.insert("Meetup", "Tues", "13:00", "14:00", [0, 1])
    log.delete("Meetup")
    self.assertEqual(log.logsToString(),
      "Insert: time=1, nodeId=0, name=Meeting, day=Mon, start_time=12:00, end_time=13:00, participants=[0, 1]\n" +
      "  Insert: time=2, nodeId=0, name=Meetup, day=Tues, start_time=13:00, end_time=14:00, participants=[0, 1]\n" +
      "  Delete: time=3, nodeId=0, name=Meetup")
    self.assertEqual(log.timeTableToString(), "[[3, 0, 0], [0, 0, 0], [0, 0, 0]]")

    # Make the log think the other two nodes have gotten the first two logs
    # by sending a message with no logs, just a time table update.
    fakeMsg = "[1, [], [[2, 0, 0], [2, 0, 0], [2, 0, 0]]]"
    log.receiveMessage(fakeMsg)
    self.assertEqual(log.logsToString(), "Delete: time=3, nodeId=0, name=Meetup")
    self.assertEqual(log.timeTableToString(), "[[3, 0, 0], [2, 0, 0], [2, 0, 0]]")

    # Make the log think the other two nodes have gotten the third message.
    fakeMsg = "[1, [], [[3, 0, 0], [3, 0, 0], [3, 0, 0]]]"
    log.receiveMessage(fakeMsg)
    self.assertEqual(log.logsToString(), "")
    self.assertEqual(log.timeTableToString(), "[[3, 0, 0], [3, 0, 0], [3, 0, 0]]")


if __name__ == '__main__':
  unittest.main()
