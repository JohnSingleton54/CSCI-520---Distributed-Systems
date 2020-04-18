#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 3 (Blockchain Programming Project)
# due May 7, 2020 by 11:59 PM

import threading
import sys

import sockets
import blockChain


useServerHost = True
socketURLs = [
    "localhost:8080",
    "localhost:8081",
    "localhost:8082",
    "localhost:8083",
]

myNodeId = int(sys.argv[1])
print("My node Id is %d" % (myNodeId))

difficulty = 3
miningReward = 1.0


class mainLoop:
    def __init__(self):
        self.__socks = sockets.socketManager(
            myNodeId, self.__onConnected, self.__onMessage, self.__onClosed
        )
        self.__socks.startFullyConnected(socketURLs, useServerHost)
        self.__blockChain = blockChain.blockChain(difficulty, miningReward)

    def __onConnected(self, nodeId: int):
        print("Connected to", nodeId)

    def __onClosed(self, nodeId: int):
        print("Connection to", nodeId, "closed")

    def __onMessage(self, nodeId: int, message: str):
        # TODO: Implement
        print("Message from %d:" % (nodeId), message)

    def __makeTransaction(self):
        # TODO: Implement
        pass

    def __showFullChain(self):
        print(self.__blockChain)

    def __showLastBlock(self):
        print(self.__blockChain.lastBlock())

    def __showBalances(self):
        print(self.__blockChain.getAllBalances())

    def run(self):
        while True:
            print("What would you like to do?")
            print("  1. Make Transaction")
            print("  2. Show Full Chain")
            print("  3. Show Last Block")
            print("  4. Show Balances")
            print("  5. Exit")

            try:
                choice = int(input("Enter your choice: "))
            except:
                print("Invalid choice. Try again.")
                continue

            if choice == 1:
                self.__makeTransaction()
            elif choice == 2:
                self.__showFullChain()
            elif choice == 3:
                self.__showLastBlock()
            elif choice == 4:
                self.__showBalances()
            elif choice == 5:
                break
            else:
                print('Invalid choice "%s". Try again.' % (choice))

        print("Closing...")
        self.__socks.close()


if __name__ == "__main__":
    mainLoop().run()
