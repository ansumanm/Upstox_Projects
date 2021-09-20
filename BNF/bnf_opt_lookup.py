import copy
from upstox_api.api import *
import argparse
from datetime import datetime
from pprint import pprint
import os, sys
import time
from tempfile import gettempdir
import logging
import pickle
import subprocess

u = None

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

# inst_str = 'crudeoil19mayfut'
inst_str = 'zinc19mayfut'
# Filter example.
def main():
    parser = argparse.ArgumentParser("Banknifty Options lookup")
    parser.add_argument('-s', '--strike',
            help='strike price to search')
    parser.add_argument('-e', '--expiry',
            help='Expiry to search')

    args = vars(parser.parse_args())
    try:
        inst_strike = float(args['strike'])
        inst_expiry = args['expiry']
    except:
        print("exec -s inst -c class")
        sys.exit(0)

    u = load_from_file('upstox.pickle')
    u.get_master_contract('NSE_EQ')
    u.get_master_contract('NSE_FO')

    try:
        matches = u.search_instruments('NSE_FO', 'banknifty')
        inst_opt = list(filter(lambda x: x.strike_price == inst_strike, matches))

        inst_opt_sorted = sorted(inst_opt, key=lambda x: int(x.expiry))
        for inst in inst_opt_sorted:
            expiry_str = datetime.fromtimestamp(int(inst.expiry)/1000).strftime("%d%b")
            print(inst.symbol, inst.closing_price, expiry_str)
    except Exception as e:
        print("Failed: {}".format(e))


if __name__ == '__main__':
    main()
