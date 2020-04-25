#!/usr/bin/env python

# Simple multiple socket manager with
# message framing and node Id determination.
# by Grant Nelson

import threading
import socket
import time
import re


class socketConst:
    # Maximum size a chunk can grow without hitting a message delimiter.
    # If a chunk reaches this size the current growing message is dumped, meaning
    # if a delimiter is reached shortly after, it could create a bad message.
    maximumChunkSize = 4000

    # The byte size of the chunks to read from the socket at one time.
    receiveChunkSize = 256

    # The delimiter to use to indicate the end of a message.
    messageDelimiter = "#"

    # The escape character used to indicate the delimiter is part of the message.
    messageEscape = "/"

    # The double escape is used to replace escape characters in the messages.
    messageDoubleEscape = messageEscape + messageEscape

    # The escaped delimiter is used to replace delimiter characters in the messages.
    messageEscapedDelimiter = messageEscape + messageDelimiter

    # The regular expression used to pull out the node Id from a node Id
    # message. The node Id message is used to tell in-sockets which node Id
    # the in-socket is connected to.
    nodeIdRegex = "GJN>>>(\d+)<<<GJN"

    # The message to pack a node Id into as the first message to an in-socket
    # so that the in-socket knows which node it is connected to.
    nodeIdMessage = "GJN>>>%d<<<GJN"

    # Error number for "[WinError 10038] An operation was attempted on something that is not a socket"
    errorSocketNotConnected = 10038

    # Error number for "[WinError 10053] An established connection was aborted by the software in your host machine"
    errorConnectionClosedHost = 10053

    # Error number for "[WinError 10054] An existing connection was forcibly closed by the remote host"
    errorConnectionClosedRemote = 10054

    # Error number for "[WinError 10061] No connection could be made because the target machine actively refused it"
    errorNoConnectionMade = 10061

    # Backlog for socket host when listening for incoming connections.
    socketServerBacklog = 1

    # The amount of time, in seconds, to wait until attempting to bind the socket host
    # after the OS rejects the host being binded. This rejection usually is from the socket still in use.
    hostRebindDelay = 3.0

    # The amount of time, in seconds, to attempt to connect an outgoing socket to a socket host
    # before stopping for a short delay and trying again.
    connectTimeout = 3.0

    # The amount of time, in seconds, to wait between failing to connect and retrying to connect.
    reconnectDelay = 1.0


class messageDefragger:
    # This is a tool for piecing together parts of messages
    # which have been escaped and streamed across the socket.
    # Also provides the why to escape and frame the message.

    def __init__(self):
        # Creates a new message defragger.
        self.__escaped = False
        self.__data = bytearray()

    def decode(self, chunk: bytes) -> [str]:
        # Adds more content into the growing message(s).
        # If one or more message has been found they will be returned.
        # Only complete messages will be returned, partial messages will wait until complete.
        messages = []
        for c in chunk:
            if self.__escaped:
                self.__data.append(c)
                self.__escaped = False
            elif c == ord(socketConst.messageEscape):
                self.__escaped = True
            elif c == ord(socketConst.messageDelimiter):
                messages.append(self.__data.decode())
                self.__data.clear()
            else:
                self.__data.append(c)
        if len(self.__data) > socketConst.maximumChunkSize:
            self.__data.clear()
            self.__escaped = False
        return messages

    def encode(self, msg: str) -> bytes:
        # Escapes and frames the message so it can be decoded later.
        msg = msg.replace(socketConst.messageEscape, socketConst.messageDoubleEscape)
        msg = msg.replace(
            socketConst.messageDelimiter, socketConst.messageEscapedDelimiter
        )
        msg += socketConst.messageDelimiter
        return msg.encode()


class inSocket:
    # This is a handler for a socket from an incoming connection to the local host.

    def __init__(self, conn, onConnected, onMessages, onClosed):
        # Creates a new socket for the given connection, `conn`.
        self.__conn = conn
        self.__onConnected = onConnected
        self.__onMessages = onMessages
        self.__onClosed = onClosed
        self.__keepAlive = True
        self.__defrag = messageDefragger()
        self.__nodeId = -1

        thread = threading.Thread(target=self.__listen)
        thread.start()

    def __listen(self):
        # Asynchronously listen for messages on this socket.
        while self.__keepAlive:
            try:
                chunk = self.__conn.recv(socketConst.receiveChunkSize)
                if chunk:
                    self.__addMessageChunk(chunk)
            except socket.error as e:
                if e.errno == socketConst.errorConnectionClosedHost:
                    # Host closed so close the socket.
                    break
                elif e.errno == socketConst.errorConnectionClosedRemote:
                    # Out-socket closed so close this socket.
                    break
                else:
                    print("inSocket exception:", e)
                    break
            except Exception as e:
                print("inSocket exception:", e)
                break
        self.__onClosed(self)

    def __addMessageChunk(self, chunk: bytearray):
        # Deals with new chunk of a message being received.
        messages = self.__defrag.decode(chunk)
        messages = self.__checkNodeId(messages)
        if messages:
            self.__onMessages(self, messages)

    def __checkNodeId(self, messages: [str]) -> [str]:
        # Checks if the node Id is set and looks for the first message containing the nodeId.
        if self.__nodeId < 0:
            while len(messages) > 0:
                msg = messages[0]
                messages = messages[1:]
                match = re.search(socketConst.nodeIdRegex, msg)
                if match:
                    self.__nodeId = int(match.group(1))
                    self.__onConnected(self)
                    break
        return messages

    def nodeId(self):
        # Gets the node Id for this socket.
        # Will return negative until fully connected and
        # the node Id message has been received.
        return self.__nodeId

    def send(self, message: str):
        # Sends a message out of this channel.
        data = self.__defrag.encode(message)
        self.__conn.send(data)

    def close(self):
        # Closes this socket.
        self.__keepAlive = False
        self.__conn.close()


class inSocketHost:
    # This handles opening a host for all incoming sockets connections.

    def __init__(self, url: str, useHost: bool, onConnected, onMessages, onClosed):
        # Creates a new in-socket host with the given URL to host.
        self.__url = url
        self.__useHost = useHost
        self.__onConnected = onConnected
        self.__onMessages = onMessages
        self.__onClosed = onClosed
        self.__dataLock = threading.Lock()
        self.__keepAlive = True
        self.__pending = []
        self.__sockets = {}

        thread = threading.Thread(target=self.__run)
        thread.start()

    def __run(self):
        # Asynchronous method to listen for incoming connections.
        parts = self.__url.split(":")
        host = parts[0] if self.__useHost else ""
        port = int(parts[1])

        while self.__keepAlive:
            # Try to setup the socket host.
            try:
                self.__serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__serverSock.bind((host, port))
            except OSError as e:
                print("Failed to bind host:", e)
                time.sleep(socketConst.hostRebindDelay)
                continue

            # Listen for connections and accept any incoming sockets.
            self.__serverSock.listen(socketConst.socketServerBacklog)
            while self.__keepAlive:
                try:
                    conn, addr = self.__serverSock.accept()
                    self.__addConnection(conn, addr)
                except socket.error as e:
                    if e.errno == socketConst.errorSocketNotConnected:
                        # `accept` can't be called, socket closed, go back to binding
                        break
                    else:
                        print("inSocketHost exception:", e)
                        break

    def __addConnection(self, conn, addr):
        # Adds a new in-socket for the new connection.
        sock = inSocket(
            conn,
            self.__onInSocketConnected,
            self.__onInSocketMessages,
            self.__onInSocketClosed,
        )
        with self.__dataLock:
            self.__pending.append(sock)

    def __onInSocketConnected(self, sock):
        # Handles a socket being connected and receiving the node Id.
        nodeId = sock.nodeId()
        with self.__dataLock:
            if sock in self.__pending:
                self.__pending.remove(sock)
            #
            # TODO: If another connection to the same node Id exists, close it and take newer
            #
            self.__sockets[nodeId] = sock
        self.__onConnected(nodeId)

    def __onInSocketMessages(self, sock, messages: [str]):
        # Handles a socket receiving a message.
        self.__onMessages(sock.nodeId(), messages)

    def __onInSocketClosed(self, sock):
        # Handles a socket closing.
        nodeId = sock.nodeId()
        wasConnected = False
        with self.__dataLock:
            if nodeId in self.__sockets:
                del self.__sockets[nodeId]
                wasConnected = True
            else:
                self.__pending.remove(sock)
        if wasConnected:
            self.__onClosed(nodeId)

    def sendTo(self, nodeId: int, message: str) -> bool:
        # Sends a message to the given node Id. If no socket has connected for the node Id,
        # then this call has no effect. Returns true if socket by that node Id exists.
        sock = None
        with self.__dataLock:
            if nodeId in self.__sockets:
                sock = self.__sockets[nodeId]
        if sock:
            sock.send(message)
            return True
        return False

    def sendToAll(self, message: str) -> bool:
        # Sends the message to all the connected sockets.
        # Returns true if any socket sent a massage, false if no message was sent.
        socks = {}
        with self.__dataLock:
            socks = self.__sockets.copy()
        for sock in socks.values():
            sock.send(message)
        if socks:
            return True
        return False

    def close(self):
        # Closes all the in-sockets, both connected and pending.
        self.__keepAlive = False
        socks = {}
        pends = []
        with self.__dataLock:
            socks = self.__sockets.copy()
            pends = self.__pending.copy()
        for sock in socks.values():
            sock.close()
        for pend in pends:
            pend.close()
        self.__serverSock.close()


class outSocket:
    # This is an outgoing socket which continues to try to connect and stay connected to a host until closed.

    def __init__(
        self, nodeId: int, targetId: int, url: str, onConnected, onMessages, onClosed
    ):
        # Creates a new outgoing socket for this `nodeId` to connect with the
        # host `targetId` via the given `url` to the `targetId`.
        self.__nodeId = nodeId
        self.__targetId = targetId
        self.__onConnected = onConnected
        self.__onMessages = onMessages
        self.__onClosed = onClosed
        self.__dataLock = threading.Lock()
        self.__keepAlive = True
        self.__defrag = messageDefragger()
        self.__pending = None
        self.__sock = None

        parts = url.split(":")
        host = parts[0]
        port = int(parts[1])
        thread = threading.Thread(target=self.__run, args=(host, port))
        thread.start()

    def __run(self, host: str, port: str):
        # Asynchronously attempt to connect to the host until a connection is made or closed.
        # If a connection is made this will call `listen` so that if the connection is lost
        # then it will drop back to this method to continue trying to reconnect.
        while self.__keepAlive:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                with self.__dataLock:
                    self.__pending = sock

                sock.settimeout(socketConst.connectTimeout)
                sock.connect((host, port))
                sock.settimeout(None)

                self.__socketConnected(sock)
                self.__listen()
            except socket.timeout:
                # Socket failed to connect in specified timeout, check "keep alive" and try again.
                self.__closeConnection()
                continue
            except socket.error as e:
                if e.errno == socketConst.errorNoConnectionMade:
                    # No connection could be made yet or host was setup yet.
                    # Attempt to connect to host again.
                    pass
                elif e.errno == socketConst.errorConnectionClosedRemote:
                    # An existing connection was forcibly closed by the remote host.
                    # Start trying to reconnect.
                    pass
                elif e.errno == socketConst.errorConnectionClosedHost:
                    # This connection closed so close the out-socket.
                    pass
                elif e.errno == socketConst.errorSocketNotConnected:
                    # Trying to listen on a closed socket, try to reconnect.
                    pass
                else:
                    print("outSocket expection:", e)

                # Failed to connect or lost connection, wait a little bit then try again.
                self.__closeConnection()
                if self.__keepAlive:
                    time.sleep(socketConst.reconnectDelay)
                continue
        self.__closeConnection()

    def __listen(self):
        # Listens to the socket to receive messages.
        while self.__keepAlive:
            chunk = self.__sock.recv(socketConst.receiveChunkSize)
            if chunk:
                self.__addMessageChunk(chunk)

    def __socketConnected(self, sock):
        # The socket has been connected, prepare to start listening.
        # Sends the node Id message to the host to let it know who connected to it.
        with self.__dataLock:
            self.__pending = None
            self.__sock = sock
        self.sendTo(socketConst.nodeIdMessage % (self.__nodeId))
        self.__onConnected(self.__targetId)

    def __addMessageChunk(self, chunk: bytes):
        # Adds a new chunk of a message to the growing messages.
        # Sends any messages which have been creates.
        messages = self.__defrag.decode(chunk)
        self.__onMessages(self.__targetId, messages)

    def __closeConnection(self):
        # The connection has been or is closing, update the state of the connection.
        closed = False
        if self.__sock:
            closed = True
        self.__pending = None
        self.__sock = None
        if closed:
            self.__onClosed(self.__targetId)

    def sendTo(self, message: str) -> bool:
        # Sends a message to the connected socket.
        # If the socket is not connected then the message is not sent.
        if message:
            sock = None
            with self.__dataLock:
                if self.__sock:
                    sock = self.__sock
            if sock:
                data = self.__defrag.encode(message)
                sock.send(data)
                return True

    def close(self):
        # Closes this out-socket connection.
        self.__keepAlive = False
        if self.__pending:
            self.__pending.close()
        if self.__sock:
            self.__sock.close()


class socketManager:
    # A tool for setting up and maintaining several connections
    # for processes identified with an integer, the node Id.

    def __init__(self, nodeId: int, onConnected, onMessage, onClosed):
        # Creates a new socket manager for the process with the given `nodeId`.
        # The given callback methods maybe set to `None` to not have it callback.
        # The `onConnected` and `onClosed` is called when a connection has been made,
        # however an outgoing connection will automatically attempt to reconnect. The point
        # of those two callbacks is to indicate when a message can be sent or not.
        # The callback methods are called asynchronously and multiple maybe called
        # at the same time. If you need to synchronize then you must add a lock.
        self.__nodeId = nodeId
        self.__outSockets = []
        self.__onConnected = onConnected
        self.__onMessage = onMessage
        self.__onClosed = onClosed
        self.__inSocketHost = None

    def startFullyConnected(self, socketURLs: [str], useHost: bool = True):
        # Starts a fully connected group of nodes. The given `socketURLs` contains
        # the URLs for the node Id where the node Id is the index of the URL in the list.
        # This will start a socket host for this manager's node Id, the host will be contacted by all
        # higher value node Id processes. It will attempt to connect to all lower node Id processes.
        self.startSocketHost(socketURLs[self.__nodeId], useHost)
        for targetId in range(0, self.__nodeId):
            self.connectTo(targetId, socketURLs[targetId])

    def startSocketHost(self, url: str, useHost: bool = True):
        # Starts a socket host for this manager's node Id and the given URL. If a socket host
        # already has been started the older socket host will be closed.
        if self.__inSocketHost:
            self.__inSocketHost.close()
        self.__inSocketHost = inSocketHost(
            url,
            useHost,
            self.__onInnerConnected,
            self.__onInnerMessages,
            self.__onInnerClosed,
        )

    def connectTo(self, targetId: int, url: str):
        # Connects this manager to another node which has a socket hosted.
        # If the other node hasn't started the host yet, this will continue to attempt to connect
        # until it has been connected or the manager is closed.
        outSock = outSocket(
            self.__nodeId,
            targetId,
            url,
            self.__onInnerConnected,
            self.__onInnerMessages,
            self.__onInnerClosed,
        )
        self.__outSockets.append(outSock)

    def __onInnerConnected(self, nodeId: int):
        # Handles a socket being connected.
        if self.__onConnected:
            self.__onConnected(nodeId)

    def __onInnerMessages(self, nodeId: int, messages: [str]):
        # Handles a socket receiving zero or more message.
        if self.__onMessage:
            for message in messages:
                self.__onMessage(nodeId, message)

    def __onInnerClosed(self, nodeId: int):
        # Handles a socket being closed.
        if self.__onClosed:
            self.__onClosed(nodeId)

    def sendToAll(self, message: str) -> bool:
        # Sends a message to all sockets which have been connected.
        # Returns true if one or more messages were sent, false if no message was sent out.
        anySent = False
        if self.__inSocketHost.sendToAll(message):
            anySent = True
        for sock in self.__outSockets:
            if sock.sendTo(message):
                anySent = True
        return anySent

    def sendTo(self, nodeId: int, message: str) -> bool:
        # Sends a message to the process with the given node Id.
        # Returns true if the message was sent and false if that node Id is not connected.
        if nodeId == self.__nodeId:
            return False
        elif nodeId < self.__nodeId:
            if nodeId in self.__outSockets:
                return self.__outSockets[nodeId].sendTo(message)
            return False
        else:
            return self.__inSocketHost.sendTo(nodeId, message)

    def close(self):
        # Closes and cleanup all the sockets being used by this manager.
        if self.__inSocketHost:
            self.__inSocketHost.close()
        for sock in self.__outSockets:
            sock.close()
