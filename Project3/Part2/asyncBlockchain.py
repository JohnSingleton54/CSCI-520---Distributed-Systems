#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import threading

import blockchain
import block
import misc


timeBetweenCreations = 20.0  # seconds
timeBetweenTicks = 0.5 # seconds


class AsyncBlockchain:
    # This is a wrapper around a blockchain to provide thread safe access
    # to the chain and asynchronous validating.

    def __init__(self, creator: str, validators: [str], onCandidateCreated, onBlockAdded):
        self.bc   = blockchain.Blockchain(creator, validators)
        self.lock = threading.Lock()
        self.onCandidateCreated = onCandidateCreated
        self.onBlockAdded       = onBlockAdded
        self.stopFlag = threading.Event()
        self.thread   = None
        self.startOfInterval = misc.newTime()

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
            self.__bumpIntervalTimer()

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

    def validateCandidateBlock(self, block: block.Block, verbose: bool = False) -> str:
        # Determine if the new is at or past the end of the chain. If not, ignore it.
        with self.lock:
            return self.bc.validateCandidateBlock(block, verbose)

    def setBlocks(self, blocks: [block.Block], verbose: bool = False) -> str:
        # Adds and replaces blocks in the chain with the given blocks.
        # The blocks are only replaced if valid otherwise no change and false is returned.
        with self.lock:
            result = self.bc.setBlocks(blocks, verbose)
            if result == blockchain.blocksAdded:
                self.__bumpIntervalTimer()
            return result

    def whoShouldCreateBlock(self, prevHash) -> str:
        # Gets the name of the validator who should create the new block.
        with self.lock:
            return self.bc.whoShouldCreateBlock(prevHash)

    def __bumpIntervalTimer(self):
        # Must be called from in a lock. Resets the start of the interval.
        lastTime = self.bc.lastBlock().timestamp
        if lastTime > self.startOfInterval:
            self.startOfInterval = lastTime
    
    def addSignature(self, sign: str, candidateHash):
        # Adds a signature to the candidate and checks if the block can be added.
        with self.lock:
            if not self.bc.addSignature(sign, candidateHash):
                return False
            block = self.bc.candidate
            self.bc.setBlocks([block], True)
            self.bc.candidate = None
            self.__bumpIntervalTimer()
        self.onBlockAdded(block)

    def start(self) -> bool:
        # Start an asynchronous creation thread.
        self.thread = threading.Thread(target=self.__run)
        self.thread.start()

    def stop(self):
        # Stops the creation timer for shutting down.
        self.stopFlag.set()

    def __run(self):
        # This tread will periodically create a candidate block.
        # The `while not flag.wait` is based on https://stackoverflow.com/a/12435256
        while not self.stopFlag.wait(timeBetweenTicks):
            now = misc.newTime()
            delta = (now - self.startOfInterval)
            if delta >= timeBetweenCreations:
                self.startOfInterval = now
                self.__checkPreviousBlockWasAdded()
                self.__createBlock()

    def __checkPreviousBlockWasAdded(self):
        # TODO: Implement checking the last time block and then making an invalid block.

        # Also clear out any stale candidate
        with self.lock:
            self.bc.candidate = None

    def __createBlock(self):
        # Checks if this needs to create a new candidate block and creates one.
        with self.lock:
            if not self.bc.shouldCreateNextBlock():
                return
            candidate = self.bc.createNextBlock()
            self.bc.candidate = candidate
            self.startOfInterval = candidate.timestamp
        self.onCandidateCreated(candidate)
