import sys
sys.path.append('../')
from ClientServer import Server

s = Server()
s.set_port('40000')
s.create()
no_messages = 10
while no_messages:
    message = s.recv()
    print('Received %s' % message)
    resp = 'Got your message %s' % message.decode('utf-8')
    b = resp.encode('utf-8')
    s.send(b)
    no_messages -= 1
