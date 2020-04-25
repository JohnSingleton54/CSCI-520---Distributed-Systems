#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import time
import random


def timeToStr(timestamp: float) -> str:
    # Converts a timestamp into a formatted string.
    return time.strftime("%d %b %Y %H:%M:%S", time.localtime(timestamp))

def newRandomNonce() -> int:
    # Creates a new randomized nonce value.
    return random.randint(0, 4000000000)

# This is a method that when called returns the current time.
# This is redefined like this so that in the tests we can set the
# time and not have to deal with when a test is run.
newTime = time.time

# This is a method that when called returns a new nonce.
# This is defined like this so that in the tests we can override
# this method and not have to deal with a random nonce.
newNonce = newRandomNonce
