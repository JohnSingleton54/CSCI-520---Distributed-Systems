#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import math

import transaction
import misc


initialHash = "0"*64


class Block:
    # Stores a single block in the chain.
    # It contains a set of transactions since the prior chain.

    def __init__(self, timestamp: float = 0.0, blockNum: int = 0,
        previousHash = None, creator: str = "", transactions: [transaction] = []):
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
        parts.append("  signatures: %s" % (", ".join(self.signatures)))
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
            "signatures":   self.signatures,
            "transactions": trans,
        }

    def fromTuple(self, data: {}):
        # This loads a block from the given tuple.
        self.blockNum      = data["blockNum"]
        self.timestamp     = data["timestamp"]
        self.previousHash  = data["previousHash"]
        self.hash          = data["hash"]
        self.creator       = data["creator"]
        self.signatures    = data["signatures"]
        self.transactions  = []
        for subdata in data["transactions"]:
            t = transaction.Transaction()
            t.fromTuple(subdata)
            self.transactions.append(t)

    def addSignature(self, sign) -> bool:
        # Add a signature to this block.
        # Returns true if signature was added, False otherwise.
        if sign == self.creator:
            # May not sign your own block
            return False
        for other in self.signatures:
            if other == sign:
                # Already signed so ignore
                return False
        self.signatures.append(sign)
        return True

    def totalTransactionCost(self) -> float:
        # Gets the total of the transactions in this block.
        runningBalances = {}
        for tran in self.transactions:
            tran.updateBalance(runningBalances)

        # This gets the running balance first to get the overall money movement
        # that way a large amount of transactions back and forth between two accounts
        # doesn't cause a total transaction over the full sum of all coins like simply
        # summing up the amounts in all the transactions.
        total = 0.0
        for balance in runningBalances.values():
            total = math.abs(balance)

        # Half the total transaction but not the total fees.
        # Half, since the total has both sender and receiver.
        fees = transaction.transactionFee * len(self.transactions)
        return (total - fees) * 0.5 + fees

    def calculateHash(self):
        # Calculates the hash for this whole block, excluding the hash value.
        data = self.toTuple()
        del data["hash"]
        return misc.hashData(data)

    def updateBalance(self, runningBalances: {str: float}):
        # Updates the given running Balances
        for tran in self.transactions:
            tran.updateBalance(runningBalances)
        self.__updateWithValidatorPayout(runningBalances)

    def __updateWithValidatorPayout(self, runningBalances: {str: float}):
        # Updates the running balances for the transaction fee payouts.
        # The creator and all the signers will receive an equal amount.
        totalFee = transaction.transactionFee * len(self.transactions)
        payoutAmount = totalFee / (len(self.signatures) + 1) # "+1" for the creator

        # This idea: Since there will need to be less signers if the signer has higher
        # stake, and with signers getting an equal payout, the payout is higher for
        # with less. However, since is isn't directly proportional to the stake it
        # helps with the rich-get-richer problem.
        runningBalances[self.creator] = runningBalances.get(self.creator, 0.0) + payoutAmount
        for signer in self.signatures:
            runningBalances[signer] = runningBalances.get(signer, 0.0) + payoutAmount

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

        for i in range(len(self.signatures)):
            signer = self.signatures[i]
            if not signer:
                if verbose:
                    print("Block %d has an empty signer name at %d" % (self.blockNum, i))
                return False
            if signer == self.creator:
                if verbose:
                    print("Block %d may not have the creator %s as the signer at %d" % (self.blockNum, signer, i))
                return False

        for i in range(len(self.transactions)):
            if not self.transactions[i].isValid(runningBalances, verbose):
                if verbose:
                    print("Block %d has transaction %d which is not valid" % (self.blockNum, i))
                return False

        # The transaction.isValid will update the rest of the balance (to allow sub-block
        # transactions which go over the balance before the block) so not just update
        # the balance for the transaction fees payout.
        self.__updateWithValidatorPayout(runningBalances)
        return True
