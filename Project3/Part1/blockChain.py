#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import threading

import block
import transaction
import misc


class blockChain:
    # The block chain and current configurations.

    def __init__(self, difficulty: int, minerReward: float):
        # Creates a new block chain.
        self.difficulty  = difficulty
        self.minerReward = minerReward
        self.chain       = []
        self.pending     = []  # pending transactions
        self.keepMining  = True

    def __str__(self) -> str:
        # Gets a string for this transaction.
        parts = []
        parts.append("blocks:")
        for block in self.chain:
            parts.append("  "+str(block).replace("\n", "\n  "))
        parts.append("pending:")
        for tran in self.pending:
            parts.append("  "+str(tran).replace("\n", "\n  "))
        return "\n".join(parts)

    def toTuple(self) -> {}:
        # Creates a dictionary for this block chain.
        blocks = []
        for block in self.chain:
            blocks.append(block.toTuple())
        pending = []
        for tran in self.pending:
            pending.append(tran.toTuple())
        return {
            # No need to output difficulty or mining reward
            "blocks":  blocks,
            "pending": pending,
        }

    def fromTuple(self, data: {}):
        # This loads a block chain from the given tuple.
        self.chain = []
        for subdata in data["blocks"]:
            b = block.block()
            b.fromTuple(subdata)
            self.chain.append(b)

        self.pending = []
        for subdata in data["pending"]:
            t = transaction.transaction()
            t.fromTuple(subdata)
            self.pending.append(t)

    def lastHash(self):
        # Returns the last hash in the chain.
        if self.chain:
            return self.chain[-1].hash
        return block.initialHash

    def newTransaction(self, fromAccount: str, toAccount: str, amount: float) -> transaction:
        # Creates a new transaction and adds it to the pending
        # transactions to wait to be added to a block during the next mine.
        trans = transaction.transaction(fromAccount, toAccount, amount)
        self.addTransaction(trans)
        return trans

    def addTransaction(self, trans: transaction):
        # Adds a transition to the pending transactions to wait
        # to be added to a block during the next mine.
        self.pending.append(trans)
        self.pending.sort(key=transaction.toSortKey)
        
    def getBalance(self, account: str) -> float:
        # Gets the balance for the given account.
        balance = 0.0
        for b in self.chain:
            if account == b.minerAccount:
                balance += b.minerReward
            for tran in b.transactions:
                if account == tran.fromAccount:
                    balance -= tran.amount
                if account == tran.toAccount:
                    balance += tran.amount
        return balance

    def getAllBalances(self) -> {str: float}:
        # Gets a dictionary of account to balance.
        accounts = {}
        for b in self.chain:
            accounts[b.minerAccount] = accounts.get(b.minerAccount, 0.0) + b.minerReward
            for tran in b.transactions:
                accounts[tran.fromAccount] = accounts.get(tran.fromAccount, 0.0) - tran.amount
                accounts[tran.toAccount]   = accounts.get(tran.toAccount,   0.0) + tran.amount
        return accounts

    def isValid(self, verbose: bool = False) -> bool:
        # Indicates if this block chain is valid.
        return self.isChainValid(self.chain, verbose)

    def isChainValid(self, chain: [block.block], verbose: bool = False) -> bool:
        # Indicates if this given chain is valid.
        prevHash = block.initialHash
        runningBalances = {}
        for i in range(len(chain)):
            b = chain[i]

            if b.blockNum != i:
                if verbose:
                    print("Block %d has the block number %d" % (i, b.blockNum))
                return False

            if not b.isValid(self.difficulty, self.minerReward, runningBalances, verbose):
                if verbose:
                    print("Block %d is not valid" % (i))
                return False

            if b.previousHash != prevHash:
                if verbose:
                    print("Block %d has the wrong previous hash" % (i))
                return False

            prevHash = b.hash
        return True

    def setBlocks(self, index: int, blocks: [block.block]) -> bool:
        # Adds and replaces blocks in the chain with the given blocks.
        # The blocks are only replaced if valid otherwise no change and false is returned.
        newChain = []
        newChain.extend(self.chain[:index])
        newChain.extend(blocks)
        if self.isChainValid(newChain):
            self.chain = newChain
            return True
        return False

    def stopMining(self):
        # Stops the mining loop.
        self.keepMining = False

    def minePendingTransactions(self, miningAccount: str, onBlockMined = None):
        # Constructs and mines a new block. If a block is mined and added
        # prior to the mining being stopped or another block being added,
        # onBlockedMined will be called with the new block.
        balances = self.getAllBalances()
        trans = []
        for tran in self.pending:
            if tran.isValid(balances):
                trans.append(tran)
        self.pending = []
        blockNum = len(self.chain)
        b = block.block(blockNum, self.lastHash(), miningAccount, self.minerReward, trans)

        self.keepMining = True
        while self.keepMining:
            # This picks a nonce and rehashes this block. It checks if the difficulty
            # challenge has been reached. Returns true if this attempt was successful, false otherwise.
            b.nonce = misc.newNonce()
            b.hash = b.calculateHash()
            if str(b.hash).startswith('0'*self.difficulty):
                # Found a nonce which works! Check that the block hasn't grown
                # and we just happened to miss it, then append our new block and return it.
                self.keepMining = False
                # TODO: What should be do if another block is here? Should we find
                # any transactions it was missing and put them back into the pending?
                if self.lastHash() == b.previousHash:
                    self.chain.append(b)
                    if onBlockMined:
                        onBlockMined(b)
                break
