#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import transaction
import misc


class block:
    # Stores a single block in the chain.
    # It contains a set of transactions since the prior chain.

    def __init__(self, previousHash = None, transactions: [transaction] = []):
        # Creates a new block with the given previous block's hash
        # and the transactions for this block.
        self.__timestamp    = misc.newTime()
        self.__transactions = transactions
        self.__previousHash = previousHash
        self.__hash         = None
        self.__nonce        = 0
        self.__minerAddress = ""

    def __str__(self) -> str:
        # Gets a string for this block.
        parts = []
        parts.append("block: time: %s, prev: %s, hash: %s, nonce: %d, miner: %s" % (
            misc.timeToStr(self.__timestamp), str(self.__previousHash),
            str(self.__hash), self.__nonce, self.__minerAddress))
        for trans in self.__transactions:
            parts.append("  "+str(trans).replace("\n", "\n  "))
        return "\n".join(parts)

    def toTuple(self) -> {}:
        # Creates a dictionary for this block.
        trans = []
        for tran in self.__transactions:
            trans.append(tran.toTuple())
        return {
            "timestamp":    self.__timestamp,
            "transactions": trans,
            "previousHash": self.__previousHash,
            "hash":         self.__hash,
            "nonce":        self.__nonce,
            "minerAddress": self.__minerAddress,
        }

    def timestamp(self) -> float:
        # The time this block was created at.
        return self.__timestamp

    def transactions(self) -> [transaction]:
        # Gets a copy of the list of the transactions.
        return self.__transactions.copy()

    def previousHash(self):
        # The previous block's hash value.
        return self.__previousHash

    def hash(self):
        # The hash for this blocks hash value.
        return self.__hash

    def minerAddress(self):
        # The address of the person which mined this block.
        return self.__minerAddress

    def calculateHash(self):
        # Calculates the hash for this whole block, excluding the hash value itself.
        tuple = self.toTuple()
        del tuple["hash"]
        return hash(tuple)

    def isValid(self, difficulty: int, miningReward: float) -> bool:
        # Determines if this block is valid.
        rewardTransaction = True
        for trans in self.__transactions:
            if not trans.isValid(rewardTransaction, miningReward, self.__minerAddress):
                return False
            rewardTransaction = False
        if self.calculateHash() != self.__hash:
            return False
        if not str(self.__hash).startswith('0'*difficulty):
            return False
        return True

    def mineBlock(self, minerAddress: str, difficulty: int) -> bool:
        # This randomly picks a nonce and rehashes this block. It checks if the difficulty
        # challenge has been reached. Returns true if this attempt was successful, false otherwise.
        self.__nonce = misc.newNonce()
        #
        # TODO: Implement
        #
        return False
