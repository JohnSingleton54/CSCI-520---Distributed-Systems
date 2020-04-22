#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import unittest
import json
import types

import blockChain
import block
import transaction
import misc


def constantTime() -> float:
    return 1587222721.0  # 18 Apr 2020 09:12:01

# Override the misc.newTime to return a constant time.
misc.newTime = constantTime


nonRandomValue = -1
def nonRandomNonce() -> int:
    global nonRandomValue
    nonRandomValue += 1
    return nonRandomValue

misc.newNonce = nonRandomNonce


class TestBlockChain(unittest.TestCase):

    def test_allPending(self):
        bc = blockChain.blockChain(3, 100.0)
        bc.newTransaction("bob", "jill", 4.0)
        bc.newTransaction("jill", "bob", 10.0)

        self.assertEqual(str(bc),
            "blocks:\n"+
            "  block: time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n" +
            "pending:\n"+
            "  tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 4.000000\n" +
            "  tran: time: 18 Apr 2020 09:12:01, from: jill, to: bob, amount: 10.000000")
        self.assertTrue(bc.isValid())
        self.assertEqual(bc.getBalance("jill"), 0.0)
        self.assertEqual(bc.getBalance("bob"), 0.0)
        
    def test_mineBlock(self):
        self.maxDiff = None
        bc = blockChain.blockChain(3, 100.0)
        bc.newTransaction("bob", "jill", 4.0)
        bc.newTransaction("jill", "bob", 10.0)
        bc.minePendingTransactions("tim")

        self.assertEqual(str(bc),
            "blocks:\n" +
            "  block: time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n" + 
            "  block: time: 18 Apr 2020 09:12:01, prev: None, hash: 000774ba923eb3a9875dc28536843c4722b0ae9e64b70efd93b35722694341eb, nonce: 1346, miner: tim\n" + 
            "    tran: time: 18 Apr 2020 09:12:01, from: None, to: tim, amount: 100.000000\n" + 
            "    tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 4.000000\n" + 
            "    tran: time: 18 Apr 2020 09:12:01, from: jill, to: bob, amount: 10.000000\n" +
            "pending:")
        self.assertTrue(bc.isValid())
        self.assertEqual(bc.getBalance("jill"), -6.0)
        self.assertEqual(bc.getBalance("bob"), 6.0)
        self.assertEqual(bc.getBalance("tim"), 100.0)
        self.assertEqual(bc.getBalance("sal"), 0.0)

    def checkToFromTuples(self, bc: blockChain.blockChain, expStr: str):
        self.maxDiff = None
        dataStr = json.dumps(bc.toTuple())
        self.assertTrue(isinstance(dataStr, str))

        bc2 = blockChain.blockChain(3, 100.0)
        bc2.fromTuple(json.loads(dataStr))
        self.assertEqual(str(bc), expStr)

    def test_toFromTuple(self):
        bc = blockChain.blockChain(3, 100.0)
        self.checkToFromTuples(bc,
            "blocks:\n"+
            "  block: time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n"+
            "pending:")

        bc.newTransaction("bob", "jill", 60.0)
        bc.newTransaction("jill", "bob", 10.0)
        bc.minePendingTransactions("bob")
        self.checkToFromTuples(bc,
            "blocks:\n"+
            "  block: time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n"+
            "  block: time: 18 Apr 2020 09:12:01, prev: None, hash: 000c0bec7b9defe5251903667e5cf9a7a2290261da360752cdd365d41e4266d6, nonce: 2912, miner: bob\n"+
            "    tran: time: 18 Apr 2020 09:12:01, from: None, to: bob, amount: 100.000000\n"+
            "    tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 60.000000\n"+
            "    tran: time: 18 Apr 2020 09:12:01, from: jill, to: bob, amount: 10.000000\n"+
            "pending:")

        bc.newTransaction("bob", "jill", 30.0)
        bc.newTransaction("jill", "bob", 20.0)
        self.checkToFromTuples(bc,
            "blocks:\n"+
            "  block: time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n"+
            "  block: time: 18 Apr 2020 09:12:01, prev: None, hash: 000c0bec7b9defe5251903667e5cf9a7a2290261da360752cdd365d41e4266d6, nonce: 2912, miner: bob\n"+
            "    tran: time: 18 Apr 2020 09:12:01, from: None, to: bob, amount: 100.000000\n"+
            "    tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 60.000000\n"+
            "    tran: time: 18 Apr 2020 09:12:01, from: jill, to: bob, amount: 10.000000\n"+
            "pending:\n"+
            "  tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 30.000000\n"+
            "  tran: time: 18 Apr 2020 09:12:01, from: jill, to: bob, amount: 20.000000")

if __name__ == '__main__':
    unittest.main()
