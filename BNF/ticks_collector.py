import sys
import argparse
from upstox_api.api import *
# from datetime import datetime
import time
import logging
# from logging.config import fileConfig
import pickle
from influxdb import InfluxDBClient

"""
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context
"""
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

u = None
s = None

upstox_settings = dict()
client = InfluxDBClient(host='localhost', port=8086)

sys.path.append('../topic_pub_sub')
from TopicPubSub import TopicPublisher
port=5000
publisher = TopicPublisher()
publisher.init(port)

def dump_to_file(obj,filename):
    try:
        with open(filename, 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print('dump_to_file: {}'.format(e))

def load_from_file(filename):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print('load_from_file: {}'.format(e))

def my_on_order_update_handler (event):
    try:
        data = eval(str(event))
    except Exception as e:
        print("Error: {}".format(str(e)))
        return

    print(event)
    print(type(event))

    try:
        publisher.sock_send('Order', str(event))
    except Exception as e:
        print("sock_send error: %s" % str(e))

    """ {'quantity': 40, 'exchange_order_id': '', 'order_type': 'SL',
    'status': 'put order req received', 'transaction_type': 'S', 'exchange':
    'NSE_FO', 'trigger_price': 19075.45, 'symbol': 'BANKNIFTY20APRFUT',
    'traded_quantity': 0, 'is_amo': False, 'product': 'OCO',
    'order_request_id': '1', 'duration': None, 'price': 1907 5.45,
    'time_in_micro': '1585553760835062', 'parent_order_id': 'NA', 'order_id':
    '200330000593469', 'message': '', 'exchange_time': '',
    'disclosed_quantity': 0 , 'token': 56058, 'average_price': 0.0,
    'instrument': Instrument(exchange='NSE_FO', token=56058,
            parent_token=26009, symbol='banknifty20aprfut', name='', clos
            ing_price=19778.65, expiry='1588185000000', strike_price=None,
            tick_size=5.0, lot_size=20, instrument_type='FUTIDX', isin=None)}
    try:
        point = {
                "measurement": "Orders",
                "tags": {
                    'order_type': data['order_type'],
                    'transaction_type': data['transaction_type'],
                    'exchange': data['exchange'],
                    'symbol': data['symbol'],
                    'product': data['product']
                    },
                "time": data['time_in_micro'],
                "fields": {
                    'quantity': data['quantity'],
                    'exchange_order_id': data['exchange_order_id'],
                    'status': data['status'],
                    'trigger_price': data['trigger_price'],
                    'traded_quantity': data['traded_quantity'],
                    'order_request_id': data['order_request_id'],
                    'price': data['price'],
                    'parent_order_id': data['parent_order_id'],
                    'order_id': data['order_id'],
                    'message': data['message'],
                    'exchange_time': data['exchange_time'],
                    'disclosed_quantity': data['disclosed_quantity'],
                    'average_price': data['average_price']
                    }
                }
    except Exception as e:
        print("my_on_order_update_handler(): ", str(e))

    print(point)
    try:
        client.write_points([point], time_precision='ms',  database='transactions')
    except Exception as e:
        print("write_points error:[{}] {}".format(e.__class__.__name__, str(e)))
        client.create_database('transactions')
    """

def my_on_trade_update_handler (event):
    print("******** Trade Update START ******** ")
    print("%s" % str(event))
    print("******** Trade Update END ******** ")
    # telegram_handler(event, "on_trade_update")

def my_on_quote_update_handler (event):
    """
    {'timestamp': '1588755121000', 'exchange': 'NSE_FO', 'symbol': 'BANKNIFTY20MAYFUT', 'ltp': 19500.0, 'close': 19246.35, 'open': 19219.2, 'high': 19819.0, 'low': 18900.0, 'vtt': 6867920.0, 'atp': 19470.32, 'oi': 1614860.0, 'spot_price': 19540.75, 'total_buy_qty': 183200, 'total_sell_qty': 131420, 'lower_circuit': 17321.75, 'upper_circuit': 21171.0, 'yearly_low': None, 'ltt': 1588755121000, 'bids': [{'quantity': 2220, 'price': 19500.0, 'orders': 7}, {'quantity': 20, 'price': 19499.95, 'orders': 1}, {'quantity': 20, 'price': 19499.7, 'orders': 1}, {'quantity': 40, 'price': 19498.9, 'orders': 2}, {'quantity': 80, 'price': 19498.35, 'orders': 1}], 'asks': [{'quantity': 40, 'price': 19500.05, 'orders': 2}, {'quantity': 20, 'price': 19502.85, 'orders': 1}, {'quantity': 20, 'price': 19503.15, 'orders': 1}, {'quantity': 20, 'price': 19503.2, 'orders': 1}, {'quantity': 20, 'price': 19503.35, 'orders': 1}], 'instrument': Instrument(exchange='NSE_FO', token=52461, parent_token=26009, symbol='banknifty20mayfut', name='', closing_price=19246.35, expiry='1590604200000', strike_price=None, tick_size=5.0, lot_size=20, instrument_type='FUTIDX', isin=None)}
    """
    logging.info("%s" % str(event))

    try:
        data = eval(str(event))
    except Exception as e:
        print("Error: {}".format(str(e)))
        return

    # "time": datetime.fromtimestamp(data['ltt']/1000).isoformat('T'),
    try:
        point = {
                "measurement": "FeedFull",
                "tags" : {
                    'exchange': data['instrument'].exchange,
                    'symbol': data['instrument'].symbol,
                    'token': data['instrument'].token,
                    'parent_token': data['instrument'].parent_token,
                    'name': data['instrument'].name,
                    'expiry': data['instrument'].expiry,
                    'strike_price': data['instrument'].strike_price,
                    'tick_size': data['instrument'].tick_size,
                    'lot_size': data['instrument'].lot_size,
                    'instrument_type': data['instrument'].instrument_type,
                    'isin': data['instrument'].isin,
                    },
                "time": data['ltt'],
                "fields": {
                    "ltp": data['ltp'],
                    "close": data['close'],
                    "open": data['open'],
                    "high": data['high'],
                    "low": data['low'],
                    "vtt": data['vtt'],
                    "atp": data['atp'],
                    "oi": data['oi'],
                    "spot_price": data['spot_price'],
                    "total_buy_qty": data['total_buy_qty'],
                    "total_sell_qty": data['total_sell_qty'],
                    }
                }
    except Exception as e:
        print("Point error: {}".format(str(e)))

    # print(point)
    try:
        client.write_points([point], time_precision='ms',  database='ticks')
    except Exception as e:
        print("write_points error:[{}] {}".format(e.__class__.__name__, str(e)))
        client.create_database('ticks')
    
def my_generic_event_handler (event):
    print ("%s" % str(event))

def my_on_disconnect_handler (event):
    print ("Disconnect Handler: %s" % str(event))

def my_on_error_handler (ws, event):
    print("Error: {}".format(event))


# Filter example.
def main():
    # parser = argparse.ArgumentParser("Instrument subscribe")
    # parser.add_argument('-s', '--str',help='instrument to subscribe')
    # args = vars(parser.parse_args())
    # inst_str = args['str']
    logging.basicConfig(filename="tradebot_ws.log", level=logging.INFO)
    # fileConfig('logging_config.ini')
    global publisher

    u = load_from_file('upstox.pickle')
    # u.get_master_contract('MCX_FO') # get contracts for MCX FO
    u.get_master_contract('NSE_EQ')
    u.get_master_contract('BSE_EQ')
    u.get_master_contract('NSE_FO')

    # u.set_on_order_update (my_generic_event_handler)
    u.set_on_order_update (my_on_order_update_handler)
    u.set_on_quote_update (my_on_quote_update_handler)
    u.set_on_trade_update (my_on_trade_update_handler)
    u.set_on_error (my_on_error_handler)

    """
    try:
        u.subscribe(u.get_instrument_by_symbol('MCX_FO', inst_str), LiveFeedType.Full)
    except Exception as e:
        print("Could not subscribe: {}".format(e))
    """
    retries = 10

    while(retries > 0):
        print("""
                Starting websocket... %d
                """ % retries )
        u.start_websocket(False)
        retries = retries - 1

if __name__ == '__main__':
    main()
