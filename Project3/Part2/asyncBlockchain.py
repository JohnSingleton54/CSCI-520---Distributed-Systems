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
    # to the chain and asynchronous validating.

    def __init__(self, creator: str, probability: float):
        self.bc = blockchain.Blockchain(creator, probability)
        self.lock = threading.Lock()
        self.thread = None
        self.needToRestart = True

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

    # TODO: Add the part which creates the blocks and shares them around
    #       as candidates and the voting to choose the correct block
    #       then use addBlock to instert block and check other chains
    #       with the request more information like in part 1.
