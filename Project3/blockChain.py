#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import block
import transaction


class blockChain:
    # The block chain and current configurations.

    def __init__(self, difficulty: int, miningReward: float):
        # TODO: Implement
        self.__difficulty = difficulty
        self.__miningReward = miningReward
        self.__chain = [block.block()]
        self.__pending = []  # pending transactions
        self.__keepMining = True

    def __str__(self) -> str:
        # Gets a string for this transaction.
        return str(self.toTuple())

    def toTuple(self) -> {}:
        # Creates a dictionary for this block chain.
        blocks = []
        for block in self.__chain:
            blocks.append(block.toTuple())
        pending = []
        for tran in self.__pending:
            pending.append(tran.toTuple())
        return {
            # No need to output difficulty or mining reward
            "blocks": blocks,
            "pending": pending,
        }

    def lastBlock(self) -> block:
        # Returns the last block added to the chain.
        return self.__chain[-1]

    def addTransaction(self, fromAccount: str, toAccount: str, amount: float) -> bool:
        # Creates a new transaction and adds it to the pending
        # transactions to wait to be added to a block during the next mine.
        trans = transaction.transaction(fromAccount, toAccount, amount)
        if trans.isValid():
            self.__pending.append(trans)
            return True
        return False

    def getAccounts(self) -> [str]:
        # Gets a list of all the accounts in the chain.
        accounts = {}
        for block in self.__chain:
            for trans in block.transactions():
                accounts[trans.fromAddress()] = True
                accounts[trans.toAddress()] = True
        return accounts.keys()

    def getBalance(self, account: str) -> float:
        # Gets the balance for a single account in the chain.
        amount = 0.0
        for block in self.__chain:
            for trans in block.transactions():
                if account == trans.fromAddress():
                    amount -= trans.amount
                if account == trans.toAddress():
                    amount += trans.amount
        return amount

    def getAllBalances(self) -> {str: float}:
        # Gets a dictionary of account to balance.
        accounts = {}
        for block in self.__chain:
            for trans in block.transactions():
                accounts[trans.fromAddress()] -= trans.amount
                accounts[trans.toAddress()] += trans.amount
        return accounts

    def stopMining(self):
        # Stops the mining loop.
        self.__keepMining = False

    def minePendingTransactions(self, miningAddress: str) -> block:
        # Constructs and mines a new block. If None is returned there are no
        # transactions to mine or the mining has been stopped before finishing.
        # Unless stopped this method will not return.
        self.__keepMining = True

        #
        # TODO: Implement
        #

        return None

    def isValid(self) -> bool:
        # Indicates if this block chain is valid.
        prev = self.__chain[0] # Default initial block
        for i in range(1, len(self.__chain)-1):
            block = self.__chain[i]
            if not block.isValid():
                return False
            if block.previousHash() != prev.hash():
                return False
            prev = block
        return True
