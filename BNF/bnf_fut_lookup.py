from upstox_api.api import *
import argparse
from datetime import datetime
import os
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

    inst_str = 'banknifty'
    inst_cls = 'NSE_FO'

    u = load_from_file('upstox.pickle')
    u.get_master_contract('NSE_EQ')
    u.get_master_contract('NSE_FO')

    try:
        matches = u.search_instruments(inst_cls, inst_str)
        inst_fut = list(filter(lambda x: x.instrument_type != 'OPTIDX' , matches))

        for inst in inst_fut:
            print(inst)
    except Exception as e:
        print("Failed: {}".format(e))


if __name__ == '__main__':
    main()
