#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import time


class transaction:
    # A description of the transfer of some amount from one address to another.

    def __init__(self, fromAddress: str, toAddress: str, amount: float):
        self.__timestamp = time.time()
        self.__fromAddress = fromAddress
        self.__toAddress = toAddress
        self.__amount = amount
        # No signature according to project requirements
        
    def timestamp(self) -> time.time:
        return self.__timestamp

    def fromAddress(self) -> str:
        return self.__fromAddress

    def toAddress(self) -> str:
        return self.__toAddress

    def amount(self) -> float:
        return self.__amount

    def isValid(self) -> bool:
        # TODO: Implement
        return True
