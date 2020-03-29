#!/usr/bin/env python

# Grant Nelson and John M. Singleton
# CSCI 520 - Distributed Systems
# Project 2 (Consensus Project)
# due Apr 6, 2020 by 11:59 PM


import http.server
import socketserver
import threading
import json


clientDir = 'clientFiles/'
fileServerTimeout = 0.5  # in seconds


class fileServer:
  # This serves the files (html, javascript, css, png, ico, and json)
  # needed for the browser pages.


  def __init__(self, fileSharePort, playerColor, socketURL):
    self.__fileSharePort = fileSharePort
    self.__playerColor   = playerColor
    self.__socketURL     = socketURL
    self.__keepAlive     = True

    # Start thread for serving up client files
    threading.Thread(target=self.__run).start()


  def __run(self):
    parent = self
    class ClientRequestHandler(http.server.SimpleHTTPRequestHandler):
      # Closure callback for the TCP server to customize the files being served.

      def __getDefault(self):
        # Make the default URL run index.html
        self.path = clientDir+'index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

      def __getConfigFile(self):
        # Construct and serve a json config file. This file provides all the information
        # the client will need to configure itself and create a socket back to this server.
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        data = json.dumps({
          'PlayerColor': parent.__playerColor,
          'SocketURL':   parent.__socketURL,
        })
        self.wfile.write(bytes(data, "utf8"))

      def __getFiles(self):
        # For all other files, fetch and serve those files.
        # The files are in their own folder so that no one can ask there server to serve
        # any of the python files (not like it really matters here since we don't have any private in it).
        self.path = clientDir + self.path
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

      def do_GET(self):
        if self.path == '/':
          self.__getDefault()
        elif self.path == '/config.json':
          self.__getConfigFile()
        else:
          self.__getFiles()

    fileServer = socketserver.TCPServer(("", self.__fileSharePort), ClientRequestHandler)
    while self.__keepAlive:
      try:
        fileServer.timeout = fileServerTimeout
        fileServer.handle_request()
      except:
        continue


  def close(self):
    self.__keepAlive = False
