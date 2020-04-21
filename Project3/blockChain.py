#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

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

    def __str__(self) -> str:
        # Gets a string for this transaction.
        parts = []
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

    def lastBlock(self) -> block:
        # Returns the last block added to the chain.
        return self.__chain[-1]

    def addTransaction(self, fromAccount: str, toAccount: str, amount: float) -> bool:
        # Creates a new transaction and adds it to the pending
        # transactions to wait to be added to a block during the next mine.
        trans = transaction.transaction(fromAccount, toAccount, amount)
        if trans.isValid():
            self.__pending.append(trans)
            return True
        return False

    def getAccounts(self) -> [str]:
        # Gets a list of all the accounts in the chain.
        accounts = {}
        for block in self.__chain:
            for trans in block.transactions():
                accounts[trans.fromAddress()] = True
                accounts[trans.toAddress()]   = True
        return accounts.keys()

    def getBalance(self, account: str) -> float:
        # Gets the balance for a single account in the chain.
        amount = 0.0
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
        for block in self.__chain:
            for trans in block.transactions():
                accounts[trans.fromAddress()] -= trans.amount()
                accounts[trans.toAddress()]   += trans.amount()
        return accounts

    def isValid(self) -> bool:
        # Indicates if this block chain is valid.
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

    def minePendingTransactions(self, miningAddress: str) -> block:
        # Constructs and mines a new block. If None is returned there are no
        # transactions to mine or the mining has been stopped before finishing.
        # Unless stopped this method will not return.        
        if not self.__pending:
            return None

        trans = []
        trans.append(transaction.transaction(None, miningAddress, self.__miningReward))
        trans.extend(self.__pending)
        b = block.block(self.lastBlock().hash(), trans)

        self.__pending = []
        self.__keepMining = True
        while self.__keepMining:
            if b.mineBlock(miningAddress, self.__difficulty):
                self.__chain.append(b)
                return b
        return None
