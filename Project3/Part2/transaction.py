#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import misc


# Amount of additional money take from the "fromAccount"
# beyond the amount to cover the transaction cost.
# This cost is divided among the validators.
transactionFee = 1.0


class Transaction:
    # A description of the transfer of some amount from one address to another.

    def __init__(self, fromAccount: str = "", toAccount: str = "", amount: float = 0.0):
        # Creates a new transaction.
        # No signature according to project requirements.
        self.timestamp   = misc.newTime()
        self.fromAccount = fromAccount
        self.toAccount   = toAccount
        self.amount      = amount

    def __str__(self) -> str:
        # Gets a string for this transaction.
        return "tran: time: %s, from: %s, to: %s, amount: %f" % (
            misc.timeToStr(self.timestamp), self.fromAccount, self.toAccount, self.amount)

    def toTuple(self) -> {}:
        # Creates a dictionary for this transaction.
        return {
            "timestamp":   self.timestamp,
            "fromAccount": self.fromAccount,
            "toAccount":   self.toAccount,
            "amount":      self.amount
        }

    def fromTuple(self, data: {}):
        # This loads a transaction from the given tuple.
        self.timestamp   = data["timestamp"]
        self.fromAccount = data["fromAccount"]
        self.toAccount   = data["toAccount"]
        self.amount      = data["amount"]

    def compare(self, other) -> int:
        # Determines how these two transactions compare.
        # less than zero for this transaction being less than the other.
        # greater than zero for this transaction being greater than the other.
        # equal to zero if the two transactions are equal.
        if self.timestamp < other.timestamp:
            return -1
        if self.timestamp > other.timestamp:
            return 1
        if self.fromAccount < other.fromAccount:
            return -1
        if self.fromAccount > other.fromAccount:
            return 1
        if self.toAccount < other.toAccount:
            return -1
        if self.toAccount > other.toAccount:
            return 1
        # Use epsilon comparator for amount since a float may not JSON perfectly.
        if abs(self.amount - other.amount) > 0.000001:
            if self.amount < other.amount:
                return -1
            if self.amount > other.amount:
                return 1
        # They are the same
        return 0
        
    def updateBalance(self, runningBalances: {str: float}):
        # Update the balances with this given transaction
        runningBalances[self.fromAccount] = runningBalances.get(self.fromAccount, 0.0) - (self.amount + transactionFee)
        runningBalances[self.toAccount]   = runningBalances.get(self.toAccount,   0.0) + self.amount

    def isValid(self, runningBalances: {str: float}, verbose: bool = False) -> bool:
        # Indicates if this transaction is valid.
        if self.amount <= 0:
            if verbose:
                print("Amount was %d <= 0" % (self.amount))
            return False

        if not self.fromAccount:
            if verbose:
                print("Must have a from account")
            return False

        if not self.toAccount:
            if verbose:
                print("Must have a to account")
            return False

        if runningBalances.get(self.fromAccount, 0.0) < self.amount + transactionFee:
            if verbose:
                print("Insufficient funds: %s has less than %d (with transaction fee)" % (
                    self.fromAccount, self.amount + transactionFee))
            return False
        
        self.updateBalance(runningBalances)
        return True
