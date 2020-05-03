#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import transaction
import misc


initialHash = "0"*64


class Block:
    # Stores a single block in the chain.
    # It contains a set of transactions since the prior chain.

    def __init__(self, timestamp: float = 0.0, blockNum: int = 0, previousHash = None, creator: str = "", transactions: [transaction] = []):
        # Creates a new block with the given previous block's hash
        # and the transactions for this block.
        self.blockNum     = blockNum
        self.timestamp    = timestamp
        self.transactions = transactions
        self.previousHash = previousHash
        self.hash         = initialHash
        self.creator      = creator
        self.signatures   = []
        # Calculate the hash for this block.
        self.hash = self.calculateHash()

    def __str__(self) -> str:
        # Gets a string for this block.
        parts = []
        parts.append("block: %d, time: %s, creator: %s" % (
            self.blockNum, misc.timeToStr(self.timestamp), str(self.creator)))
        parts.append("  prev: %s" % (str(self.previousHash)))
        parts.append("  hash: %s" % (str(self.hash)))
        #parts.append(self.signatures) # TODO: Add signatures to everything
        parts.append("  transactions:")
        for trans in self.transactions:
            parts.append("    "+str(trans).replace("\n", "\n  "))
        return "\n".join(parts)

    def toTuple(self) -> {}:
        # Creates a dictionary for this block.
        trans = []
        for tran in self.transactions:
            trans.append(tran.toTuple())
        return {
            "blockNum":     self.blockNum,
            "timestamp":    self.timestamp,
            "previousHash": self.previousHash,
            "hash":         self.hash,
            "creator":      self.creator,
            "transactions": trans,
        }

    def fromTuple(self, data: {}):
        # This loads a block from the given tuple.
        self.blockNum      = data["blockNum"]
        self.timestamp     = data["timestamp"]
        self.previousHash  = data["previousHash"]
        self.hash          = data["hash"]
        self.creator       = data["creator"]
        self.transactions  = []
        for subdata in data["transactions"]:
            t = transaction.Transaction()
            t.fromTuple(subdata)
            self.transactions.append(t)

    def calculateHash(self):
        # Calculates the hash for this whole block, excluding the hash value.
        data = self.toTuple()
        del data["hash"]
        return misc.hashData(data)

    def updateBalance(self, runningBalances: {str: float}):
        # Updates the given running Balances
        for tran in self.transactions:
            tran.updateBalance(runningBalances)

    def isValid(self, runningBalances: {str: float}, verbose: bool = False) -> bool:
        # Determines if this block is valid.
        if self.calculateHash() != self.hash:
            if verbose:
                print("Block %d has different hash than calculated" % (self.blockNum))
            return False

        if not self.creator:
            if verbose:
                print("Block %d has no creator set" % (self.blockNum))
            return False

        for i in range(len(self.transactions)):
            if not self.transactions[i].isValid(runningBalances, verbose):
                if verbose:
                    print("Block %d has transaction %d which is not valid" % (self.blockNum, i))
                return False

        self.__updateWithValidatorPayout(runningBalances)
        return True
