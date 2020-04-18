#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import misc


class transaction:
    # A description of the transfer of some amount from one address to another.

    def __init__(self, fromAddress: str, toAddress: str, amount: float):
        # Creates a new transaction.
        # No signature according to project requirements.
        self.__timestamp   = misc.newTime()
        self.__fromAddress = fromAddress
        self.__toAddress   = toAddress
        self.__amount      = amount

    def __str__(self) -> str:
        # Gets a string for this transaction.
        return "tran: time: %s, from: %s, to: %s, amount: %f" % (
            misc.timeToStr(self.__timestamp), self.__fromAddress, self.__toAddress, self.__amount)

    def toTuple(self) -> {}:
        # Creates a dictionary for this transaction.
        return {
            "timestamp":   self.__timestamp,
            "fromAddress": self.__fromAddress,
            "toAddress":   self.__toAddress,
            "amount":      self.__amount
        }

    def timestamp(self) -> float:
        # The timestamp for when this transaction was created.
        return self.__timestamp

    def fromAddress(self) -> str:
        # The address to take the amount from.
        return self.__fromAddress

    def toAddress(self) -> str:
        # The address to give the amount to.
        return self.__toAddress

    def amount(self) -> float:
        # The amount being transferred between the addresses.
        return self.__amount

    def isValid(self, rewardTransaction: bool = False, miningReward: float = 0.0, minerAddress: str = None) -> bool:
        # Indicates if this transaction is valid.
        if rewardTransaction:
            return self.__amount == miningReward and not self.__fromAddress and self.__toAddress == minerAddress
        return self.__amount > 0 and self.__fromAddress and self.__toAddress
