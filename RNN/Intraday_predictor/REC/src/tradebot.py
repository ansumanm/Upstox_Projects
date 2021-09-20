"""
Automated trade program.
1) Get the open price
2) Get the predicted HLC
3) Trade.
"""
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
from predict import predict_HLC

u = None

"""
We need ATR to use this function.
"""
def long_candle(pClose, pOpen, pATR):
    """
    Instead of pClose, pOpen, it should be 
    pLow, pHigh.
    """
    var1 = abs(pClose - pOpen)

    if (pATR != 0): 
        ratio = var1/pATR
    else:
        return False

    if (ratio >= 1):
        return True
    else:
        return False


def bull_candle(pHigh, pLow, pClose):
    var1 = pHigh - pLow
    var2 = pHigh - pClose
    if (var2 != 0):
        ratio = var1/var2
    else:
        return True

    if (ratio >= 4):
        return True
    else:
        return False

def bear_candle(pHigh, pLow, pClose):
    var1 = pHigh - pLow
    var2 = pClose - pLow
    if (var2 != 0):
        ratio = var1/var2
    else:
        ''' Close = Low, Indicates a Bear candle. ''' 
        return True

    if (ratio >= 4):
        return True
    else:
        return False


def running_candle(pHigh, pLow, pClose, pOpen):
    var1 = pHigh - pLow
    var2 = abs(pClose - pOpen)
    if (var2 != 0):
        ratio = var1/var2
    else:
        return False
    
    if (ratio >= 1) and (ratio <= 1.5):
        return True
    else:
        return False

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
    """
    Predicted Low crossover strategy:
    Wait for the price to fall below predicted Low.
    Put a SL Buy order at predicted low with SL at Low.

    Predicted High crossover strategy:
    Wait for the price to fall below predicted Low.
    Put a SL Buy order at predicted low with SL at Low.
    """
    pass
    # my_generic_event_handler(event, "on_quote_update")

def my_on_disconnect_handler (event):
    my_generic_event_handler(event, "on_disconnect")

def my_on_error_handler (ws, event):
    telegram_handler(event, "on_error")
    # Lets login again.
    subprocess.run(['python3', 'upstox_auto_login.py'])
    spawn_myself() 

u = load_from_file('upstox.pickle')

u.set_on_order_update (my_on_order_update_handler)
u.set_on_trade_update (my_on_trade_update_handler)
u.set_on_quote_update (my_on_quote_update_handler)
u.set_on_disconnect (my_on_disconnect_handler)
u.set_on_error (my_on_error_handler)

# u.set_on_quote_update(event_handler_quote_update)
u.get_master_contract('NSE_EQ')
u.get_master_contract('BSE_EQ')
u.get_master_contract('NSE_FO')

quote = u.get_live_feed(u.get_instrument_by_symbol('NSE_EQ', 'RECLTD'), LiveFeedType.Full)
Open = quote['open']
print(quote['open'])

(High, Low, Close) = predict_HLC(quote['open'])
print('''
        High {} Open {} Close {} Low {}
        '''.format(High, Open, Close, Low))

# Sanitize
if not (High > Close > Low):
    print('Predicted result insane..')
    sys.exit(0)


# Now the trading strategy part.
quantity = 100

"""
Scenario #1: Close < Open
Generally, the price will make a HIGH and then will make a LOW and then CLOSE.

Scenario #2: Close > Open
Generally, the price will make a LOW and then will make a HIGH and then CLOSE.

Sentiment: BULLISH, BEARISH, NEUTRAL
Formula: ((Close - Open)/Open) * 100
"""
def bull_strategy_on_quote_update_handler (event):
    print("BULL on_quote_update: {}".format(str(event))) 

def bear_strategy_on_quote_update_handler (event):
    print("BEAR on_quote_update: {}".format(str(event))) 

if bull_candle(High, Low, Close) and running_candle(High, Low, Close, Open):
    """
    We put a SL BUY order at Open price when it goes below Open. 
    SL at Low.
    """
    u.set_on_quote_update (bull_strategy_on_quote_update_handler)

if bear_candle(High, Low, Close) and running_candle(High, Low, Close, Open):
    """
    We put a SL SELL order at Open price when it goes above Open. 
    SL at High.
    """
    u.set_on_quote_update (bear_strategy_on_quote_update_handler)

"""
Neither a BULL, nor a BEAR
We got for a predicted LOW/HIGH crossover strategy.

Predicted Low crossover strategy:
    Wait for the price to fall below predicted Low.
    Put a SL Buy order at predicted low with SL at Low.

Predicted High crossover strategy:
    Wait for the price to fall below predicted Low.
    Put a SL Buy order at predicted low with SL at Low.
"""

"""
try:
    u.subscribe(u.get_instrument_by_symbol('NSE_EQ', 'RECLTD'), LiveFeedType.Full)
    print("Subscribed to RECLTD...")
except:
    print("!!!FAIL!!!: Subscribe to RECLTD...")
    pass

print("Starting upstocks websocket...")
u.start_websocket(False)
"""
