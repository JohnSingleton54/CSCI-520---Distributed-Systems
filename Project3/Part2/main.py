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


useServerHost = True
socketURLs = [
    "localhost:8080",
    "localhost:8081",
    "localhost:8082",
    "localhost:8083",
]
validators = [
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
validatorAccount = validators[myNodeId]
print("My validator account is %s" % (validatorAccount))


class MainLoop:
    def __init__(self):
        self.sock = sockets.SocketManager(myNodeId, self.__onConnected, self.__onMessage, self.__onClosed)
        self.sock.startFullyConnected(socketURLs, useServerHost)
        self.bc = asyncBlockchain.AsyncBlockchain(validatorAccount, self.__onCandidateCreated)
        self.__loadFromFile()
        self.bc.startCreation()

    def __onConnected(self, nodeId: int):
        print("Connected to", nodeId)
        # Check if the other connection is more up-to-date (has a longer chain)
        self.__requestMoreInfo(nodeId)

    def __onClosed(self, nodeId: int):
        print("Connection to", nodeId, "closed")

    def __printInfo(self):
        print("My node Id is %d" % (myNodeId))
        print("My validator account is %s" % (validatorAccount))

    def __getFileName(self):
        # Gets the name of the chain file for this node ID.
        return 'chain%d.json' % myNodeId

    def __saveToFile(self):
        #print("JMS1", "in method __saveToFile")
        # data = json.dumps(self.bc.toTuple())  
        # f = open(self.__getFileName(), 'w')
        # f.write(data)
        # f.close()
        pass # TODO: Undo. Comment back in

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
            "Type":   "NeedMoreInfo",
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
        result = self.bc.setBlocks([b])
        if result == blockchain.blocksAdded:
            # TODO: Stop voting and start count down to next block
            self.__saveToFile()
        elif result == blockchain.needMoreBlockInfo:
            # The block we tried to add was for a possibly longer chain.
            self.__requestMoreInfo()
        # else ignoreBlock and do nothing.

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
        result = self.bc.setBlocks(blocks)
        if result == blockchain.blocksAdded:
            self.__saveToFile()
        # else needMoreBlockInfo or ignoreBlock which
        # probably means the data is invalid so do nothing

    def __onCandidateCreated(self, candidate):
        self.sock.sendToAll(json.dumps({
            "Type":      "AddCandidate",
            "Candidate": candidate.toTuple()
        }))

    def __onAddCandidate(self, data):
        candidate = block.Block()
        candidate.fromTuple(data)
        result = self.bc.addCandidateBlock(candidate, True)
        if result == blockchain.needMoreBlockInfo:
            # The block we tried to add was for a possibly longer chain.
            self.__requestMoreInfo()
        # else blocksAdded or ignoreBlock so do nothing

    def __onMessage(self, nodeId: int, message: str):
        try:
            data = json.loads(message)
        except Exception as e:
            print("Error receiving message:", e)
            return
        dataType = data["Type"]
        if dataType == "AddTransaction":
            self.__onRemoteAddTransaction(data["Transaction"])
        elif dataType == "AddCandidate":
            self.__onAddCandidate(data["Candidate"])
        elif dataType == "AddBlock":
            self.__onRemoteAddBlock(data["Block"])
        elif dataType == "NeedMoreInfo":
            self.__onRemoteNeedMoreInfo(data["Hashes"], nodeId)
        elif dataType == "ReplyWithInfo":
            self.__onRemoteReplayWithInfo(data["Diff"])
        else:
            print("Unknown message from %d:" % (nodeId), message)

    def __makeTransaction(self):
        try:
            fromAccount = str(input("From: "))
            toAccount = str(input("To: "))
            amount = float(input("Amount: "))
            trans = self.bc.newTransaction(fromAccount, toAccount, amount)
            if trans:
                self.sock.sendToAll(json.dumps({
                    "Type":        "AddTransaction",
                    "Transaction": trans.toTuple()
                }))
            else:
                print("Invalid transaction")
        except Exception as e:
            print("Invalid transaction: %s" % (e))

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
        self.bc.stopCreation()


if __name__ == "__main__":
    MainLoop().run()
