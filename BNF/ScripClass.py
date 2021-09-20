"""
ScripClass: Object holds information about the scrip.
"""
import logging
import sys
import json
import pickle
from upstox_api.api import *

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

class Scrip:
    def __init__(self):
        pass

    def init_from_tsb(self, tsb):
        u = load_from_file('upstox.pickle')
        u.get_master_contract('NSE_EQ')
        u.get_master_contract('NSE_FO')

        try:
            matches = u.search_instruments('NSE_FO', tsb)
        except Exception as e:
            print("Failed: {}".format(e))

        """
        Instrument(exchange='NSE_FO', token=51472, parent_token=26009,
        symbol='banknifty19octfut', name='', closing_price=27613.6,
        expiry='1572460200000', strike_price=None, tick_size=5.0, lot_size=20,
        instrument_type='FUTIDX', isin=None)
        """
        self.exchange = matches[0].exchange
        self.token = matches[0].token
        self.parent_token = matches[0].parent_token
        self.symbol = matches[0].symbol
        self.name = matches[0].name
        self.closing_price = matches[0].closing_price
        self.expiry = matches[0].expiry
        self.strike_price = matches[0].strike_price
        self.tick_size = matches[0].tick_size
        self.lot_size = matches[0].lot_size
        self.instrument_type = matches[0].instrument_type
        self.isin = matches[0].isin
        return True

    def init_from_token(self, token):
        """
        [{'instrument_token': '53501959', 'exchange_token':
        '208992', 'tradingsymbol': 'CRUDEOIL18FEBFUT', 'name':
            'Light Sweet Crude Oil', 'last_price': 0.0,
            'expiry': '2018-02-16', 'strike': 0.0, 'tick_size':
                1.0, 'lot_size': 1, 'instrument_type': 'FUT',
                'segment': 'MCX', 'exchange': 'MCX'}] 
        """
        scrip = json.loads(query_db_by_token(token))[0]
        for key, value in scrip.items():
            exec_str = 'self.{} = "{}"'.format(key, value)
            exec(exec_str)


def main():
    print("Testing Scrip Object")
    s = Scrip()
    s.init_from_tsb('CRUDEOIL18FEBFUT')
    print(s.segment)

    s2 = Scrip()
    s2.init_from_tsb('BANKNIFTY15FEB1828600PE')
    print(s2.segment)

if __name__ == '__main__':
     main()
