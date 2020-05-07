#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

# JMS - 'python3 main.py 0'

# References:
# 1. https://blog.goodaudience.com/how-a-miner-adds-transactions-to-the-blockchain-in-seven-steps-856053271476

import threading
import sys
import json

import sockets
import asyncBlockchain
import blockchain
import block
import transaction


useServerHost = False
socketURLs = [
    "35.155.81.205:8080",
    "54.244.147.5:8080",
    "100.26.186.49:8080",
    "34.239.125.175:8080",
]
miners = [
    "bob",
    "ted",
    "sal",
    "kim",
]


if len(sys.argv) != 2:
    print("Must provide a node ID")
    quit()

myNodeId = int(sys.argv[1])
print("My node Id is %d" % (myNodeId))
minerAccount = miners[myNodeId]
print("My miner account is %s" % (minerAccount))

# What are the ranges of possible values for difficulty and miningReward?
# difficulty is the target number of leading zeros of the hash in hexadecimal format (256 / 4 = 64 characters)
# Therefore difficulty is an integer in [0, 64].

# JMS - What are the ranges of possible values for difficulty and miningReward?
# GJN - On my machine 4 is about once a second, smaller will be faster.
#       5 is about once every 10 seconds or so. The difficulty must be between 1 and 63
#       but we can do some math to determine what a good range is. With 1 we must
#       have 1 zero at the front of a hex number, therefore 1:16, or on average 8 tries to
#       find a nonce which satisfies that difficulty. 2 zeros is then 1:256, 3 zeros is
#       1:4096, N is 1:16^N. So if it takes 10 ms (for example) to try a single nonce
#       then with a difficulty of 4 (1:32768) it will take on average 5.46 minutes
#       (obviously we are faster than 10 ms per single nonce).
#       The miningReward is arbitrary since that's just how much our own crypto currency grows.
difficulty = 6
miningReward = 1.0

#import hashlib
#test = bytearray(str(54), 'utf-8')
#print("JMS2", hashlib.sha256(test).hexdigest())


class MainLoop:
    def __init__(self):
        self.sock = sockets.SocketManager(
            myNodeId, self.__onConnected, self.__onMessage, self.__onClosed
        )
        self.sock.startFullyConnected(socketURLs, useServerHost)
        self.bc = asyncBlockchain.AsyncBlockchain(
            difficulty, miningReward, minerAccount, self.__onBlockedMined)
        self.__loadFromFile()
        self.bc.startMining()

    def __onConnected(self, nodeId: int):
        print("Connected to", nodeId)
        # Check if the other connection is more up-to-date (has a longer chain)
        self.__requestMoreInfo(nodeId)

    def __onClosed(self, nodeId: int):
        print("Connection to", nodeId, "closed")

    def __printInfo(self):
        print("My node Id is %d" % (myNodeId))
        print("My miner account is %s" % (minerAccount))
        print("Difficulty is %d" % (difficulty))
        print("Mining reward is %s" % (miningReward))

    def __getFileName(self):
        # Gets the name of the chain file for this node ID.
        # JMS - Q: Why does the following print statement execute every few seconds?
        # JMS - A: This method is called once by method __loadFromFile and then periodically by
        # JMS -    method __saveToFile.
        #str0 = 'chain%d.json' % myNodeId
        #print("JMS0", str0)
        return 'chain%d.json' % myNodeId

    def __saveToFile(self):
        #print("JMS1", "in method __saveToFile")
        data = json.dumps(self.bc.toTuple())  
        f = open(self.__getFileName(), 'w')
        f.write(data)
        f.close()

    def __loadFromFile(self):
        try:
            f = open(self.__getFileName(), 'r')
            data = f.read()
            f.close()
            if data:
                self.bc.fromTuple(json.loads(data))
        except FileNotFoundError:
            # Ignore file not found since that fine, we just start from scratch
            # and will request for more information from the other servers anyway.
            pass
        except Exception as e:
            print('Failed to load from log file: %s' % (e))

    def __requestMoreInfo(self, nodeId: int = -1):
        hashes = self.bc.listHashes()
        msg = json.dumps({
            "Type": "NeedMoreInfo",
            "Hashes": hashes
        })
        if nodeId < 0:
            self.sock.sendToAll(msg)
        else:
            self.sock.sendTo(nodeId, msg)

    def __onRemoteAddTransaction(self, data: {}):
        t = transaction.Transaction()
        t.fromTuple(data)
        self.bc.addTransaction(t)

    def __onRemoteAddBlock(self, data: {}):
        b = block.Block()
        b.fromTuple(data)
        result = self.bc.setBlocks([b], True)
        if result == blockchain.blocksAdded:
            # A block was added so stop mining the
            # current block and start the next one.
            self.bc.restartMining()
            self.__saveToFile()
        elif result == blockchain.needMoreBlockInfo:
            # The block we tried to add was for a possibly longer chain.
            self.__requestMoreInfo()
        # else ignoreAddBlock and do nothing.

    def __onRemoteNeedMoreInfo(self, hashes: [], nodeId: int):
        diff = self.bc.getDifferenceTuple(hashes)
        if diff:
            self.sock.sendTo(nodeId, json.dumps({
                "Type": "ReplyWithInfo",
                "Diff": diff
            }))

    def __onRemoteReplayWithInfo(self, dataList: {}):
        blocks = []
        for data in dataList:
            b = block.Block()
            b.fromTuple(data)
            blocks.append(b)
        result = self.bc.setBlocks(blocks, True)
        if result == blockchain.blocksAdded:
            # The missing block(s) were added so stop mining the
            # current block and start the next one.
            self.bc.restartMining()
            self.__saveToFile()
        # else needMoreBlockInfo or ignoreAddBlock which
        # probably means the data is invalid so do nothing.bo

    def __onMessage(self, nodeId: int, message: str):
        try:
            data = json.loads(message)
        except Exception as e:
            print("Error receiving message:", e)
            return
        dataType = data["Type"]
        if dataType == "AddTransaction":
            self.__onRemoteAddTransaction(data["Transaction"])
        elif dataType == "AddBlock":
            self.__onRemoteAddBlock(data["Block"])
        elif dataType == "NeedMoreInfo":
            self.__onRemoteNeedMoreInfo(data["Hashes"], nodeId)
        elif dataType == "ReplyWithInfo":
            self.__onRemoteReplayWithInfo(data["Diff"])
        else:
            print("Unknown message from %d:" % (nodeId), message)

    def __makeTransaction(self):
        fromAccount = str(input("From: "))
        toAccount = str(input("To: "))
        amount = float(input("Amount: "))
        trans = self.bc.newTransaction(fromAccount, toAccount, amount)
        if trans:
            self.sock.sendToAll(json.dumps({
                "Type": "AddTransaction",
                "Transaction": trans.toTuple()
            }))
        else:
            print("Invalid transaction")

    def __onBlockedMined(self, block):
        self.sock.sendToAll(json.dumps({
            "Type": "AddBlock",
            "Block": block.toTuple()
        }))
        self.__saveToFile()

    def __showFullChain(self):
        print(self.bc)

    def __showLastBlock(self):
        print(self.bc.lastBlock())

    def __showBalances(self):
        balances = self.bc.getAllBalances()
        print("Balances:")
        for account in balances:
            print("  %s = %f" % (account, balances[account]))

    def run(self):
        while True:
            print("What would you like to do?")
            print("  1. Info")
            print("  2. Make Transaction")
            print("  3. Show Full Chain")
            print("  4. Show Last Block")
            print("  5. Show Balances")
            print("  6. Exit")

            try:
                choice = int(input("Enter your choice: "))
            except:
                print("Invalid choice. Try again.")
                continue

            if choice == 1:
                self.__printInfo()
            elif choice == 2:
                self.__makeTransaction()
            elif choice == 3:
                self.__showFullChain()
            elif choice == 4:
                self.__showLastBlock()
            elif choice == 5:
                self.__showBalances()
            elif choice == 6:
                break
            else:
                print('Invalid choice "%s". Try again.' % (choice))

        print("Closing...")
        self.sock.close()
        self.bc.stopMining()


if __name__ == "__main__":
    MainLoop().run()
