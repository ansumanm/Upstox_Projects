#!/usr/bin/env python3

import zmq
import sys
import logging

class ordermanager_client():
    def __init__(self):
        logging.basicConfig(filename="logs/ordermanager_api.log", level=logging.DEBUG)
        self.server_port = "5001"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ) 

    def request(self, data):
        try:
            self.socket.connect("tcp://localhost:%s" % self.server_port)
        except Exception as e:
            print("Request failed(1): %s" % str(e))
            return None

        try:
            self.socket.send_string(data)
        except Exception as e:
            print("Request failed(2): %s" % str(e))
            return None

        try:
            reply = self.socket.recv_string()
        except Exception as e:
            print("Request failed(3): %s" % str(e))
            return None

        # Job done. Close the socket.
        try:
            self.socket.close()
        except Exception as e:
            print("Socket Close failed: %s" % str(e))

        return reply

    def place_order(self, data):
        reply = self.request(data)

        return reply

    def modify_order(self, data):
        reply = self.request(data)

        return reply

    def cancel_order(self, data):
        reply = self.request(data)

        return reply





