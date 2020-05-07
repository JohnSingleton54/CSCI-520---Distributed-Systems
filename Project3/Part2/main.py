#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

# JMS - 'python3 main.py 0' ...on my laptop
# JMS - In Sublime Text, to comment out (or uncomment) a block of Python code I can press 'Ctrl+/'.

# References:
# 1. https://blog.goodaudience.com/how-a-miner-adds-transactions-to-the-blockchain-in-seven-steps-856053271476

import threading
import sys
import json

import random

import sockets
import asyncBlockchain
import blockchain
import block
import transaction


useServerHost = False
socketURLs = [
    "35.155.81.205:8080",
    "54.244.147.5:8080",
    "52.24.179.93:8080",
    "54.212.10.209:8080",
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
        self.sock = sockets.SocketManager(myNodeId,
            self.__onConnected, self.__onMessage, self.__onClosed)
        self.sock.startFullyConnected(socketURLs, useServerHost)
        self.bc = asyncBlockchain.AsyncBlockchain(validatorAccount, validators,
            self.__onCandidateCreated, self.__onBlockAdded)
        self.__loadFromFile()
        self.bc.start()

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
            "Type":      "Candidate",
            "Candidate": candidate.toTuple()
        }))

    def __onCandidate(self, data, nodeId):
        candidate = block.Block()
        candidate.fromTuple(data)
        result = self.bc.validateCandidateBlock(candidate, True)
        if result == blockchain.needMoreBlockInfo:
            # The block we tried to add was for a possibly longer chain.
            self.__requestMoreInfo()
        elif result == blockchain.validCandidate:
            print("%s signed the block from %s" % (validatorAccount, candidate.creator))
            self.sock.sendTo(nodeId, json.dumps({
                "Type":         "AddSignature",
                "Validator":     validatorAccount,
                "CandidateHash": candidate.hash
            }))
        # else ignoreBlock so do nothing
    
    def __onAddSignature(self, validator, candidateHash):
        self.bc.addSignature(validator, candidateHash)

    def __onBlockAdded(self, block):
        self.sock.sendToAll(json.dumps({
            "Type": "AddBlock",
            "Block": block.toTuple()
        }))
        self.__saveToFile()

    def __onMessage(self, nodeId: int, message: str):
        try:
            data = json.loads(message)
        except Exception as e:
            print("Message: %s" % (str(message)))
            print("Error receiving message:", e)
            return
        
        try:
            dataType = data["Type"]
            if dataType == "AddTransaction":
                self.__onRemoteAddTransaction(data["Transaction"])
            elif dataType == "Candidate":
                self.__onCandidate(data["Candidate"], nodeId)
            elif dataType == "AddSignature":
                self.__onAddSignature(data["Validator"], data["CandidateHash"])
            elif dataType == "AddBlock":
                self.__onRemoteAddBlock(data["Block"])
            elif dataType == "NeedMoreInfo":
                self.__onRemoteNeedMoreInfo(data["Hashes"], nodeId)
            elif dataType == "ReplyWithInfo":
                self.__onRemoteReplayWithInfo(data["Diff"])
            else:
                print("Unknown message from %d:" % (nodeId), message)
        except Exception as e:
            print("Message: %s" % (str(message)))
            print("Error processing message:", e)
            return

    def __makeTransaction(self):
        try:
            fromAccount = str(input("From: "))
            toAccount = str(input("To: "))
            amount = float(input("Amount: "))
            self.__makeTxn(fromAccount, toAccount, amount)
        except Exception as e:
            print("Invalid transaction: %s" % (e))

    # RECALL: Python does NOT support method overloading.
    def __makeTxn(self, fromAccount, toAccount, amount):
        try:
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

    def __insertTenTxns(self):
        for i in range(10):
            l = validators.copy()
            fromAndTo = random.sample(l, 2)
            fromAcct = fromAndTo[0]
            #print("fromAcct: ", fromAcct)
            toAcct = fromAndTo[1]
            #print("toAcct: ", toAcct)
            amt = round(random.uniform(0.01, 1.01), 9)
            #print(amt)
            self.__makeTxn(fromAcct, toAcct, amt)

    def __showFullChain(self):
        print(self.bc)

    def __showLastBlock(self):
        print(self.bc.lastBlock())

    def __showBalances(self):
        balances = self.bc.getAllBalances()
        print("Balances:")
        for account in balances:
            print("  %s = %f" % (account, balances[account]))

    def __showNextCreator(self):
        print("Next Creator: ", self.bc.whoShouldCreateBlock())

    def run(self):
        while True:
            print("What would you like to do?")
            print("  1. Info")
            print("  2. Make Transaction")
            print("  3. Insert Ten Transactions")
            print("  4. Show Full Chain")
            print("  5. Show Last Block")
            print("  6. Show Balances")
            print("  7. Next Creator")
            print("  8. Exit")

            try:
                choice = int(input("Enter your choice: "))
            except:
                print("Invalid choice. Try again.")
                continue

            if choice   == 1:
                self.__printInfo()
            elif choice == 2:
                self.__makeTransaction()
            elif choice == 3:
                self.__insertTenTxns()
            elif choice == 4:
                self.__showFullChain()
            elif choice == 5:
                self.__showLastBlock()
            elif choice == 6:
                self.__showBalances()
            elif choice == 7:
                self.__showNextCreator()
            elif choice == 8:
                break
            else:
                print('Invalid choice "%s". Try again.' % (choice))

        print("Closing...")
        self.sock.close()
        self.bc.stop()


if __name__ == "__main__":
    MainLoop().run()
