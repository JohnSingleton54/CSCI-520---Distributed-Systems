#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import Project3.block
import Project3.transaction


class blockChain:
    # The block chain and current configurations.

    def __init__(self, difficulty: int, miningReward: float):
        # TODO: Implement
        self.__difficulty = difficulty
        self.__miningReward = miningReward
        # chain:               []Block
        # pendingTransactions: []Transaction

    def addTransaction(self, fromAccount: int, toAccount: int, amount: float):
        # TODO: Implement
        pass

    def getAccounts(self) -> [int]:
        # TODO: Implement
        pass

    def getBalance(self, account: int) -> float:
        # TODO: Implement
        pass

    def getAllBalances(self) -> {int: float}:
        # TODO: Implement
        pass
