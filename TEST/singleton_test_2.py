import sched
import time

class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        print("ENTER: new ...")
        if not cls._instance:
            print("Creating new object...")
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

class A(Singleton):
    s = sched.scheduler(time.time, time.sleep)
    def __init__(self):
        print("Init ...")

a = A()
b = A()

print(a.s, b.s)
