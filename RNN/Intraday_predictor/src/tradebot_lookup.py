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
    parser = argparse.ArgumentParser("Instrument lookup")
    parser.add_argument('-s', '--str',
            help='instrument to search')
    parser.add_argument('-c', '--class',
            help='[MCX_FO, NSE_EQ, BSE_EQ, NSE_FO]')

    args = vars(parser.parse_args())
    try:
        inst_str = args['str']
        inst_cls = args['class']
    except:
        print("exec -s inst -c class")
        sys.exit(0)

    u = load_from_file('upstox.pickle')
    u.get_master_contract('MCX_FO') # get contracts for MCX FO
    u.get_master_contract('NSE_EQ')
    u.get_master_contract('BSE_EQ')
    u.get_master_contract('NSE_FO')

    try:
        matches = u.search_instruments(inst_cls, inst_str)
        # inst_fut = list(filter(lambda x: x.strike_price == None , matches))

        for inst in matches:
            print(inst)
    except Exception as e:
        print("Failed: {}".format(e))


if __name__ == '__main__':
    main()
