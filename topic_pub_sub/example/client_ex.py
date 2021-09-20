import sys
sys.path.append('../')
from ClientServer import Client

s = Client()
s.set_port('40000')
try: 
    s.create()
except Exception as e:
    print("create: {}".format(e))

no_messages = 10

while no_messages:
    try:
        b = 'Hi'.encode('utf-8')
    except Exception as e:
        print('encode: {}'.format(e))
        sys.exit(0)

    try:
        s.send(b)
    except Exception as e:
        print("send: {}".format(e))
        sys.exit(0)

    try:
        message = s.recv()
    except Exception as e:
        print("recv: {}".format(e))
        sys.exit(0)

    print('Received %s' % message.decode('utf-8'))
    no_messages -= 1

