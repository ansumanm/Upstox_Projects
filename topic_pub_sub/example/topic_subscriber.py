import threading, queue
import zmq                                                                       
import json
import sys
sys.path.append('../')  

from TopicPubSub import TopicSubscriber

q = queue.Queue()

def Thread1():
    sub = TopicSubscriber()
    sub.init("1000", 8888)
    print("Collecting updates for 1000")
    while True:
        msg = sub.sock_receive()
        print("Thread1 putting in queue: ")
        print(msg)
        # q.put(json.dumps(msg))


def Thread2():
    sub = TopicSubscriber()
    print("Collecting updates...")
    sub.init("1002", 8888)
    while True:
        msg = sub.sock_receive()
        print("Thread2 putting in queue ")
        q.put(json.dumps(msg))


def Thread4():
    sub = TopicSubscriber()
    print("Collecting updates...")
    sub.init("", 8888)
    while True:
        msg = sub.sock_receive()
        print("Thread4 putting in queue ")
        q.put(json.dumps(msg))


def Thread3():
    #for update_nbr in range(9):
    while True:
        string = json.loads(q.get())
        print((string))
        print(type(string))


Thread1 = threading.Thread(target=Thread1)
"""
Thread2 = threading.Thread(target=Thread2)
Thread3 = threading.Thread(target=Thread3)
Thread4 = threading.Thread(target=Thread4)
"""

Thread1.start()
"""
Thread2.start()
Thread3.start()
Thread4.start()
"""


