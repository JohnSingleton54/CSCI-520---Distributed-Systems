#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import threading

import blockChain
import block


stateNotRunning = 1
stateRunning = 2
stateStopping = 3


class asyncBlockChain:
    # This is a wrapper around a block chain to provide thread safe access
    # to the chain and asynchronous mining.

    def __init__(self, difficulty: int, minerReward: float, onBlockedMined):
        self.bc = blockChain.blockChain(difficulty, minerReward)
        self.onBlockedMined = onBlockedMined
        self.lock = threading.lock()
        self.thread = None
        self.miningState = stateNotRunning

    def __str__(self) -> str:
        # Gets a string for this transaction.
        with self.lock:
            return str(self.bc)

    def toTuple(self) -> {}:
        # Creates a dictionary for this block chain.
        with self.lock:
            return self.bc.toTuple()

    def fromTuple(self, data: {}):
        # This loads a block chain from the given tuple.
        with self.lock:
            self.bc.fromTuple(data)
        
    def listHashes(self) -> []:
        # Returns all the hashes in the current chain.
        with self.lock:
            return self.listHashes()

    def getDifferenceTuple(self, otherHashes: []) -> []:
        # Returns the tuples of the blocks for the differences between the chains.
        # Will return empty if the other hash is less than or equal to this chain.
        with self.lock:
            index = self.bc.getHashDiffIndex(otherHashes)
            if index < 0:
                return []
            diff = []
            for i in range(index: len(self.bc.chain)):
                diff.append(self.bc.chain[i].toTuple())
            return diff

    def newTransaction(self, fromAccount: str, toAccount: str, amount: float) -> transaction:
        # Creates a new transaction and adds it to the pending
        # transactions to wait to be added to a block during the next mine.
        with self.lock:
            return self.bc.newTransaction(fromAccount, toAccount, amount)

    def addTransaction(self, trans: transaction):
        # Adds a transition to the pending transactions to wait
        # to be added to a block during the next mine.
        with self.lock:
            self.bc.addTransaction(trans)

    def getBalance(self, account: str) -> float:
        # Gets the balance for the given account.
        with self.lock:
            return self.bc.getBalance(account)

    def getAllBalances(self) -> {str: float}:
        # Gets a dictionary of account to balance.
        with self.lock:
            return self.bc.getAllBalances()

    def isValid(self, verbose: bool = False) -> bool:
        # Indicates if this block chain is valid.
        with self.lock:
            return self.bc.isValid(verbose)

    def setBlocks(self, blocks: [block.block]) -> bool:
        # Adds and replaces blocks in the chain with the given blocks.
        # The blocks are only replaced if valid otherwise no change and false is returned.
        with self.lock:
            if not self.bc.setBlocks(blocks):
                return False
        self.stopMining()
        return True

    def startMining(self, miningAccount: str) -> bool:
        with self.lock:
            if self.miningState != stateNotRunning:
                return False
            self.miningState = stateRunning
        self.thread = threading.Thread(target=self.__asyncMinePendingTransactions, args=(miningAccount))
        self.thread.start()
        return True

    def stopMining(self):
        with self.lock:
            if self.miningState != stateRunning:
                return
            self.miningState = stateStopping
        self.thread.join()

    def __asyncMinePendingTransactions(self, miningAccount: str):
        # Constructs and mines a new block. If a block is mined and added
        # prior to the mining being stopped or another block being added,
        # onBlockedMined will be called with the new block.
        with self.lock:
            b = self.bc.buildNextBlock(miningAccount)
        while self.miningState == stateRunning:
            with self.lock:
                added = self.bc.mineBlock(b):
            if added:
                self.onBlockedMined(b)
        self.miningState = stateNotRunning
