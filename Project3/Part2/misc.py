#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import time
import random
import hashlib
import json


def timeToStr(timestamp: float) -> str:
    # Converts a timestamp into a formatted string.
    return time.strftime("%d %b %Y %H:%M:%S", time.localtime(timestamp))


# This is a method that when called returns the current time.
# This is redefined like this so that in the tests we can set the
# time and not have to deal with when a test is run.
newTime = time.time

def useTestTime():
    # Override the misc.newTime to return a constant time
    # and resets the test time.
    testTimeValue = 1587222720.0  # 18 Apr 2020 09:12:00
    def testTime() -> float:
        nonlocal testTimeValue
        testTimeValue += 1.0
        return testTimeValue
    global newTime
    newTime = testTime


def hashData(data: {}):
    # Gets the hash of the given dictionary.
    dataBytes = bytearray(str(data), 'utf-8')
    return hashlib.sha256(dataBytes).hexdigest()


def coinToss(seed, probability: float, verbose: bool = False) -> bool:
    # This seeds a random number with the given seed then checks if the
    # returned random number is less than the probability [0.0 .. 1.0].
    # True if successful (heads), false otherwise (tails).
    r = random.Random(seed)
    value = r.random()
    if verbose:
        print("coinToss(", value, "<", probability, ")=", value < probability)
    return value < probability


def insertSort(sortedList, value) -> bool:
    # Adds a value to a sorted list, the values are required to have the compare method.
    # This will return True if added, False if already exists.
    for i in range(len(sortedList)):
        cmp = sortedList[i].compare(value)
        if cmp == 0:
            return False
        if cmp > 0:
            sortedList.insert(i, value)
            return True
    sortedList.append(value)
    return True


def removeFromSorted(sortedList, value) -> bool:
    # Removes a value from a sorted list, the values are required to have the compare method.
    # This will return True if removed, False if already doesn't exist.
    for i in range(len(sortedList)):
        cmp = sortedList[i].compare(value)
        if cmp == 0:
            del sortedList[i]
            return True
        if cmp > 0:
            return False
    return False
