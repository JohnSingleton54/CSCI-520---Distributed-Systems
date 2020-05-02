#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import block
import transaction
import misc


ignoreBlock       = "ignoreBlock"
needMoreBlockInfo = "needMoreBlockInfo"
blocksAdded       = "blocksAdded"


class Blockchain:
    # The blockchain and current configurations.

    def __init__(self, creator: str, probability: float):
        # Creates a new block chain.
        self.creator     = creator
        self.probability = probability
        self.chain       = []
        self.pending     = [] # pending transactions
        self.candidates  = [] # candidate blocks needing to be voted on

    def __str__(self) -> str:
        # Gets a string for this transaction.
        parts = []
        parts.append("blocks:")
        for block in self.chain:
            parts.append("  "+str(block).replace("\n", "\n  "))
        parts.append("pending:")
        for tran in self.pending:
            parts.append("  "+str(tran).replace("\n", "\n  "))
        parts.append("candidates:")
        for block in self.candidates:
            parts.append("  "+str(block).replace("\n", "\n  "))
        return "\n".join(parts)

    def toTuple(self) -> {}:
        # Creates a dictionary for this block chain.
        # This will not persist candidate blocks.
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
        # This will not override the candidate blocks.
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
        return misc.insertSort(self.pending, tran)

    def removeTransaction(self, tran: transaction.Transaction) -> bool:
        # Removes a transition from the pending transactions.
        # This will return True if removed, False if already doesn't exist.
        return misc.removeFromSorted(self.pending, tran)

    def getAllBalances(self) -> {str: float}:
        # Gets a dictionary of account to balance.
        runningBalances = {}
        for b in self.chain:
            b.updateBalance(runningBalances)
        return runningBalances

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

            # Check if the creator was allowed to create the block.
            if not self.__isAllowedToCreateBlock(prevHash, b.creator, b.timestamp, verbose):
                if verbose:
                    print("Block %d is not allowed to created by that creator yet" % (i))
                return False

            if not b.isValid(runningBalances, verbose):
                if verbose:
                    print("Block %d is not valid" % (i))
                return False

            if b.previousHash != prevHash:
                if verbose:
                    print("Block %d has the wrong previous hash" % (i))
                return False

            prevHash = b.hash
        return True

    def addCandidateBlock(self, block: block.Block, verbose: bool = False) -> str:
         # Determine if the new is at or past the end of the chain. If not, ignore it.
        index = block.blockNum
        if index < len(self.chain):
            if verbose:
                print("Ignore candidate block at %d, we have %d which is longer" % (
                    index, len(self.chain)))
            return ignoreBlock

        if index > len(self.chain):
            if verbose:
                print("Candidate block %d is past the last known block %d, so request more information" % (
                    index, len(self.chain)))
            return needMoreBlockInfo

        # Validate the new candidate block
        if not self.isChainValid([block], index, self.lastHash(), verbose):
            if verbose:
                print("Candidate block was invalid")
            return ignoreBlock

        # Check if the candidate already exists, is an too old, or if the creator already added one
        # (keep newest but drops stake on oldest). Remove any old candidates by block number.
        for i in reversed(range(len(self.candidates))):
            other = self.candidates[i]
            if (other.hash == block.hash) or (other.blockNum > block.blockNum):
                return ignoreBlock
            
            if other.creator == block.creator:
                if other.timestamp < block.timestamp:
                    del self.candidates[i]
                    continue
                else:
                    return ignoreBlock
            
            if other.blockNum < block.blockNum:
                del self.candidates[i]
                continue

        # Add block to candidates
        self.candidates.append(block)
        if verbose:
            print("Candidate block was added")
        return blocksAdded

    def setBlocks(self, blocks: [block.Block], verbose: bool = False) -> str:
        # Adds and replaces blocks in the chain with the given blocks.
        # The blocks are only replaced if valid otherwise no change and false is returned.
        if not blocks:
            if verbose:
                print("Ignore empty block set")
            return ignoreBlock
        
        # Determine if the new blocks will make this chain longer. If not, ignore it.
        index = blocks[0].blockNum
        if index + len(blocks) <= len(self.chain):
            if verbose:
                print("Ignore %d blocks starting at %d, we have %d which is longer" % (len(blocks), index, len(self.chain)))
            return ignoreBlock

        if index > len(self.chain):
            if verbose:
                print("Block %d is past the last known block %d, so request more information" % (index, len(self.chain)))
            return needMoreBlockInfo

        # Validate the knew blocks
        if not self.isChainValid(blocks, index, self.lastHash(), verbose):
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

    def shouldCreateNextBlock(self, timestamp, verbose: bool = False) -> bool:
        # Determines if this block chain should create the next block.
        return self.__isAllowedToCreateBlock(self.lastHash(), self.creator, timestamp, verbose)

    def __isAllowedToCreateBlock(self, prevHash, creator: str, timestamp: float, verbose: bool = False) -> bool:
        # Determines if the given creator was permitted to create the block.
        data = misc.hashData({
            "previousHash": prevHash,
            "creator":      creator,
            "timestamp":    timestamp,
        })
        return misc.coinToss(data, self.probability, verbose)

    def createNextBlock(self, timestamp: float) -> block.Block:
        # Constructs a new block. Will use but not clear out pending transactions.
        balances = self.getAllBalances()
        trans = []
        for tran in self.pending:
            # In Python, dictionaries are mutable objects. balances is a dictionary and the method
            # isValid does update balances appropriately each time it is called.
            if tran.isValid(balances):
                trans.append(tran)
        blockNum = len(self.chain)
        return block.Block(timestamp, blockNum, self.lastHash(), self.creator, trans)
