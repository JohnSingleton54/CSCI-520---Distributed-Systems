#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)
# Duplicated from Project 1 (Replicated Log Project)
# due Apr 6, 2020 by 11:59 PM

# This file contains the code for listening and sending on a channel.

import threading
import time
import socket
import sys
import select

# helpful links:
# - https://www.tutorialspoint.com/python/python_multithreading.htm
# - https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
# - https://pypi.org/project/multitasking/
# - https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
# - https://www.geeksforgeeks.org/start-and-stop-a-thread-in-python/


connectionTimeout = 0.5  # in seconds
maximumMessageSize = 4096


class connection:
  # This is a class to send out and receive messages from the given host and port.
  # This will have a queue of messages which are sent when they can be.


  def __init__(self, handleMethod, hostAndPort):
    # Creates a new sender/receiver which connects to the given host and port.
    self.__handleMethod = handleMethod
    self.__connected = False
    self.__keepAlive = True
    self.__queueLock = threading.Lock()
    self.__pendingQueue = []

    parts = hostAndPort.split(':')
    host = parts[0]
    port = int(parts[1])

    thread = threading.Thread(target=self.__run, args=(host, port))
    thread.start()
  

  def __run(self, host, port):
    # This method runs in a separete thread to talk to the socket.
    # Any messages in the queue will be sent out the socket periodically
    # between reads from the socket.
    while self.__keepAlive:
      try:
        # Prepare to try to connect/reconnect
        self.__connected = False
        with self.__queueLock:
          if self.__pendingQueue:
            self.__pendingQueue.clear()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, port))

        try:
          # Connection made start reading and sending to the socket.
          self.__connected = True
          sock.settimeout(connectionTimeout)
          while self.__keepAlive:
            try:
              # Check if there are any pending messages and send all of them.
              with self.__queueLock:
                while self.__pendingQueue:
                  message = self.__pendingQueue.pop(0)
                  sock.sendall(message.encode())

              # Read the socket for any incoming messages.
              data = sock.recv(maximumMessageSize)
              if data:
                # Got a message send it to the handle method.
                self.__handleMethod(data.decode())
            except socket.timeout:
              continue

        except Exception as e:
          # Error occurred in the socket
          print(e)
        finally:
          # Close socket and try to reconnect 
          sock.close()

      except socket.timeout:
        time.sleep(1)
      except socket.error:
        # Failed to connect or lost connection, wait a little bit then try again.
        time.sleep(3)


  def send(self, message):
    # Adds the message to the pending messages to be send out the socket.
    # If this is not connected, the message will be ignored.
    if self.__connected:
      with self.__queueLock:
        self.__pendingQueue.append(message)


  def close(self):
    # This starts shutting down the sender.
    self.__keepAlive = False
