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


class TestBlockChain(unittest.TestCase):

    def test_allPending(self):
        self.maxDiff = None
        misc.useTestTime()
        misc.useTestNonce()

        bc = blockChain.blockChain(3, 100.0)
        bc.newTransaction("bob", "jill", 4.0)
        bc.newTransaction("jill", "bob", 10.0)

        self.assertEqual(str(bc),
            "blocks:\n" +
            "pending:\n" +
            "  tran: time: 18 Apr 2020 09:12:01, from: bob, to: jill, amount: 4.000000\n" +
            "  tran: time: 18 Apr 2020 09:12:02, from: jill, to: bob, amount: 10.000000")
        self.assertTrue(bc.isValid())
        self.assertEqual(bc.getBalance("jill"), 0.0)
        self.assertEqual(bc.getBalance("bob"), 0.0)
        
    def test_mineBlock(self):
        self.maxDiff = None
        misc.useTestTime()
        misc.useTestNonce()

        bc = blockChain.blockChain(3, 100.0)
        bc.minePendingTransactions("bob")
        bc.newTransaction("bob", "jill", 10.0)
        bc.newTransaction("jill", "bob", 4.0)
        bc.minePendingTransactions("tim")

        self.assertEqual(str(bc),
            "blocks:\n" +
            "  block: 0, time: 18 Apr 2020 09:12:01, nonce: 5237, miner: bob, reward: 100.000000\n" +
            "    prev: 0000000000000000000000000000000000000000000000000000000000000000\n" +
            "    hash: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "  block: 1, time: 18 Apr 2020 09:12:04, nonce: 7589, miner: tim, reward: 100.000000\n" +
            "    prev: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "    hash: 000028d02d72fa5e78cee2e16da4b4c407728c2550ffac7866a5acb293e60a31\n" +
            "    tran: time: 18 Apr 2020 09:12:02, from: bob, to: jill, amount: 10.000000\n" +
            "    tran: time: 18 Apr 2020 09:12:03, from: jill, to: bob, amount: 4.000000\n" +
            "pending:")
            
        self.assertTrue(bc.isValid(True))
        self.assertEqual(bc.getBalance("jill"), 6.0)
        self.assertEqual(bc.getBalance("bob"), 94.0)
        self.assertEqual(bc.getBalance("tim"), 100.0)
        self.assertEqual(bc.getBalance("sal"), 0.0)

    def checkToFromTuples(self, bc: blockChain.blockChain, expStr: str):
        dataStr = json.dumps(bc.toTuple())
        self.assertTrue(isinstance(dataStr, str))

        bc2 = blockChain.blockChain(3, 100.0)
        bc2.fromTuple(json.loads(dataStr))
        self.assertEqual(str(bc), expStr)

    def test_toFromTuple(self):
        self.maxDiff = None
        misc.useTestTime()
        misc.useTestNonce()

        bc = blockChain.blockChain(3, 100.0)
        self.checkToFromTuples(bc,
            "blocks:\n"+
            "pending:")

        bc.minePendingTransactions("bob")
        self.checkToFromTuples(bc,
            "blocks:\n" +
            "  block: 0, time: 18 Apr 2020 09:12:01, nonce: 5237, miner: bob, reward: 100.000000\n" +
            "    prev: 0000000000000000000000000000000000000000000000000000000000000000\n" +
            "    hash: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "pending:")

        bc.newTransaction("bob", "jill", 60.0)
        bc.newTransaction("jill", "bob", 10.0)
        bc.minePendingTransactions("bob")
        self.checkToFromTuples(bc,
            "blocks:\n" +
            "  block: 0, time: 18 Apr 2020 09:12:01, nonce: 5237, miner: bob, reward: 100.000000\n" +
            "    prev: 0000000000000000000000000000000000000000000000000000000000000000\n" +
            "    hash: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "  block: 1, time: 18 Apr 2020 09:12:05, nonce: 7016, miner: bob, reward: 100.000000\n" +
            "    prev: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "    hash: 00058d694bf443b94d7a1322f18e5e8c777bcd41040caeedfd4afa53edf09768\n" +
            "    tran: time: 18 Apr 2020 09:12:03, from: bob, to: jill, amount: 60.000000\n" +
            "    tran: time: 18 Apr 2020 09:12:04, from: jill, to: bob, amount: 10.000000\n" +
            "pending:")

        bc.newTransaction("bob", "jill", 30.0)
        bc.newTransaction("jill", "bob", 20.0)
        self.checkToFromTuples(bc,
            "blocks:\n" +
            "  block: 0, time: 18 Apr 2020 09:12:01, nonce: 5237, miner: bob, reward: 100.000000\n" +
            "    prev: 0000000000000000000000000000000000000000000000000000000000000000\n" +
            "    hash: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "  block: 1, time: 18 Apr 2020 09:12:05, nonce: 7016, miner: bob, reward: 100.000000\n" +
            "    prev: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "    hash: 00058d694bf443b94d7a1322f18e5e8c777bcd41040caeedfd4afa53edf09768\n" +
            "    tran: time: 18 Apr 2020 09:12:03, from: bob, to: jill, amount: 60.000000\n" +
            "    tran: time: 18 Apr 2020 09:12:04, from: jill, to: bob, amount: 10.000000\n" +
            "pending:\n" +
            "  tran: time: 18 Apr 2020 09:12:10, from: bob, to: jill, amount: 30.000000\n" +
            "  tran: time: 18 Apr 2020 09:12:11, from: jill, to: bob, amount: 20.000000")

if __name__ == '__main__':
    unittest.main()
