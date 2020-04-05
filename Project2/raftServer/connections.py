#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)
# due Apr 6, 2020 by 11:59 PM

# This file contains the code for listening and sending on a channel.

import threading
import time
import socket
import sys
import json
import select

# helpful links:
# - https://www.tutorialspoint.com/python/python_multithreading.htm
# - https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
# - https://pypi.org/project/multitasking/
# - https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
# - https://www.geeksforgeeks.org/start-and-stop-a-thread-in-python/


class listener:
  # This is a class to listen for incoming messages sent to the given host and port.
  # This will callback to the given method, `handleMethod`, for handling messages.

  def __init__(self, handleMethod, hostAndPort, useMyHost):
    # Creates a new listener to the given host and port.
    self.__handleMethod = handleMethod
    self.__timeToDie = False

    parts = hostAndPort.split(':')
    host = parts[0] if useMyHost else ""
    port = int(parts[1])

    thread = threading.Thread(target=self.__run, args=(host, port))
    thread.start()


  def __run(self, host, port):
    # This method runs in a separete thread to listen for new connections.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(1)

    while not self.__timeToDie:
      try:
        sock.settimeout(1)
        conn, addr = sock.accept()

        thread = threading.Thread(target=self.__connection, args=(conn, addr))
        thread.start()
      except socket.timeout:
        continue
    sock.close()


  def __connection(self, conn, addr):
    # This method handles a connection from a talker and listens to it.
    conn.settimeout(1)
    while not self.__timeToDie:
      try:
        data = conn.recv(4096)
        if data:
          # Got a message send it to the handle method.
          parts = data.decode().split('#')
          for part in parts:
            if part:
              msg = ''
              try:
                msg = json.loads(part)
              except Exception as e:
                print('Error parsing JSON(%s): %s' % (part, e))
              if msg:
                try:
                  self.__handleMethod(msg, conn)
                except Exception as e:
                  print('Exception in handler of (%s): %s' % (part, e))
      except socket.timeout: 
        continue
    conn.close()


  def close(self):
    # This starts shutting down the listener.
    self.__timeToDie = True


class sender:
  # This is a class to send messages out the given host and port.
  # This will have a queue of messages which are sent when they can be.

  def __init__(self, hostAndPort):
    # Creates a new sender to the given host and port.
    self.__connected = False
    self.__timeToDie = False
    self.__queueLock = threading.Lock()
    self.__pendingQueue = []

    parts = hostAndPort.split(':')
    host = parts[0]
    port = int(parts[1])

    thread = threading.Thread(target=self.__run, args=(host, port))
    thread.start()
  

  def __run(self, host, port):
    # This method runs in a separete thread to talk to the socket.
    # Any messages in the queue will be sent out the socket.
    while not self.__timeToDie:
      try:
        # Prepare to try to connect/reconnect
        self.__connected = False
        with self.__queueLock:
          self.__pendingQueue = []

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, port))
        self.__connected = True

        while not self.__timeToDie:
          # Check if there are any pending messages and send all of them.
          with self.__queueLock:
            for data in self.__pendingQueue:
              sock.sendall(data.encode())
            self.__pendingQueue = []

          # Sleep for a bit to let new messages get pended.
          time.sleep(0.01)

        # Close socket and exit thread
        sock.close()
        return

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
        data = json.dumps(message)+'#'
        self.__pendingQueue.append(data)


  def close(self):
    # This starts shutting down the sender.
    self.__timeToDie = True
