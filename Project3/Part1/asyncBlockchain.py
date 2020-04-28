#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import threading

import blockchain
import block


class AsyncBlockchain:
    # This is a wrapper around a blockchain to provide thread safe access
    # to the chain and asynchronous mining.

    def __init__(self, difficulty: int, miningReward: float, minerAccount: str, onBlockedMined):
        self.bc = blockchain.Blockchain(difficulty, miningReward)
        self.onBlockedMined = onBlockedMined
        self.minerAccount = minerAccount
        self.lock = threading.Lock()
        self.thread = None
        self.keepMining = True
        self.needToRestart = True

    def __str__(self) -> str:
        # Gets a string for this transaction.
        with self.lock:
            return str(self.bc)

    def toTuple(self) -> {}:
        # Creates a dictionary for this blockchain.
        with self.lock:
            return self.bc.toTuple()

    def fromTuple(self, data: {}):
        # This loads a blockchain from the given tuple.
        with self.lock:
            self.bc.fromTuple(data)

    def lastBlock(self):
        # Returns the last block in the chain.
        with self.lock:
            return self.bc.lastBlock()

    def listHashes(self) -> []:
        # Returns all the hashes in the current chain.
        with self.lock:
            return self.bc.listHashes()

    def getDifferenceTuple(self, otherHashes: []) -> []:
        # Returns the tuples of the blocks for the differences between the chains.
        # Will return empty if the other hash is less than or equal to this chain.
        with self.lock:
            return self.bc.getDifferenceTuple(otherHashes)

    def newTransaction(self, fromAccount: str, toAccount: str, amount: float):
        # Creates a new transaction and adds it to the pending
        # transactions to wait to be added to a block during the next mine.
        with self.lock:
            return self.bc.newTransaction(fromAccount, toAccount, amount)

    def addTransaction(self, trans):
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
        # Indicates if this blockchain is valid.
        with self.lock:
            return self.bc.isValid(verbose)

    def setBlocks(self, blocks: [block.Block], verbose: bool = False) -> int:
        # Adds and replaces blocks in the chain with the given blocks.
        # The blocks are only replaced if valid otherwise no change and false is returned.
        with self.lock:
            return self.bc.setBlocks(blocks, verbose)

    def startMining(self) -> bool:
        # Start an asynchronous mining thread.
        self.keepMining = True
        self.thread = threading.Thread(target=self.__asyncMinePendingTransactions)
        self.thread.start()

    def restartMining(self):
        # Stops the current block being mined and starts new block.
        self.needToRestart = True

    def stopMining(self):
        # Stop and rejoin the mining thread.
        self.keepMining = False
        self.thread.join()

    def __asyncMinePendingTransactions(self):
        # Constructs and mines a new block. If a block is mined and added
        # prior to the mining being stopped or another block being added,
        # onBlockedMined will be called with the new block.
        while self.keepMining:
            with self.lock:
                b = self.bc.buildNextBlock(self.minerAccount)
            self.needToRestart = False
            while self.keepMining and not self.needToRestart:
                added = False
                with self.lock:
                    added = self.bc.mineBlock(b)
                if added:
                    self.needToRestart = True
                    self.onBlockedMined(b)
