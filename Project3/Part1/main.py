#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

# JMS - 'python3 main.py 0'

import threading
import sys
import json

import sockets
import asyncBlockChain
import blockChain
import block
import transaction


useServerHost = True
socketURLs = [
    "localhost:8080",
    "localhost:8081",
    "localhost:8082",
    "localhost:8083",
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

# JMS - What are the ranges of possible values for difficulty and miningReward?
difficulty = 5
miningReward = 1.0


class mainLoop:
    def __init__(self):
        self.sock = sockets.socketManager(
            myNodeId, self.__onConnected, self.__onMessage, self.__onClosed
        )
        self.sock.startFullyConnected(socketURLs, useServerHost)
        self.bc = asyncBlockChain.asyncBlockChain(
            difficulty, miningReward, minerAccount, self.__onBlockedMined)
        self.__loadFromFile()
        self.bc.startMining()
        self.__requestMoreInfo()

    def __onConnected(self, nodeId: int):
        print("Connected to", nodeId)

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
        #except Exception as e:
        #    print('Failed to load from log file: %s' % (e))
        # JMS - Do we want to print a msg or do we just want to pass?
        except FileNotFoundError:
            print('Failed to load from log file: %s' % (self.__getFileName()))


    def __requestMoreInfo(self):
        hashes = self.bc.listHashes()
        self.sock.sendToAll(json.dumps({
            "Type": "NeedMoreInfo",
            "NodeId": myNodeId,
            "Hashes": hashes
        }))

    def __onRemoteAddTransaction(self, data: {}):
        t = transaction.transaction()
        t.fromTuple(data)
        self.bc.addTransaction(t)

    def __onRemoteAddBlock(self, data: {}):
        b = block.block()
        b.fromTuple(data)
        result = self.bc.setBlocks([b])
        if result == blockChain.blocksAdded:
            # A block was added so stop mining the
            # current block and start the next one.
            self.bc.restartMining()
            self.__saveToFile()
        elif result == blockChain.needMoreBlockInfo:
            # The block we tried to add was for a possibly longer chain.
            self.__requestMoreInfo()
        # else ignoreAddBlock and do nothing.

    def __onRemoteNeedMoreInfo(self, hashes: [], nodeId: int):
        diff = self.bc.getDifferenceTuple(hashes)
        self.sock.sendTo(nodeId, json.dumps({
            "Type": "ReplyWithInfo",
            "Diff": diff
        }))

    def __onRemoteReplayWithInfo(self, dataList: {}):
        blocks = []
        for data in dataList:
            b = block.block()
            b.fromTuple(data)
            blocks.append(b)
        result = self.bc.setBlocks(blocks)
        if result == blockChain.blocksAdded:
            # The missing block(s) were added so stop mining the
            # current block and start the next one.
            self.bc.restartMining()
            self.__saveToFile()
        # else needMoreBlockInfo or ignoreAddBlock which
        # probably means the data is invalid so do nothing.

    def __onMessage(self, nodeId: int, message: str):
        data = json.loads(message)
        dataType = data["Type"]
        if dataType == "AddTransaction":
            self.__onRemoteAddTransaction(data["Transaction"])
        elif dataType == "AddBlock":
            self.__onRemoteAddBlock(data["Block"])
        elif dataType == "NeedMoreInfo":
            self.__onRemoteNeedMoreInfo(data["Hashes"], data["NodeId"])
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
        print(self.bc.getAllBalances())

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
    mainLoop().run()
