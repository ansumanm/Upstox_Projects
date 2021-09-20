import zmq                                                                       
import random                                                                    
import sys                                                                       
import time                                                                      
import pandas as pd
import json
sys.path.append('../')
from TopicPubSub import TopicPublisher
port = 8888

publisher = TopicPublisher()
publisher.init(port)


df = pd.DataFrame([['a', 'b'], ['c', 'd']],
                    index=['row 1', 'row 2'],
                    columns=['col 1', 'col 2'])

while True:                                                                      
    try:                                                                         
        topic = random.randrange(999, 1005)
        print("putting topic %s" % topic)
        jj = df.to_json(orient='records')
        publisher.sock_send(str(topic), jj)
        time.sleep(1)                                                            
    except Exception as e:                                                       
        print(e)                                                                 
        sys.exit(0)  
