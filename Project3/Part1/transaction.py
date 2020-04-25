#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import misc


class transaction:
    # A description of the transfer of some amount from one address to another.

    def __init__(self, fromAccount: str = "", toAccount: str = "", amount: float = 0.0):
        # Creates a new transaction.
        # No signature according to project requirements.
        self.__timestamp   = misc.newTime()
        self.__fromAccount = fromAccount
        self.__toAccount   = toAccount
        self.__amount      = amount

    def __str__(self) -> str:
        # Gets a string for this transaction.
        return "tran: time: %s, from: %s, to: %s, amount: %f" % (
            misc.timeToStr(self.__timestamp), self.__fromAccount, self.__toAccount, self.__amount)

    def toTuple(self) -> {}:
        # Creates a dictionary for this transaction.
        return {
            "timestamp":   self.__timestamp,
            "fromAccount": self.__fromAccount,
            "toAccount":   self.__toAccount,
            "amount":      self.__amount
        }

    def fromTuple(self, data: {}):
        # This loads a transaction from the given tuple.
        self.__timestamp   = data["timestamp"]
        self.__fromAccount = data["fromAccount"]
        self.__toAccount   = data["toAccount"]
        self.__amount      = data["amount"]

    def timestamp(self) -> float:
        # The timestamp for when this transaction was created.
        return self.__timestamp

    def fromAccount(self) -> str:
        # The address to take the amount from.
        return self.__fromAccount

    def toAccount(self) -> str:
        # The address to give the amount to.
        return self.__toAccount

    def amount(self) -> float:
        # The amount being transferred between the addresses.
        return self.__amount

    def isValid(self, runningBalances: {str: float}) -> bool:
        # Indicates if this transaction is valid.
        if self.__amount <= 0:
            return False
        if not self.__fromAccount or not self.__toAccount:
            # Must have a from account and to account.
            return False
        if (not self.__fromAccount in runningBalances) or (runningBalances[self.__fromAccount] < self.__amount):
            # May not take more money from an account than they have.
            return False
        runningBalances[self.__fromAccount] -= self.__amount
        runningBalances[self.__toAccount]   += self.__amount
        return True
