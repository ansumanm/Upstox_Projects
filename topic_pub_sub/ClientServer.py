import zmq
import sys

class Server:
    def __init__(self):
        self.port = "5556"

    def __del__(self):
        pass

    def set_port(self, port):
        self.port = port

    def create(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:%s" % self.port)

    def recv(self):
        try:
            message = self.socket.recv()
        except Exception as e:
            print("Server[recv error] {}".format(e))
            return None
        return message

    def send(self, data):
        try:
            self.socket.send(data)
        except Exception as e:
            print("Server[send error] {}".format(e))

    def recv_string(self):
        try:
            message = self.socket.recv_string()
        except Exception as e:
            print("Server[recv error] {}".format(e))
            return None
        return message

    def send_string(self, data):
        try:
            self.socket.send_string(data)
        except Exception as e:
            print("Server[send error] {}".format(e))


class Client:
    def __init__(self):
        self.port = "5556"

    def __del__(self):
        pass

    def set_port(self, port):
        self.port = port

    def create(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

    def recv(self):
        try:
            message = self.socket.recv()
        except Exception as e:
            print("Client[recv error] {}".format(e))
            return None
        return message

    def recv_string(self):
        try:
            message = self.socket.recv_string()
        except Exception as e:
            print("Client[recv error] {}".format(e))
            return None
        return message

    def send(self, data):
        try:
            self.socket.connect("tcp://localhost:%s" % self.port)
        except Exception as e:
            print("Client[connect error] {}".format(e))
            sys.exit(0)

        try:
            self.socket.send(data)
        except Exception as e:
            print("Client[send error] {}".format(e))
            sys.exit(0)

    def send_string(self, data):
        try:
            self.socket.connect("tcp://localhost:%s" % self.port)
        except Exception as e:
            print("Client[connect error] {}".format(e))
            sys.exit(0)

        try:
            self.socket.send_string(data)
        except Exception as e:
            print("Client[send error] {}".format(e))
            sys.exit(0)

