from upstox_api.api import *
from datetime import datetime
from pprint import pprint
import os, sys
from tempfile import gettempdir
import pickle

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

u = load_from_file('upstox.pickle')

print ("Balance:\n" , u.get_balance()) # get balance / margin limits
print ("Profile:\n", u.get_profile()) # get profile
print ("Holdings:\n", u.get_holdings()) # get holdings
print ("Positions:\n", u.get_positions()) # get positions

u.get_master_contract('nse_eq') # get contracts for NSE EQ

print(
        u.place_order(TransactionType.Buy,  # transaction_type
            u.get_instrument_by_symbol('NSE_EQ', 'UNITECH'),  # instrument
            1,  # quantity
            OrderType.StopLossLimit,  # order_type
            ProductType.OneCancelsOther,  # product_type
            8.0,  # price
            8.0,  # trigger_price
            0,  # disclosed_quantity
            DurationType.DAY,  # duration
            1.0,  # stop_loss
            1.0,  # square_off
            20)  # trailing_ticks 20 * 0.05
        )
