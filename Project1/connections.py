#!/usr/bin/env python2.7

import threading
import time
import socket
import sys
import select

# helpful links:
# https://www.tutorialspoint.com/python/python_multithreading.htm
# https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
# https://pypi.org/project/multitasking/
# https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method


class listener:
  # This is a class to listen for incoming messages from the given host and port.
  # This will callback to the given method for handling messages.

  def __init__(self, handleMethod, hostAndPort, useMyHost):
    # Creates a new listener to the given host and port.
    self.handleMethod = handleMethod
    parts = hostAndPort.split(':')
    self.host = parts[0] if useMyHost else ""
    self.port = int(parts[1])
    self.timeToDie = False
    self.thread = threading.Thread(target=self.__run)
    self.thread.start()

  def __run(self):
    while not self.timeToDie:
      try:
        # This method run in a separete thread to listen to the socket.
        # Any message which comes in is passed to handleMethod.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.settimeout(3)
        s.listen()
        conn, addr = s.accept()
        while not self.timeToDie:
          # Use select to timeout after 1 seconds to check if it is time to die.
          ready = select.select([conn], [], [], 1)
          if ready[0]:
            data = conn.recv(4096)
            if data:
              # Got a message send it to the handle method.
              self.handleMethod(data.decode())
        # Close connection, close socket, and exit thread
        conn.close()
        s.close()
        return
      except Exception as e:
        # Failed to connect, wait a little bit until the listener is there.
        time.sleep(1)

  def close(self):
    # Close will stop the listener.
    # This call will not return until the thread has exited.
    self.timeToDie = True
    self.thread.join()


class talker:
  # This is a class to talker to send messages to the given host and port.
  # This will have a queue of messages which are sent when they can be.

  def __init__(self, hostAndPort):
    # Creates a new talker to the given host and port.
    # The given handleLock is used to synchronize calls to handleMethod.
    parts = hostAndPort.split(':')
    self.host = parts[0]
    self.port = int(parts[1])
    self.timeToDie = False
    self.queueLock = threading.Lock()
    self.pendingQueue = []
    self.thread = threading.Thread(target=self.__run)
    self.thread.start()
  
  def __run(self):
    # This method run in a separete thread to talk to the socket.
    # Any messages in the queue will be sent out the socket.
    connected = False
    while (not connected) and (not self.timeToDie):
      try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        connected = True
        while not self.timeToDie:
          # Check if there are any pending messages and send all of them.
          self.queueLock.acquire()
          while self.pendingQueue:
            message = self.pendingQueue.pop(0)
            s.sendall(message.encode())
          self.queueLock.release()
          # Sleep for a bit to let new messages get pended.
          time.sleep(1)
        # Close socket and exit thread
        s.close()
        return
      except Exception as e:
        # Failed to connect, wait a little bit until the listener is there.
        time.sleep(1)

  def send(self, message):
    # Adds the message to the pending messages to be send to the socket.
    self.queueLock.acquire()
    self.pendingQueue.append(message)
    self.queueLock.release()

  def close(self):
    # Close will stop the talker.
    # This call will not return until the thread has exited.
    self.timeToDie = True
    self.thread.join()
