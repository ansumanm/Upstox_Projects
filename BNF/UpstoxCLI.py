#!/usr/bin/env python3
import os
import atexit
import readline
import pickle
from cmd2 import Cmd
from upstox_api.api import *
from ordermanager import ordermanager_client
import socket

history_file = os.path.expanduser('~/.UpstoxCLI_history')
if not os.path.exists(history_file):
    with open(history_file, "w") as fobj:
        fobj.write("")
readline.read_history_file(history_file)
atexit.register(readline.write_history_file, history_file)

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


class REPL(Cmd):
    prompt = "Upstox> "
    intro = """
	Upstox CLI 
    """

    def __init__(self):
        Cmd.__init__(self)

        self.u = load_from_file('upstox.pickle')
        self.u.get_master_contract('NSE_EQ')
        self.u.get_master_contract('NSE_FO')
        self.u.get_master_contract('BSE_EQ')

        self.option_symbols = None

    def search(self, inst_cls, inst_str):
        try:
            self.matches = self.u.search_instruments(inst_cls, inst_str)
        except Exception as e:
            print("Failed: {}".format(e))
            return None

    def do_search_fo(self, line):
        self.search('NSE_FO', line)

        if self.matches:
            for inst in self.matches:
                expiry_str = datetime.fromtimestamp(int(inst.expiry)/1000).strftime("%d%b")
                print("""
                {} {} {}
                """.format(inst.symbol, expiry_str, inst.instrument_type))
                
    def do_search_fut(self, line):
        self.search('NSE_FO', line)

        if self.matches:
            for inst in self.matches:
                if 'FUT' in inst.instrument_type:
                    expiry_str = datetime.fromtimestamp(int(inst.expiry)/1000).strftime("%d%b")
                    print("""
                    {} {} {}
                    """.format(inst.symbol, expiry_str, inst.instrument_type))
                

    def do_search_eq(self, line):
        self.search('NSE_EQ', line)

    def do_search_mcx(self, line):
        self.search('MCX_FO', line)

    def do_search_bse(self, line):
        self.search('BSE_EQ', line)

    def do_prepare_bnf_option_symbols(self, line):
        # banknifty19101729100pe format
        # banknifty[yy][mm][dd][strike][ce|pe]
        try:
            symbol_prefix = line.arg_list[0]
            strike = int(line.arg_list[1])
            no = int(line.arg_list[2])
        except Exception as e:
            print("Error: {}".format(str(e)))
            print("Symbol Format: banknifty[yy][mm][dd][strike][ce|pe]")
            print("Usage: prepare_bnf_option_symbols symbol_prefix strike number_of_strikes")
            print("Example: prepare_bnf_option_symbols banknifty191017 28000 10")
            return

        symbols = []

        # Add PEs
        start = strike
        step = -100
        stop = strike + step*no 
        for x in range(start, stop, step):
            symbol = symbol_prefix + str(x) + 'pe'
            symbols.append(symbol)

        # Add CEs
        start = strike
        step = 100
        stop = strike + step*no 
        for x in range(start, stop, step):
            symbol = symbol_prefix + str(x) + 'ce'
            symbols.append(symbol)

        print(symbols)
        self.option_symbols = symbols

    def do_subscribe_bnf_option_symbols(self, line):
        inst_cls = 'NSE_FO'

        if self.option_symbols is None:
            print("Prepare the option symbols first")
            print("Symbol Format: banknifty[yy][mm][dd][strike][ce|pe]")
            print("Usage: prepare_bnf_option_symbols symbol_prefix strike number_of_strikes")
            print("Example: prepare_bnf_option_symbols banknifty191017 28000 10")
            return

        for symbol in self.option_symbols:
            inst_str = symbol
            try:
                self.u.subscribe(self.u.get_instrument_by_symbol(inst_cls, inst_str), LiveFeedType.Full)
                print("Subscribed to {}".format(inst_str))
            except Exception as e:
                print("Could not subscribe: {}".format(e))

    def do_unsubscribe_bnf_option_symbols(self, line):
        inst_cls = 'NSE_FO'

        if self.option_symbols is None:
            print("Prepare the option symbols first")
            print("Symbol Format: banknifty[yy][mm][dd][strike][ce|pe]")
            print("Usage: prepare_bnf_option_symbols symbol_prefix strike number_of_strikes")
            print("Example: prepare_bnf_option_symbols banknifty191017 28000 10")
            return

        for symbol in self.option_symbols:
            inst_str = symbol
            try:
                self.u.unsubscribe(self.u.get_instrument_by_symbol(inst_cls, inst_str), LiveFeedType.Full)
                print("Unsubscribed from {}".format(inst_str))
            except Exception as e:
                print("Could not unsubscribe: {}".format(e))

    def do_subscribe_fo(self, line):
        inst_cls = 'NSE_FO'
        inst_str = line
        try:
            self.u.subscribe(self.u.get_instrument_by_symbol(inst_cls, inst_str), LiveFeedType.Full)
            print("Subscribed to {}".format(inst_str))
        except Exception as e:
            print("Could not subscribe: {}".format(e))

    def do_unsubscribe_fo(self, line):
        inst_cls = 'NSE_FO'
        inst_str = line
        try:
            self.u.unsubscribe(self.u.get_instrument_by_symbol(inst_cls, inst_str), LiveFeedType.Full)
            print("Unsubscribed from {}".format(inst_str))
        except Exception as e:
            print("Could not subscribe: {}".format(e))

    def do_get_live_feed(self, line):
        price = self.u.get_live_feed(self.u.get_instrument_by_symbol('NSE_FO', line), LiveFeedType.Full)
        print(price)
        print(type(price))

    def do_place_bo(self, line):
        """
        [BUY/SELL] QTY SCRIP PRICE SL TARGET TRAIL
        BUY 20 banknifty20febfut 31440 30 90 30 
        """
        inst_cls = 'NSE_FO'

        args = line.split()

        transaction_type = args[0]
        quantity = int(args[1])
        symbol = args[2]
        price = float(args[3])
        sl = float(args[4])
        target = float(args[5])
        trail = int(args[6])

        print(transaction_type, quantity, symbol, price, sl, target, trail)

        if transaction_type == "BUY":
            ttype = TransactionType.Buy
        elif transaction_type == "SELL":
            ttype = TransactionType.Sell
        else:
            print("Bad transaction type.")
            return

        try:
            result = u.place_order(ttype,  # transaction_type
                             u.get_instrument_by_symbol('NSE_FO', symbol),  # instrument
                             quantity,  # quantity
                             OrderType.StopLossLimit,  # order_type
                             ProductType.OneCancelsOther,  # product_type
                             price,  # price
                             price,  # trigger_price
                             0,  # disclosed_quantity
                             DurationType.DAY,  # duration
                             sl,  # stop_loss
                             target,  # square_off
                             trail*20)  # trailing_ticks 20 * 0.05

            print(result)
            print(type(result))
        except Exception as e:
            print(str(e))

        """
        print(
           self.u.place_order(TransactionType.Buy,  # transaction_type
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
        """

    def do_get_positions(self, line):
        p = self.u.get_positions() # get positions
        print("No. of positions: {}".format(len(p)))
        print(p)
        print(type(p))
        # Calculate Net quantity
        tot_quantity = 0
        for position in p:
            tot_quantity += int(position['net_quantity'])

        print("Total quantity: {}".format(tot_quantity))


    def do_get_historical_data(self, line):
        u = self.u
        data = u.get_ohlc(u.get_instrument_by_symbol('NSE_EQ', 'RELIANCE'), OHLCInterval.Minute_10, datetime.strptime('01/07/2017', '%d/%m/%Y').date(), datetime.strptime('07/07/2017', '%d/%m/%Y').date())
        print(data)
        print(type(data))

    def do_get_account_info(self, line):
        print("""
        +++++++++++ Balance +++++++++++
        """)
        print (self.u.get_balance()) # get balance / margin limits
        print("""
        +++++++++++ Profile +++++++++++
        """)
        print (self.u.get_profile()) # get profile
        print("""
        +++++++++++ Holdings +++++++++++
        """)
        print (self.u.get_holdings()) # get holdings
        print("""
        +++++++++++ Positions +++++++++++
        """)
        print (self.u.get_positions()) # get positions

    def do_ping(self, line):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 5001

        s.connect(('127.0.0.1', port))
        req = 'ping ' + line + '\n'
        s.send(req.encode())
        print("Sent: %s" % req)
        print(s.recv(1024))
        s.close()

    def do_sendcmd(self, line):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 5001

        s.connect(('127.0.0.1', port))

        cmd = line + '\n'
        s.send(cmd.encode())
        data_bytes = s.recv(4096)

        data_str = data_bytes.decode('utf-8')
        print(data_str)
        s.close()

    def modify_order(self, request):
        """
        Generic modify order function.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 5001

        s.connect(('127.0.0.1', port))

        cmd = "modify_order " + str(request) + '\n'
        print(cmd)
        s.send(cmd.encode())
        print(s.recv(1024))
        s.close()

    def do_modify_slm_order(self, line):
        """
        <order_id> <>
        """
        args = line.split()

        order_id = args[0]
        price = args[1]

        request = {}

        request['order'] = order_id
        request['price'] = 0
        request['trigger_price'] = args[1]

        self.modify_order(request)

    def do_modify_limit_order(self, line):
        """
        <order_id> <>
        """
        args = line.split()

        order_id = args[0]
        price = args[1]

        request = {}

        request['order'] = order_id
        request['price'] = args[1]
        request['trigger_price'] = args[1]

        self.modify_order(request)

    @staticmethod
    def place_order(order):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 5001

        s.connect(('127.0.0.1', port))

        cmd = "place_bracket_order " + str(order) + '\n'
        print(cmd)
        s.send(cmd.encode())
        print(s.recv(1024))
        s.close()


    def do_place_bracket_order(self, line):
        """
        [BUY | SELL] <symbol> <exchange> <quantity> <limit_price> <stoploss_point> <target_points> <trail_points>
        BUY SBIN NSE_EQ 10 180 2 2 1
        """
        args = line.split()

        self.order = {
                'ttype': args[0],
                'symbol': args[1],
                'exchange': args[2],
                'quantity': args[3],
                'ordertype': 'OCO',
                'producttype': 'INTRADAY',
                'price': args[4],
                'trigger_price': args[4],
                'disclosed_quantity': 0,
                'duration': 'DAY',
                'stoploss': args[5],
                'square_off': args[6],
                'trailing_ticks': args[7] 
                }

        self.place_order(self.order)


    def do_place_order_1(self, line):
        client = ordermanager_client()

        # resp = client.place_order(line)
        # print(resp)

        # symbol = self.u.get_instrument_by_symbol('NSE_EQ', 'SBIN')
        # print(symbol)
        # print(type(symbol))

        """
        order = {
                'ttype': 'BUY',
                'symbol': 'banknifty20aprfut',
                'quantity': 20,
                'ordertype': 'LIMIT',
                'producttype': 'INTRADAY',
                'price': 17225,
                'trigger_price': None,
                'disclosed_quantity': 0,
                'duration': 'DAY',
                'stoploss': None,
                'square_off': None,
                'trailing_ticks': None
                }
        """
        order = {
                'ttype': 'SELL',
                'symbol': 'banknifty20aprfut',
                'quantity': 20,
                'ordertype': 'OCO',
                'producttype': 'INTRADAY',
                'price': 19900,
                'trigger_price': 19750,
                'disclosed_quantity': 0,
                'duration': 'DAY',
                'stoploss': float(75),
                'square_off': float(1500),
                'trailing_ticks': int(75)
                }

        resp = client.place_order(str(order))
        print(resp)


if __name__ == '__main__':
    app = REPL()
    app.cmdloop()
