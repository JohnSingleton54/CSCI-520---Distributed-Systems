#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import block
import transaction
import misc


ignoreAddBlock = 0
needMoreBlockInfo = 1
blocksAdded = 2


class Blockchain:
    # The blockchain and current configurations.

    def __init__(self):
        # Creates a new block chain.
        self.chain   = []
        self.pending = []  # pending transactions

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
            "blocks":  blocks,
            "pending": pending,
        }

    def fromTuple(self, data: {}):
        # This loads a block chain from the given tuple.
        self.chain = []
        for subdata in data["blocks"]:
            b = block.Block()
            b.fromTuple(subdata)
            self.chain.append(b)

        self.pending = []
        for subdata in data["pending"]:
            t = transaction.Transaction()
            t.fromTuple(subdata)
            self.pending.append(t)

    def lastBlock(self):
        # Returns the last block in the chain.
        if self.chain:
            return self.chain[-1]
        return None

    def lastHash(self):
        # Returns the last hash in the chain.
        if self.chain:
            return self.chain[-1].hash
        return block.initialHash

    def listHashes(self) -> []:
        # Returns all the hashes in the current chain.
        hashes = []
        for b in self.chain:
            hashes.append(b.hash)
        return hashes

    def getHashDiffIndex(self, otherHashes: []) -> int:
        # Gets the index at which the hashes differ with the
        # assumption that other hashes is a smaller chain.
        length = len(otherHashes)
        if len(self.chain) <= length:
            # The other hash is longer or equal so there is no point in finding the diffs.
            return -1
        for i in range(length):
            if self.chain[i].hash != otherHashes[i]:
                return i
        return length

    def getDifferenceTuple(self, otherHashes: []) -> []:
        # Returns the tuples of the blocks for the differences between the chains.
        # Will return empty if the other hash is less than or equal to this chain.
        index = self.getHashDiffIndex(otherHashes)
        diff = []
        if index >= 0:
            for b in self.chain[index:]:
                diff.append(b.toTuple())
        return diff

    def newTransaction(self, fromAccount: str, toAccount: str, amount: float) -> transaction.Transaction:
        # Creates a new transaction and adds it to the pending
        # transactions to wait to be added to a new block.
        trans = transaction.Transaction(fromAccount, toAccount, amount)
        self.addTransaction(trans)
        return trans

    def addTransaction(self, tran: transaction.Transaction) -> bool:
        # Adds a transaction to the pending transactions to wait to be added
        # to a new block. The transaction will be sorted in.
        # This will return True if added, False if already exists.
        for i in range(len(self.pending)):
            cmp = self.pending[i].compare(tran)
            if cmp == 0:
                return False
            if cmp > 0:
                self.pending.insert(i, tran)
                return True
        self.pending.append(tran)
        return True

    def removeTransaction(self, tran: transaction.Transaction) -> bool:
        # Removes a transition from the pending transactions.
        # This will return True if removed, False if already doesn't exist.
        for i in range(len(self.pending)):
            cmp = self.pending[i].compare(tran)
            if cmp == 0:
                del self.pending[i]
                return True
            if cmp > 0:
                return False
        return False
        
    def getBalance(self, account: str) -> float:
        # Gets the balance for the given account.
        balance = 0.0
        for b in self.chain:
            if account == b.validatorAccount:
                balance += b.validatorReward
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
            accounts[b.validatorAccount] = accounts.get(b.validatorAccount, 0.0) + b.validatorReward
            for tran in b.transactions:
                accounts[tran.fromAccount] = accounts.get(tran.fromAccount, 0.0) - tran.amount
                accounts[tran.toAccount]   = accounts.get(tran.toAccount,   0.0) + tran.amount
        return accounts

    def isValid(self, verbose: bool = False) -> bool:
        # Indicates if this blockchain is valid.
        return self.isChainValid(self.chain, 0, block.initialHash, verbose)

    def isChainValid(self, chain: [block.Block], blockNumOffset, prevHash, verbose: bool = False) -> bool:
        # Indicates if this given chain is valid.
        runningBalances = {}
        for i in range(len(chain)):
            b = chain[i]

            if b.blockNum != i + blockNumOffset:
                if verbose:
                    print("Block %d has the block number %d" % (i + blockNumOffset, b.blockNum))
                return False

            if not b.isValid(self.difficulty, self.validatorReward, runningBalances, verbose):
                if verbose:
                    print("Block %d is not valid" % (i))
                return False

            if b.previousHash != prevHash:
                if verbose:
                    print("Block %d has the wrong previous hash" % (i))
                return False

            prevHash = b.hash
        return True

    def setBlocks(self, blocks: [block.Block], verbose: bool = False) -> int:
        # Adds and replaces blocks in the chain with the given blocks.
        # The blocks are only replaced if valid otherwise no change and false is returned.
        if not blocks:
            if verbose:
                print("Ignore empty block set")
            return ignoreAddBlock
        
        # Determine if the new blocks will make this chain longer. If not, ignore it.
        index = blocks[0].blockNum
        if index + len(blocks) <= len(self.chain):
            if verbose:
                print("Ignore %d blocks starting at %d, we have %d which is longer" % (len(blocks), index, len(self.chain)))
            return ignoreAddBlock

        if index > len(self.chain):
            if verbose:
                print("Block %d is past the last known block %d, so request more information" % (index, len(self.chain)))
            return needMoreBlockInfo

        # Validate the knew blocks
        prevHash = block.initialHash
        if index > 0:
            prevHash = self.chain[index-1].hash
        if not self.isChainValid(blocks, index, prevHash, verbose):
            if verbose:
                print("Request more information because constructed chain was invalid")
            return needMoreBlockInfo

        # Build new chain
        newChain = []
        newChain.extend(self.chain[:index])
        newChain.extend(blocks)

        # Check for matching or lost transactions and update pending.
        for b in self.chain[index:]:
            for t in b.transactions:
                self.addTransaction(t)
        for b in blocks:
            for t in b.transactions:
                self.removeTransaction(t)
        self.chain = newChain
        if verbose:
            print("Blocks were added")
        return blocksAdded

    def buildNextBlock(self, creator: str) -> block.Block:
        # Constructs a new block. Will use but not clear out pending transactions.
        balances = self.getAllBalances()
        trans = []
        for tran in self.pending:
            # In Python, dictionaries are mutable objects. balances is a dictionary and the method
            # isValid does update balances appropriately each time it is called.
            if tran.isValid(balances):
                trans.append(tran)
        blockNum = len(self.chain)
        return block.Block(blockNum, self.lastHash(), creator, trans)
