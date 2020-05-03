#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import threading

import blockchain
import block
import misc


probabilityOfCreation     = 0.25 # 25%
amountOfTimeBetweenBlocks = 5.0 #20.0 # seconds


class AsyncBlockchain:
    # This is a wrapper around a blockchain to provide thread safe access
    # to the chain and asynchronous validating.

    def __init__(self, creator: str, onCandidateCreated):
        self.bc = blockchain.Blockchain(creator, probabilityOfCreation)
        self.lock = threading.Lock()
        self.onCandidateCreated = onCandidateCreated
        self.stopFlag = threading.Event()
        self.thread = None

    def __str__(self) -> str:
        # Gets a string for this transaction.
        with self.lock:
            return str(self.bc)

    def toTuple(self) -> {}:
        # Creates a dictionary for this block chain.
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
        # transactions to wait to be added to a new block.
        with self.lock:
            return self.bc.newTransaction(fromAccount, toAccount, amount)

    def addTransaction(self, trans):
        # Adds a transition to the pending transactions to wait
        # to be added to a new block.
        with self.lock:
            self.bc.addTransaction(trans)

    def getAllBalances(self) -> {str: float}:
        # Gets a dictionary of account to balance.
        with self.lock:
            return self.bc.getAllBalances()

    def isValid(self, verbose: bool = False) -> bool:
        # Indicates if this blockchain is valid.
        with self.lock:
            return self.bc.isValid(verbose)

    def addCandidateBlock(self, block: block.Block, verbose: bool = False) -> str:
        # Adds a candidate block to the be signed.
        with self.lock:
            return self.bc.addCandidateBlock(block, verbose)

    def setBlocks(self, blocks: [block.Block], verbose: bool = False) -> str:
        # Adds and replaces blocks in the chain with the given blocks.
        # The blocks are only replaced if valid otherwise no change and false is returned.
        with self.lock:
            return self.bc.setBlocks(blocks, verbose)

    def startCreation(self) -> bool:
        # Start an asynchronous mining thread.
        self.thread = threading.Thread(target=self.__blockCreator)
        self.thread.start()

    def stopCreation(self):
        # Stops the creation timer for shutting down.
        self.stopFlag.set()

    def __blockCreator(self):
        # This tread will periodically create a candidate block.
        # The `while not flag.wait` is based on https://stackoverflow.com/a/12435256
        while not self.stopFlag.wait(amountOfTimeBetweenBlocks):
            with self.lock:
                timestamp = misc.newTime()
                if not self.bc.shouldCreateNextBlock(timestamp):
                    continue
                candidate = self.bc.createNextBlock(timestamp)
                self.bc.addCandidateBlock(candidate, True)
            self.onCandidateCreated(candidate)
