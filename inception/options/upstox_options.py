import copy
from upstox_api.api import *
# from datetime import datetime
import datetime
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

def get_last_restart_delay():
    try:
        with open(".last_restart_sec", "r") as f:
            return int(f.read())
    except Exception as e:
        return 2

def set_last_restart_delay(delay):
    try:
        with open(".last_restart_sec", "w") as f:
            return int(f.write("{}".format(delay)))
    except Exception as e:
        print("Could not set delay. Exiting...")
        sys.exit(0)

# Reset only if delay was more than one hour.
def reset_restart_delay():
    delay = get_last_restart_delay()

    if delay >= 3600:
        try:
            os.remove(".last_restart_sec")
        except Exception as e:
            pass


def spawn_myself():
    try:
        cmd = copy.deepcopy(sys.argv)
        cmd.insert(0,'python')

        delay = get_last_restart_delay()
        set_last_restart_delay(2*delay)
        logging.critical(
                """
                Upstox postback restarting in {} seconds.
                """.format(delay))
        time.sleep(delay)

        os.execvp(cmd[0], cmd)
    except Exception as e:
        print("Failed to spawn myself: {}".format(e))
        sys.exit(0)

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

def telegram_handler(event, handler):
    logging.critical("Handler: %s Event: %s" % (handler, str(event)))

def my_generic_event_handler (event, handler):
    print ("Handler: %s Event: %s" % (handler, str(event)))

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

def my_on_quote_update_handler (event):
    pass
    # my_generic_event_handler(event, "on_quote_update")

def my_on_disconnect_handler (event):
    my_generic_event_handler(event, "on_disconnect")

def my_on_error_handler (ws, event):
    telegram_handler(event, "on_error")
    # Lets login again.
    subprocess.run(['python3', 'upstox_auto_login.py'])
    spawn_myself() 

inf = I()
reset_restart_delay()

u = load_from_file('upstox.pickle')

u.get_master_contract('NSE_EQ')
u.get_master_contract('NSE_FO')

tatasteel_nse_fo = u.search_instruments('NSE_FO', 'tatasteel')

"""
tatasteel type: namedtuple
Instrument(exchange='NSE_FO', token=115806, parent_token=3499, symbol='tatasteel19jan750pe', name='', closing_price=231.0, expiry='1548873000000', strike_price=750.0, tick_size=5.0, lot_size=1061, instrument_type='OPTSTK', isin=None)
"""

cur_month = datetime.date.today().timetuple().tm_mon
# print(tatasteel_nse_fo)
# print(type(tatasteel_nse_fo))
for inst in tatasteel_nse_fo:
    dt = datetime.datetime.fromtimestamp(int(inst.expiry)/1000.0)
    mon = dt.timetuple().tm_mon

    if (mon == cur_month):
        # full_feed = u.get_live_feed(u.get_instrument_by_symbol('NSE_FO', inst.symbol), LiveFeedType.Full)
        # print(full_feed)

# full_feed = u.get_live_feed(u.get_instrument_by_symbol('NSE_FO', 'tatasteel19jan750ce'), LiveFeedType.Full)
# print(full_feed)
# print(type(full_feed))
