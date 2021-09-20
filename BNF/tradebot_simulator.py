import sys
import zmq
import time

sys.path.append('../topic_pub_sub')
from TopicPubSub import TopicPublisher
port=44444
publisher = TopicPublisher()
publisher.init(port)

f = open('tradebot.log', 'r')

for x in f:
    publisher.sock_send('quote', x)
    time.sleep(2)
