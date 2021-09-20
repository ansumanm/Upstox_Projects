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
sys.path.append('../infra/')
from infra import Infra as I

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

    args = vars(parser.parse_args())

    inst_str = args['str']

    u = load_from_file('upstox.pickle')
    u.get_master_contract('MCX_FO') # get contracts for MCX FO

    try:
        matches = u.search_instruments('MCX_FO', inst_str)
        inst_fut = list(filter(lambda x: x.strike_price == None , matches))

        for inst in inst_fut:
            print(inst)
    except Exception as e:
        print("Failed: {}".format(e))


if __name__ == '__main__':
    main()
