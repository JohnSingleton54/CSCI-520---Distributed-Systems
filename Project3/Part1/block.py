#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import hashlib
import json

import transaction
import misc


initialHash = "0"*64


class Block:
    # Stores a single block in the chain.
    # It contains a set of transactions since the prior chain.

    def __init__(self, blockNum: int = 0, previousHash = None, minerAccount: str = "",
        miningReward: float = 0.0, transactions: [transaction] = []):
        # Creates a new block with the given previous block's hash
        # and the transactions for this block.
        self.blockNum      = blockNum
        self.timestamp     = misc.newTime()
        self.transactions  = transactions
        self.previousHash  = previousHash
        self.hash          = initialHash
        self.nonce         = 0
        self.minerAccount  = minerAccount
        self.miningReward  = miningReward

    def __str__(self) -> str:
        # Gets a string for this block.
        parts = []
        parts.append("block: %d, time: %s, nonce: %d, miner: %s, reward: %f" % (
            self.blockNum, misc.timeToStr(self.timestamp), self.nonce, str(self.minerAccount), self.miningReward))
        parts.append("  prev: %s" % (str(self.previousHash)))
        parts.append("  hash: %s" % (str(self.hash)))
        for trans in self.transactions:
            parts.append("  "+str(trans).replace("\n", "\n  "))
        return "\n".join(parts)

    def toTuple(self) -> {}:
        # Creates a dictionary for this block.
        trans = []
        for tran in self.transactions:
            trans.append(tran.toTuple())
        return {
            "blockNum":     self.blockNum,
            "timestamp":    self.timestamp,
            "transactions": trans,
            "previousHash": self.previousHash,
            "hash":         self.hash,
            "nonce":        self.nonce,
            "minerAccount": self.minerAccount,
            "miningReward": self.miningReward,
        }

    def fromTuple(self, data: {}):
        # This loads a block from the given tuple.
        self.blockNum      = data["blockNum"]
        self.timestamp     = data["timestamp"]
        self.previousHash  = data["previousHash"]
        self.hash          = data["hash"]
        self.nonce         = data["nonce"]
        self.minerAccount  = data["minerAccount"]
        self.miningReward  = data["miningReward"]
        self.transactions  = []
        for subdata in data["transactions"]:
            t = transaction.Transaction()
            t.fromTuple(subdata)
            self.transactions.append(t)

    def calculateHash(self):
        # Calculates the hash for this whole block, excluding the hash value itself.
        data = self.toTuple()
        del data["hash"]
        dataBytes = bytearray(str(data), 'utf-8')
        return hashlib.sha256(dataBytes).hexdigest()

    def isValid(self, difficulty: int, miningReward: float, runningBalances: {str: float}, verbose: bool = False) -> bool:
        # Determines if this block is valid.
        for i in range(len(self.transactions)):
            if not self.transactions[i].isValid(runningBalances, verbose):
                if verbose:
                    print("Block %d has transaction %d which is not valid" % (self.blockNum, i))
                return False

        if not self.minerAccount:
            if verbose:
                print("Block %d has no miner account set" % (self.blockNum))
            return False

        if miningReward != self.miningReward:
            if verbose:
                print("Block %d has wrong mining reward" % (self.blockNum))
            return False

        if self.calculateHash() != self.hash:
            if verbose:
                print("Block %d has different hash than calculated" % (self.blockNum))
            return False

        if not str(self.hash).startswith('0'*difficulty):
            if verbose:
                print("Block %d did not meet difficulty requirement" % (self.blockNum))
            return False

        runningBalances[self.minerAccount] = runningBalances.get(self.minerAccount, 0.0) + self.miningReward
        return True

