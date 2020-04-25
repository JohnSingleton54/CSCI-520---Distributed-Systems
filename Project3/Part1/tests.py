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
            "  block: 0, time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n" +
            "pending:\n"+
            "  tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 4.000000\n" +
            "  tran: time: 18 Apr 2020 09:12:01, from: jill, to: bob, amount: 10.000000")
        self.assertTrue(bc.isValid())
        self.assertEqual(bc.getBalance("jill"), 0.0)
        self.assertEqual(bc.getBalance("bob"), 0.0)
        
    def test_mineBlock(self):
        self.maxDiff = None
        bc = blockChain.blockChain(3, 100.0)
        bc.minePendingTransactions("bob")
        bc.newTransaction("bob", "jill", 10.0)
        bc.newTransaction("jill", "bob", 4.0)
        bc.minePendingTransactions("tim")

        self.assertEqual(str(bc),
            "blocks:\n" +
            "  block: 0, time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n" + 
            "  block: 1, time: 18 Apr 2020 09:12:01, prev: None, hash: 0006871621c06c74c69dd7373956ea9e6b8fcc2741643d8c73a5f422c7fd3d0c, nonce: 3006, miner: tim\n" +
            "    tran: time: 18 Apr 2020 09:12:01, from: None, to: tim, amount: 100.000000\n" + 
            "    tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 4.000000\n" + 
            "    tran: time: 18 Apr 2020 09:12:01, from: jill, to: bob, amount: 10.000000\n" +
            "pending:")
        self.assertTrue(bc.isValid())
        self.assertEqual(bc.getBalance("jill"), -6.0)
        self.assertEqual(bc.getBalance("bob"), 6.0)
        self.assertEqual(bc.getBalance("tim"), 100.0)
        self.assertEqual(bc.getBalance("sal"), 0.0)

    # def checkToFromTuples(self, bc: blockChain.blockChain, expStr: str):
    #     self.maxDiff = None
    #     dataStr = json.dumps(bc.toTuple())
    #     self.assertTrue(isinstance(dataStr, str))

    #     bc2 = blockChain.blockChain(3, 100.0)
    #     bc2.fromTuple(json.loads(dataStr))
    #     self.assertEqual(str(bc), expStr)

    # def test_toFromTuple(self):
    #     bc = blockChain.blockChain(3, 100.0)
    #     self.checkToFromTuples(bc,
    #         "blocks:\n"+
    #         "  block: 0, time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n"+
    #         "pending:")

    #     bc.newTransaction("bob", "jill", 60.0)
    #     bc.newTransaction("jill", "bob", 10.0)
    #     bc.minePendingTransactions("bob")
    #     self.checkToFromTuples(bc,
    #         "blocks:\n"+
    #         "  block: 0, time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n"+
    #         "  block: 1, time: 18 Apr 2020 09:12:01, prev: None, hash: 000bc2351da378c5af3e1587408863545184e96da5d94e669224b81a45e3f102, nonce: 6879, miner: bob\n" +
    #         "    tran: time: 18 Apr 2020 09:12:01, from: None, to: bob, amount: 100.000000\n"+
    #         "    tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 60.000000\n"+
    #         "    tran: time: 18 Apr 2020 09:12:01, from: jill, to: bob, amount: 10.000000\n"+
    #         "pending:")

    #     bc.newTransaction("bob", "jill", 30.0)
    #     bc.newTransaction("jill", "bob", 20.0)
    #     self.checkToFromTuples(bc,
    #         "blocks:\n"+
    #         "  block: 0, time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n"+
    #         "  block: 1, time: 18 Apr 2020 09:12:01, prev: None, hash: 000bc2351da378c5af3e1587408863545184e96da5d94e669224b81a45e3f102, nonce: 6879, miner: bob\n" +
    #         "    tran: time: 18 Apr 2020 09:12:01, from: None, to: bob, amount: 100.000000\n"+
    #         "    tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 60.000000\n"+
    #         "    tran: time: 18 Apr 2020 09:12:01, from: jill, to: bob, amount: 10.000000\n"+
    #         "pending:\n"+
    #         "  tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 30.000000\n"+
    #         "  tran: time: 18 Apr 2020 09:12:01, from: jill, to: bob, amount: 20.000000")

if __name__ == '__main__':
    unittest.main()
