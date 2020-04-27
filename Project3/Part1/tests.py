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

    def minePendingTransactions(self, chain, miningAccount: str):
        # Constructs and mines a new block. Designed for testing the block
        # chain synchronously. This will block execution until a new block is done.
        b = chain.buildNextBlock(miningAccount)
        while not chain.mineBlock(b):
            pass

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
        self.minePendingTransactions(bc, "bob")
        bc.newTransaction("bob", "jill", 10.0)
        bc.newTransaction("jill", "bob", 4.0)
        self.minePendingTransactions(bc, "tim")

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

        self.minePendingTransactions(bc, "bob")
        self.checkToFromTuples(bc,
            "blocks:\n" +
            "  block: 0, time: 18 Apr 2020 09:12:01, nonce: 5237, miner: bob, reward: 100.000000\n" +
            "    prev: 0000000000000000000000000000000000000000000000000000000000000000\n" +
            "    hash: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "pending:")

        bc.newTransaction("bob", "jill", 60.0)
        bc.newTransaction("jill", "bob", 10.0)
        self.minePendingTransactions(bc, "bob")
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

    def test_restorePending(self):
        self.maxDiff = None
        misc.useTestTime()
        misc.useTestNonce()

        bc1 = blockChain.blockChain(3, 100.0)
        self.minePendingTransactions(bc1, "bob")
        t1 = bc1.newTransaction("bob", "jill", 42.0)
        bc1.newTransaction("jill", "bob", 13.0)
        
        bc2 = blockChain.blockChain(3, 100.0)
        bc2.chain = bc1.chain.copy()
        bc2.newTransaction("bob", "kim", 5.0)
        bc2.addTransaction(t1)
        bc2.addTransaction(t1) # Duplicate should be ignored

        self.minePendingTransactions(bc1, "bob")
        self.minePendingTransactions(bc2, "jill")
        self.minePendingTransactions(bc1, "bob")  # make bob's chain longer
        
        self.assertEqual(str(bc1),
            "blocks:\n" +
            "  block: 0, time: 18 Apr 2020 09:12:01, nonce: 5237, miner: bob, reward: 100.000000\n" +
            "    prev: 0000000000000000000000000000000000000000000000000000000000000000\n" +
            "    hash: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "  block: 1, time: 18 Apr 2020 09:12:05, nonce: 8553, miner: bob, reward: 100.000000\n" +
            "    prev: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "    hash: 0001499713128fa45c28f805c545236194716e0d5e5479d969b4d84b5ae30fac\n" +
            "    tran: time: 18 Apr 2020 09:12:02, from: bob, to: jill, amount: 42.000000\n" +
            "    tran: time: 18 Apr 2020 09:12:03, from: jill, to: bob, amount: 13.000000\n" +
            "  block: 2, time: 18 Apr 2020 09:12:07, nonce: 14484, miner: bob, reward: 100.000000\n" +
            "    prev: 0001499713128fa45c28f805c545236194716e0d5e5479d969b4d84b5ae30fac\n" +
            "    hash: 00023d3590967cb36819f89b37a405f2b9b8b9c282589abeeadc48d43713ab35\n" +
            "pending:")

        self.assertEqual(str(bc2),
            "blocks:\n" +
            "  block: 0, time: 18 Apr 2020 09:12:01, nonce: 5237, miner: bob, reward: 100.000000\n" +
            "    prev: 0000000000000000000000000000000000000000000000000000000000000000\n" +
            "    hash: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "  block: 1, time: 18 Apr 2020 09:12:06, nonce: 12166, miner: jill, reward: 100.000000\n" +
            "    prev: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "    hash: 000737103ef35a9518ddbef2d7479de0206cd3deaaa6d484f9a347d73cf2cdee\n" +
            "    tran: time: 18 Apr 2020 09:12:02, from: bob, to: jill, amount: 42.000000\n" +
            "    tran: time: 18 Apr 2020 09:12:04, from: bob, to: kim, amount: 5.000000\n" +
            "pending:")

        hashes = bc2.listHashes()
        self.assertEqual(str(hashes),
            "['000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09',"+ 
            " '000737103ef35a9518ddbef2d7479de0206cd3deaaa6d484f9a347d73cf2cdee']")
        index = bc1.getHashDiffIndex(hashes)
        self.assertEqual(index, 1)
        
        hashes = bc1.listHashes()
        self.assertEqual(str(hashes),
            "['000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09',"+ 
            " '0001499713128fa45c28f805c545236194716e0d5e5479d969b4d84b5ae30fac',"+ 
            " '00023d3590967cb36819f89b37a405f2b9b8b9c282589abeeadc48d43713ab35']")
        index = bc2.getHashDiffIndex(hashes)
        self.assertEqual(index, -1)

        bc2.setBlocks(bc1.chain[1:3])
        
        self.assertEqual(str(bc2),
            "blocks:\n" +
            "  block: 0, time: 18 Apr 2020 09:12:01, nonce: 5237, miner: bob, reward: 100.000000\n" +
            "    prev: 0000000000000000000000000000000000000000000000000000000000000000\n" +
            "    hash: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "  block: 1, time: 18 Apr 2020 09:12:05, nonce: 8553, miner: bob, reward: 100.000000\n" +
            "    prev: 000f9a23d81617f55f488ded747a5dde654b22a59fd0f0164c475366e08bdc09\n" +
            "    hash: 0001499713128fa45c28f805c545236194716e0d5e5479d969b4d84b5ae30fac\n" +
            "    tran: time: 18 Apr 2020 09:12:02, from: bob, to: jill, amount: 42.000000\n" +
            "    tran: time: 18 Apr 2020 09:12:03, from: jill, to: bob, amount: 13.000000\n" +
            "  block: 2, time: 18 Apr 2020 09:12:07, nonce: 14484, miner: bob, reward: 100.000000\n" +
            "    prev: 0001499713128fa45c28f805c545236194716e0d5e5479d969b4d84b5ae30fac\n" +
            "    hash: 00023d3590967cb36819f89b37a405f2b9b8b9c282589abeeadc48d43713ab35\n" +
            "pending:\n" +
            "  tran: time: 18 Apr 2020 09:12:04, from: bob, to: kim, amount: 5.000000") # got put back in pending

if __name__ == '__main__':
    unittest.main()
