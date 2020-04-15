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
        self.__chain = [Project3.block.block()]
        self.__pending = [] # pending transactions

    def __str__(self) -> str:
        return str(self.toTuple())

    def toTuple(self) -> {}:
        blocks = []
        for block in self.__chain:
            blocks.append(block.toTuple())
        pending = []
        for tran in self.__pending:
            pending.append(tran.toTuple())
        return {
            # No need to output difficulty or mining reward
            'blocks': blocks,
           	'pending': pending
        }

    def addTransaction(self, fromAccount: str, toAccount: str, amount: float):
        trans = Project3.transaction.transaction(fromAccount, toAccount, amount)
        self.__pending.append(trans)
        # TODO: Implement and check isValid
        pass

    def getAccounts(self) -> [str]:
        accounts = {}
        for block in self.__chain:
            for trans in block.transactions():
                accounts[trans.fromAddress()] = True
                accounts[trans.toAddress()] = True
        return accounts.keys()

    def getBalance(self, account: str) -> float:
        amount = 0.0
        for block in self.__chain:
            for trans in block.transactions():
                if account == trans.fromAddress():
                    amount -= trans.amount
                if account == trans.toAddress():
                    amount += trans.amount
        return amount

    def getAllBalances(self) -> {str: float}:
        accounts = {}
        for block in self.__chain:
            for trans in block.transactions():
                accounts[trans.fromAddress()] -= trans.amount
                accounts[trans.toAddress()] += trans.amount
        return accounts
