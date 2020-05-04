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
validCandidate    = "validCandidate"


probability    = 0.25  # 25%
initialBalance = 100.0 # The amount to initialize all the validators with


class Blockchain:
    # The blockchain and current configurations.

    def __init__(self, creator: str, validators: [str]):
        # Creates a new block chain.
        self.creator    = creator
        self.validators = validators
        self.chain      = []
        self.pending    = [] # pending transactions
        self.candidate  = None

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
        # This will not persist candidate block.
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
        # This will not override the candidate block.
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

    def __getHashDiffIndex(self, otherHashes: []) -> int:
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
        index = self.__getHashDiffIndex(otherHashes)
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

    def __removeTransaction(self, tran: transaction.Transaction) -> bool:
        # Removes a transition from the pending transactions.
        # This will return True if removed, False if already doesn't exist.
        return misc.removeFromSorted(self.pending, tran)

    def __initialBalances(self) -> {str: float}:
        # This is the amount of money each person starts with
        runningBalances = {}
        for validator in self.validators:
            runningBalances[validator] = initialBalance
        return runningBalances

    def getAllBalances(self) -> {str: float}:
        # Gets a dictionary of account to balance.
        runningBalances = self.__initialBalances()
        for b in self.chain:
            b.updateBalance(runningBalances)
        return runningBalances

    def isValid(self, verbose: bool = False) -> bool:
        # Indicates if this blockchain is valid.
        return self.__isChainValid(self.chain, 0, block.initialHash, verbose)

    def __isChainValid(self, chain: [block.Block], blockNumOffset, prevHash, verbose: bool = False) -> bool:
        # Indicates if this given chain is valid.
        runningBalances = self.__initialBalances()
        for i in range(len(chain)):
            b = chain[i]

            if b.blockNum != i + blockNumOffset:
                if verbose:
                    print("Block %d has the block number %d" % (i + blockNumOffset, b.blockNum))
                return False

            # Check if the creator was allowed to create the block.
            permittedCreator = self.whoShouldCreateBlock(prevHash)
            if b.creator != permittedCreator:
                if verbose:
                    print("Block %d is not allowed to created by %s, the premitted creator was %s" % (
                        i, b.creator, permittedCreator))
                return False

            if not b.isValid(runningBalances, self.validators, verbose):
                if verbose:
                    print("Block %d is not valid" % (i))
                return False

            if b.previousHash != prevHash:
                if verbose:
                    print("Block %d has the wrong previous hash" % (i))
                return False

            prevHash = b.hash
        return True

    def validateCandidateBlock(self, block: block.Block, verbose: bool = False) -> str:
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
        if not self.__isChainValid([block], index, self.lastHash(), verbose):
            if verbose:
                print("Candidate block was invalid")
            return ignoreBlock

        # Add block to candidates
        if verbose:
            print("Candidate block was valid")
        return validCandidate

    def addSignature(self, sign: str, candidateHash) -> bool:
        # Add a signature to the candidate block.
        # Returns true if this signature was enough to add the block, false otherwise.
        if (not self.candidate) or (self.candidate.hash != candidateHash):
            return False
        if not self.candidate.addSignature(sign):
            return False
        
        balances = self.getAllBalances()
        totalStake = balances.get(self.creator, 0.0) # Put in the creator's stake
        for sign in self.candidate.signatures:
            totalStake += balances.get(sign, 0.0)

        totalTrans = self.candidate.totalTransactionCost()
        return totalStake >= totalTrans

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
        if not self.__isChainValid(blocks, index, self.lastHash(), verbose):
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
                self.__removeTransaction(t)
        self.chain = newChain
        if verbose:
            print("Blocks6 were added")
        return blocksAdded

    def shouldCreateNextBlock(self) -> bool:
        # Determines if this creator should be creating the next block or not.
        return self.whoShouldCreateBlock(self.lastHash()) == self.creator

    def whoShouldCreateBlock(self, prevHash) -> str:
        # Determines which of the validators should create the block.
        # This picks the smallest hash from all the people who won the coin toss,
        # if no one won the coin toss then the smallest hash of all the loosers is used.
        creator = None
        minHash = None
        wonToss = False
        for validator in self.validators:
            hashVal = misc.hashData({
                "previousHash": prevHash,
                "validator":    validator,
            })
            if misc.coinToss(hashVal, probability):
                if (not wonToss) or (not minHash) or (hashVal < minHash):
                    creator = validator
                    minHash = hashVal
                    wonToss = True
            elif (not wonToss) and ((not minHash) or (hashVal < minHash)):
                creator = validator
                minHash = hashVal
        return creator

    def createNextBlock(self) -> block.Block:
        # Constructs a new block. Will use but not clear out pending transactions.
        balances = self.getAllBalances()
        trans = []
        for tran in self.pending:
            # In Python, dictionaries are mutable objects. balances is a dictionary and the method
            # isValid does update balances appropriately each time it is called.
            if tran.isValid(balances):
                # If this was a "Real BlockChain" we would want to make sure that the number of
                # transactions is limited such that the total transaction cost isn't more than
                # the stake of all the possible signers.
                trans.append(tran)
        blockNum = len(self.chain)
        return block.Block(blockNum, self.lastHash(), self.creator, trans)
