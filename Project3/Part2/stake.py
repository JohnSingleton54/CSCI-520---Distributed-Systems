#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import misc


class Stake:
    # A description of the stake put up for a candidate block

    def __init__(self, validator: str = "", blockHash: str = "", amount: float = 0.0):
        # Creates a new stake.
        self.timestamp = misc.newTime()
        self.validator = validator
        self.blockHash = blockHash
        self.amount    = amount

    def __str__(self) -> str:
        # Gets a string for this stake.
        return "stake: time: %s, validator: %s, blockHash: %s, amount: %f" % (
            misc.timeToStr(self.timestamp), self.validator, self.blockHash, self.amount)

    def toTuple(self) -> {}:
        # Creates a dictionary for this transaction.
        return {
            "timestamp": self.timestamp,
            "validator": self.validator,
            "blockHash": self.blockHash,
            "amount":    self.amount
        }

    def fromTuple(self, data: {}):
        # This loads a stake from the given tuple.
        self.timestamp = data["timestamp"]
        self.validator = data["validator"]
        self.blockHash = data["blockHash"]
        self.amount    = data["amount"]

    def compare(self, other) -> int:
        # Determines how these two stakes compare.
        # less than zero for this stake being less than the other.
        # greater than zero for this stake being greater than the other.
        # equal to zero if the two stake are equal.
        if self.timestamp < other.timestamp:
            return -1
        if self.timestamp > other.timestamp:
            return 1

        if self.validator < other.validator:
            return -1
        if self.validator > other.validator:
            return 1

        if self.blockHash < other.blockHash:
            return -1
        if self.blockHash > other.blockHash:
            return 1

        # Use epsilon comparator for amount since a float may not JSON perfectly.
        if abs(self.amount - other.amount) > 0.000001:
            if self.amount < other.amount:
                return -1
            if self.amount > other.amount:
                return 1
        # They are the same
        return 0

    def isValid(self, blockHash, runningBalances: {str: float}, verbose: bool = False) -> bool:
        # Indicates if this stake is valid.
        if self.amount <= 0:
            if verbose:
                print("Amount was %d <= 0 so can not fund stake" % (self.amount))
            return False

        if not self.validator:
            if verbose:
                print("Must have a from account")
            return False

        if self.blockHash != blockHash:
            if verbose:
                print("Block hash did not match expected block hash")
            return False

        if runningBalances.get(self.validator, 0.0) < self.amount:
            if verbose:
                print("Insufficient funds: %s has less than %d" % (self.validator, self.amount))
            return False
        return True
