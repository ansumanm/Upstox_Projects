import copy
from upstox_api.api import *
from datetime import datetime
from pprint import pprint
import os, sys
import time
from tempfile import gettempdir
import logging
import pickle
import subprocess
sys.path.append('../infra/')
from infra import Infra as I

u = None
s = None

upstox_settings = dict()

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
    msg = """
    symbol: {}
    quantity: {}
    transaction_type: {}
    order_type: {}
    price: {}
    trigger_price: {}
    exchange: {}
    status: {}
    message: {}
    """.format(event['symbol'], event['quantity'], \
            event['transaction_type'], event['order_type'], \
            event['price'], event['trigger_price'], \
            event['exchange'], event['status'], event['message'])

    logging.critical(msg)
    # telegram_handler(event, "on_order_update")

def my_on_trade_update_handler (event):
    msg = """
    symbol: {}
    traded_quantity: {}
    transaction_type: {}
    order_type: {}
    traded_price: {}
    exchange: {}
    """.format(event['symbol'], event['traded_quantity'], \
            event['transaction_type'], event['order_type'], \
            event['traded_price'], \
            event['exchange'])

    logging.critical(msg)
    # telegram_handler(event, "on_trade_update")

def my_on_quote_update_handler (message):
    print("Quote Update: %s" % str(message))

def my_on_disconnect_handler (event):
    pass

def my_on_error_handler (ws, event):
    print("Error: {}".format(event))

def my_generic_event_handler (event):
    print ("Event: %s" % str(event))

# Filter example.
def main():
    parser = argparse.ArgumentParser("Instrument subscribe")
    parser.add_argument('-s', '--str',help='instrument to subscribe')

    args = vars(parser.parse_args())
    inst_str = args['str']

    u = load_from_file('upstox.pickle')
    u.get_master_contract('MCX_FO') # get contracts for MCX FO

    u.set_on_order_update (my_generic_event_handler)
    u.set_on_quote_update (my_generic_event_handler)

    try:
        u.subscribe(u.get_instrument_by_symbol('MCX_FO', inst_str), LiveFeedType.Full)
    except Exception as e:
        print("Could not subscribe: {}".format(e))

    u.start_websocket(False)


if __name__ == '__main__':
    main()
