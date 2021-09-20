#!/usr/bin/env python3
import threading
import time
from cmd2 import Cmd

class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            print("Singleton.__new__(): Creating instance of %s" % str(cls))
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

# orders = {}
# Instead of making it a global variable, lets make it a global object
class OrdersDB(Singleton):
    obj = None
    _lock = None

    def __init__(self):

        if self.obj is None:
            self.obj = dict()

        if self._lock is None:
            self._lock = threading.Lock()

    def __del__(self):
        pass

    def __enter__(self):
        print("OrdersDB.__enter__()")
        self._lock.acquire()
        return self

    def __exit__(self, type, value, traceback):
        print("OrdersDB.__exit__()")
        self._lock.release()


class Order():
    def __init__(self, name):
        self.name = name

def thread1():

    OrdersDB().obj['key_1'] = Order('value_1')
    OrdersDB().obj['key_2'] = Order('value_2')
    OrdersDB().obj['key_3'] = Order('value_3')
    OrdersDB().obj['key_4'] = Order('value_4')

    print("Thread1: Sleeping for 20 seconds...")
    time.sleep(20)



class CLI(Cmd):

    @staticmethod
    def print_keyval(key):
        val = OrdersDB().obj[key]
        print(val)

    def do_print_keyval(self, line):
        for key, value in OrdersDB().obj.items():
            self.print_keyval(key)

    def do_dump(self, line):
        try:
            print(OrdersDB().obj)
        except Exception as e:
            print("Exception: %s" % str(e))

def main():
    t = threading.Thread(target=thread1)
    t.start()

    CLI().cmdloop()

    t.join()

main()
