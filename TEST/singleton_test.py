class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            print("Singleton.__new__(): Creating instance of %s" % str(cls))
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

class dictionary_test(Singleton):
    obj = dict()

    def __init__(self):
        print("dictionary_test.init(): %s" % str(self.obj))
        

class SingletonClass(Singleton):
    pass

class RegularClass():
    pass

class Pivot(Singleton):
    def __init__(self):
        self.go_long = True

class Scheduler(Singleton):
    def __init__(self):
        self.s = 20

class Position(Singleton):
    def set_direction(self, value):
        self.direction = value

    def get_direction(self):
        return self.direction

    def set_entry(self, value):
        self.entry = value

    def get_entry(self):
        return self.entry

    def set_sl(self, value):
        self.sl = value

    def get_sl(self):
        return self.sl

    def set_target(self, value):
        self.target = value

    def get_target(self):
        return self.target

def test_singleton():
    x = SingletonClass()
    y = SingletonClass()
    print(x == y)

    x = Pivot()
    print("go_long: {}".format(x.go_long))
    y = Scheduler()
    print(x == y)
    y = Pivot()
    print("go_long: {}".format(y.go_long))
    x.go_long = False
    print("go_long: {}".format(y.go_long))
    print(x == y)

    x = RegularClass()
    y = RegularClass()
    print(x == y)

    x = Position()
    x.set_entry(100)

    y = Position()
    print("Entry: {}".format(y.get_entry()))

    print("s = {}".format(Scheduler().s))
    print("s = {}".format(Scheduler().s))
    print("s = {}".format(Scheduler().s))
    print("s = {}".format(Scheduler().s))

def test_dict():
    dictionary_test().obj = {'a': 'A', 'b': 'B'}

    print(dictionary_test().obj)
    print(dictionary_test().obj)
    print(dictionary_test().obj)
    print(dictionary_test().obj)

test_dict()
