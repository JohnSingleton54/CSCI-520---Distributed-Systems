#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import time
import Project3.transaction


class block:
    # Stores a single block in the chain.
    # It contains a set of transactions since the prior chain.

    def __init__(self, previousHash: 0 = None, transactions: [Project3.transaction] = []):
        self.__timestamp = time.time()
        self.__transactions = transactions
        self.__previousHash = previousHash
        self.__hash = None
        self.__nonce = 0
        self.__minerAddress = ''

    def __str__(self) -> str:
        return str(self.toTuple())

    def toTuple(self) -> {}:
        trans = []
        for tran in self.__transactions:
            trans.append(tran.toTuple())
        return {
        	'timestamp':    self.__timestamp,
        	'transactions': trans,
        	'previousHash': self.__previousHash,
        	'hash':         self.__hash,
        	'nonce':        self.__nonce,
        	'minerAddress': self.__minerAddress
        }

    def timestamp(self) -> time.time:
        return self.__timestamp
    
    def transactions(self) -> [Project3.transaction]:
        return self.__transactions
    
    def previousHash(self):
        return self.__previousHash

    def hash(self):
        return self.__hash

    def nonce(self):
        return self.__nonce

    def minerAddress(self):
        return self.__minerAddress

    def calculateHash(self):
        # TODO: Implement
        pass

    def mineBlock(self, minerAddress: str, difficulty: int):
        # TODO: Implement
        pass

    def isValid(self) -> bool:
        # TODO: Implement
        return True
