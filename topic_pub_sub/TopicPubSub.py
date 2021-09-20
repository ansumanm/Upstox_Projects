import zmq
import sys
import json

class TopicPublisher:
    def __init__(self):
        self.context = 0
        self.socket = 0
        self.topic = ""

    def __del__(self):
        """
        Destructor
        """
        print("TopicPublisher: Destructor")
        self.context.destroy(linger=None)

    def init(self, port):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:%s" % (port))

    def sock_send(self, topic, json_input):
        self.topic = topic
        try: 
            msg = "{} {}".format(topic, json_input)
            self.socket.send_string(msg)
        except Exception as e:
            print('sock_send(): Exception')
            print(e)


class TopicSubscriber:
    def __init__(self):
        self.context = 0
        self.socket = 0
        self.topic = ""

    def __del__(self):
        """
        Destructor
        """
        print("TopicSubscriber: Destructor")
        self.context.destroy(linger=None)

    def init(self, topic, port):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect("tcp://localhost:%s" % port)
        self.topic = topic
        self.socket.setsockopt_string(zmq.SUBSCRIBE, self.topic)

    def sock_receive(self):
        try: 
            msg = self.socket.recv_string()
            # Need to remote topic from string before returning it.
            data = msg.split(' ', 1)[1]
            return data
        except Exception as e:
            print('sock_receive Exception:')
            print(e)
            return [{}]

