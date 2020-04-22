#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import threading

import block
import transaction


class blockChain:
    # The block chain and current configurations.

    def __init__(self, difficulty: int, miningReward: float):
        # Creates a new block chain.
        self.__difficulty   = difficulty
        self.__miningReward = miningReward
        self.__chain        = [block.block()]
        self.__pending      = []  # pending transactions
        self.__keepMining   = True
        self.__mining       = False
        self.__lock         = threading.Lock()

    def __str__(self) -> str:
        # Gets a string for this transaction.
        parts = []
        with self.__lock:
            parts.append("blocks:")
            for block in self.__chain:
                parts.append("  "+str(block).replace("\n", "\n  "))
            parts.append("pending:")
            for tran in self.__pending:
                parts.append("  "+str(tran).replace("\n", "\n  "))
        return "\n".join(parts)

    def toTuple(self) -> {}:
        # Creates a dictionary for this block chain.
        blocks = []
        with self.__lock:
            for block in self.__chain:
                blocks.append(block.toTuple())
            pending = []
            for tran in self.__pending:
                pending.append(tran.toTuple())
        return {
            # No need to output difficulty or mining reward
            "blocks":  blocks,
            "pending": pending,
        }

    def fromTuple(self, data: {}):
        # This loads a block chain from the given tuple.
        with self.__lock:
            self.__chain = []
            for subdata in data["blocks"]:
                b = block.block()
                b.fromTuple(subdata)
                self.__chain.append(b)

            self.__pending = []
            for subdata in data["pending"]:
                t = transaction.transaction()
                t.fromTuple(subdata)
                self.__pending.append(t)

    def lastBlock(self) -> block:
        # Returns the last block added to the chain.
        with self.__lock:
            return self.__chain[-1]

    def newTransaction(self, fromAccount: str, toAccount: str, amount: float) -> transaction:
        # Creates a new transaction and adds it to the pending
        # transactions to wait to be added to a block during the next mine.
        trans = transaction.transaction(fromAccount, toAccount, amount)
        if self.addTransaction(trans):
            return trans
        return None

    def addTransaction(self, trans: transaction) -> bool:
        # Adds a transition to the pending transactions to wait
        # to be added to a block during the next mine.
        if trans.isValid():
            # TODO: Optional, check if the fromAccount has the amount to give so they don't overdraw
            with self.__lock:
                self.__pending.append(trans)
            return True
        return False

    def getAccounts(self) -> [str]:
        # Gets a list of all the accounts in the chain.
        accounts = {}
        with self.__lock:
            for block in self.__chain:
                for trans in block.transactions():
                    accounts[trans.fromAddress()] = True
                    accounts[trans.toAddress()]   = True
        return accounts.keys()

    def getBalance(self, account: str) -> float:
        # Gets the balance for a single account in the chain.
        amount = 0.0
        with self.__lock:
            for block in self.__chain:
                for trans in block.transactions():
                    if account == trans.fromAddress():
                        amount -= trans.amount()
                    if account == trans.toAddress():
                        amount += trans.amount()
        return amount

    def getAllBalances(self) -> {str: float}:
        # Gets a dictionary of account to balance.
        accounts = {}
        with self.__lock:
            for block in self.__chain:
                for trans in block.transactions():
                    accounts[trans.fromAddress()] -= trans.amount()
                    accounts[trans.toAddress()]   += trans.amount()
        return accounts

    def isValid(self) -> bool:
        # Indicates if this block chain is valid.
        with self.__lock:
            return self.__isChainValid(self.__chain)

    def __isChainValid(self, chain: [block.block]) -> bool:
        # Indicates if this given chain is valid.
        prev = chain[0]  # Default initial block
        for block in chain[1:]:
            if not block.isValid(self.__difficulty, self.__miningReward):
                return False
            if block.previousHash() != prev.hash():
                return False
            prev = block
        return True

    def setBlocks(self, index: int, blocks: [block.block]) -> bool:
        # Adds and replaces blocks in the chain with the given blocks.
        # The blocks are only replaced if valid otherwise no change and false is returned.
        with self.__lock:
            newChain = []
            newChain.extend(self.__chain[:index])
            newChain.extend(blocks)
            if self.__isChainValid(newChain):
                self.__chain = newChain
                return True
            return False

    def stopMining(self):
        # Stops the mining loop.
        self.__keepMining = False

    def isMining(self) -> bool:
        # Indicates if a block is currently being mined by this chain.
        return self.__mining

    def startMinePendingTransactions(self, miningAddress: str, onBlockMined = None):
        # Starts mining a new block asynchronously.
        threading.Thread(target=self.minePendingTransactions).start((miningAddress, onBlockMined))

    def minePendingTransactions(self, miningAddress: str, onBlockMined = None):
        # Constructs and mines a new block. If a block is mined and added
        # prior to the mining being stopped or another block being added,
        # onBlockedMined will be called with the new block.
        with self.__lock:
            if not self.__pending:
                return
            if self.__mining:
                return
            self.__mining = True

            trans = []
            trans.append(transaction.transaction(None, miningAddress, self.__miningReward))
            trans.extend(self.__pending)
            b = block.block(self.__chain[-1].hash(), trans)
            self.__pending = []

        self.__keepMining = True
        while self.__keepMining:
            if b.mineBlock(miningAddress, self.__difficulty):
                # Found a nonce which works! Check that the block hasn't grown
                # and we just happened to miss it, then append our new block and return it.
                with self.__lock:
                    self.__keepMining = False
                    # TODO: What should be do if another block is here? Should we find
                    # any transactions it was missing and put them back into the pending?
                    if self.__chain[-1].hash() == b.previousHash():
                        self.__chain.append(b)
                        if onBlockMined:
                            onBlockMined(b)
                break
        self.__mining = False
