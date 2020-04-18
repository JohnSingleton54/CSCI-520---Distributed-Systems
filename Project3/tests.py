#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import unittest

import blockChain
import block
import transaction
import misc


def constantTime() -> float:
    return 1587222721.0  # 18 Apr 2020 09:12:01

# Override the misc.newTime to return a constant time.
misc.newTime = constantTime


class TestBlockChain(unittest.TestCase):

    def test_allPending(self):
        bc = blockChain.blockChain(3, 100.0)
        bc.addTransaction("bob", "jill", 4.0)
        bc.addTransaction("jill", "bob", 10.0)

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
        # TODO: Once we can mine the block then we can test it
        # block0 = block.block(bc.lastBlock().hash(), [
        #   transaction.transaction("bank", "bob", 100.0),
        #   transaction.transaction("bank", "jill", 100.0)])
        # bc.setBlocks(1, [block0])

        self.assertEqual(str(bc),
            "blocks:\n"+
            "  block: time: 18 Apr 2020 09:12:01, prev: None, hash: None, nonce: 0, miner: \n" +
            "pending:")
        self.assertTrue(bc.isValid())
        self.assertEqual(bc.getBalance("jill"), 0.0) # TODO: Once mined this will not be zero
        self.assertEqual(bc.getBalance("bob"), 0.0)


if __name__ == '__main__':
    unittest.main()
