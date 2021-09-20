"""
Implement our trade engine using state machine
"""
import os
import sys
import pickle
import argparse
import sched
import time
import logging
import socket
from transitions import Machine
from influxdb import InfluxDBClient
import pandas as pd
from upstox_api.api import *
import talib


"""
TODO: Store candles and compute RSI, ATR
"""

"""
Generic functions
"""
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
    except Exception:
        return None

def bull_candle(pHigh, pLow, pClose):
    var1 = pHigh - pLow
    var2 = pHigh - pClose
    if (var2 != 0):
        ratio = var1/var2
    else:
        ''' Close = High, Indicates a Bull candle. ''' 
        logging.info("bull_candle: Close = High")
        return True

    logging.info("bull_candle: ratio {}".format(ratio))
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
        logging.info("bear_candle: Close = Low")
        return True

    logging.info("bear_candle: ratio {}".format(ratio))
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

def place_order(order):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 5001

    s.connect(('127.0.0.1', port))

    cmd = "place_bracket_order " + str(order) + '\n'
    logging.info("place_order(): %s" % cmd)
    s.send(cmd.encode())
    logging.info("place_order(): %s" % s.recv(1024).decode('utf-8'))
    s.close()


def enter_real_trade(go_long, Open, High, Low, Close):
    logging.info("enter_real_trade: Enter...")

    trail = get_trail()
    stoploss = get_stoploss()
    price = float(Close)
    target = float(150)

    if go_long is True:
        """
        Place limit Buy order at close price.
        Place Stoploss order at Low price
        Target is triple the risk.
        Trail is Stoploss
        """
        target_price = price + target
        stoploss_price = max((price - stoploss), Low)

        # We set the stoploss price to configured value (get_stoploss()). This is used to trail
        # the stoploss.
        set_position(direction='long', Entry=price, Stoploss=(price - stoploss + 10), Target=target_price)

        stoploss = price - stoploss_price
        order = TransactionType.Buy
    else:
        """
        Place limit Sell order at close price.
        Place Stoploss order at High price
        Target is triple the risk.
        Trail is Stoploss
        """
        target_price = price - target
        stoploss_price = min((price + stoploss), High)

        # We set the stoploss price to configured value (get_stoploss()). This is used to trail
        # the stoploss. Take 10 points profit to upset the brokerage costs.
        set_position(direction='short', Entry=price, Stoploss=(price + stoploss - 10), Target=target_price)
        stoploss = stoploss_price - price
        order = TransactionType.Sell
        # if go_long is True END

    # trail = int(20*stoploss) # granularity is 0.05
    # trail = 75 # granularity is 0.05. Lets trail 100 points.
    # stoploss = float(75)


    if OCO_mode_enabled():
        logging.info("Placing real order: target {} trail {} price {} stoploss {} order {}".format(target, trail, price, stoploss, order))
        try:
            u = Upstox().u
            result = u.place_order(order,  # transaction_type
                             # u.get_instrument_by_symbol('NSE_FO', get_symbol()),  # instrument
                             get_symbol(),
                             get_quantity(),  # quantity
                             OrderType.StopLossLimit,  # order_type
                             ProductType.OneCancelsOther,  # product_type
                             price,  # price
                             price,  # trigger_price
                             0,  # disclosed_quantity
                             DurationType.DAY,  # duration
                             stoploss,  # stop_loss
                             target,  # square_off
                             int(20*trail))  # trailing_ticks 20 * 0.05

            logging.info(result)
        except Exception as e:
            logging.info(str(e))
            return False
    else:
        """
        Use our indigenously built order manager process.
        """
        if go_long is True:
            order = 'BUY'
        else:
            order = 'SELL'

        order = {
                'ttype': order, 
                'symbol': Symbol().symbol_str,
                'exchange': 'NSE_FO',
                'quantity': get_quantity(),
                'ordertype': 'OCO',
                'producttype': 'INTRADAY',
                'price': price,
                'trigger_price': price,
                'disclosed_quantity': 0,
                'duration': 'DAY',
                'stoploss': stoploss,
                'square_off': target,
                'trailing_ticks': trail 
                }

        place_order(order)

    return True


def enter_trade(go_long, Open, High, Low, Close):
    if RealMode().enabled():
        return enter_real_trade(go_long, Open, High, Low, Close)

    logging.info("Real mode not enabled...")
    # Test mode
    # Just Create position object
    if go_long is True:
        """
        Place limit Buy order at close price.
        Place Stoploss order at Low price
        Target is triple the risk.
        Trail is Stoploss
        """
        target = Close + (Close - Low)*3
        set_position(direction='long', Entry=Close, Stoploss=Low, Target=target)

    else:
        """
        Place limit Sell order at close price.
        Place Stoploss order at High price
        Target is triple the risk.
        Trail is Stoploss
        """
        target = Close + (Close - Low)*3
        set_position(direction='long', Entry=Close, Stoploss=Low, Target=target)

    return True


def placeTrade(Open, High, Low, Close, ATP):
    rc = False
    logging.info("placeTrade: Enter Open {} High {} Low {} Close {} ATP {}".format(Open, High, Low, Close, ATP))

    if ((Close > ATP) and bull_candle(High, Low, Close)):
        rc = enter_trade(True, Open, High, Low, Close)
    elif ((Close < ATP) and bear_candle(High, Low, Close)):
        rc = enter_trade(False, Open, High, Low, Close)
    else:
        logging.info("placeTrade: Returning without entering trade...")
        return False

    return rc
"""
Class Declarations
"""
class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

class Symbol(Singleton):
    symbol = None
    symbol_str = None

    def get_symbol(self):
        return self.symbol

    def set_symbol(self, symbol_):
        self.symbol = Upstox().u.get_instrument_by_symbol('NSE_FO', symbol_)
        self.symbol_str = symbol_

def get_symbol():
    return Symbol().get_symbol()

def set_symbol(symbol_):
    Symbol().set_symbol(symbol_)

class Trail(Singleton):
    trail = int(75)

    def get_trail(self):
        return self.trail

    def set_trail(self, trail):
        self.trail = trail

def get_trail():
    return Trail().get_trail()

def set_trail(val):
    Trail().set_trail(val)

class Stoploss(Singleton):
    sl = float(75)

    def get_sl(self):
        return self.sl

    def set_sl(self, sl):
        self.sl = sl

def get_stoploss():
    return Stoploss().get_sl()

def set_stoploss(sl):
    Stoploss().set_sl(sl)

class Quantity(Singleton):
    quantity = 20

    def get_qty(self):
        return self.quantity

    def set_qty(self, qty):
        self.quantity = qty

def get_quantity():
    return Quantity().get_qty()

def set_quantity(qty):
    return Quantity().set_qty(qty)

class OCO_mode(Singleton):
    oco_mode = False

    def enable(self):
        print("Real mode on...")
        self.oco_mode = True

    def enabled(self):
        return self.oco_mode

def OCO_mode_enabled():
    return OCO_mode().enabled()
        
def OCO_mode_enable():
    OCO_mode().enable()
        
class RealMode(Singleton):
    real_mode= False

    def enable(self):
        print("Real mode on...")
        self.real_mode = True

    def enabled(self):
        return self.real_mode
        
class Upstox(Singleton):
    u = None

    def __init__(self):
        if not self.u:
            self.u = load_from_file('upstox.pickle')
            self.u.get_master_contract('NSE_EQ')
            self.u.get_master_contract('NSE_FO')

class UnitTest(Singleton):
    ut = False

    def enable(self):
        self.ut = True

    def enabled(self):
        return self.ut

def UnitTestEnable():
    UnitTest().enable()

def UnitTestMode():
    return UnitTest().enabled()


class Client(Singleton):
    """
    InfluxDB Client
    """
    client = InfluxDBClient(host='localhost', port=8086, database='ticks')
    def __init__(self):
        pass

class Position(Singleton):
    real_position = []

    def set_direction(self, value):
        self.direction = value

    def get_direction(self):
        return self.direction

    def set_entry(self, value):
        self.entry = value

    def get_entry(self):
        return self.entry

    def set_sl(self, value):
        self.sl = value

    def get_sl(self):
        return self.sl

    def set_target(self, value):
        self.target = value

    def get_target(self):
        return self.target

def set_real_position(position):
    logging.info("set_real_position(): {}".format(str(position)))
    Position().real_position = position

def get_real_position():
    return Position().real_position

def get_net_quantity():
    positions = get_real_position()

    tot_quantity = 0

    for position in positions:
        tot_quantity += int(position['net_quantity'])

    logging.info("get_net_quantity(): {}".format(tot_quantity))
    return tot_quantity;


def set_position(direction, Entry, Stoploss, Target):
    logging.info("[set_position] direction: {} Entry: {} Stoploss: {} Target: {}"\
            .format(direction, Entry, Stoploss, Target))
    pObj = Position()
    pObj.set_direction(direction)
    pObj.set_entry(Entry)
    pObj.set_sl(Stoploss)
    pObj.set_target(Target)

def get_position():
    # Return the tuple
    x = Position()
    return (x.direction, x.entry, x.sl, x.target)

class Countdown(Singleton):
    """
    Countdown to exit.
    """
    countdown = 30

    def get(self):
        return self.countdown

    def dec(self):
        self.countdown = self.countdown - 1

    def reset(self):
        if UnitTestMode():
            self.countdown = 1
        else:
            self.countdown = 30


class Pivot(Singleton):
    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

def set_pivot(value):
    pObj = Pivot()
    pObj.set_value(value)

def get_pivot():
    pObj = Pivot()
    return pObj.get_value()

class Scheduler(Singleton):
    s = sched.scheduler(time.time, time.sleep)

    @staticmethod
    def get_secs_since_epoch(hr, mn):
        # Compute secs from epoch at market open time.
        # Market opens at 9:15 a.m for NFO and 10 a.m
        # for MCX.
        c_tm = time.localtime(time.time())

        """
        Index   Attribute   Values
        0   tm_year (for example, 1993)
        1   tm_mon  range [1, 12]
        2   tm_mday range [1, 31]
        3   tm_hour range [0, 23]
        4   tm_min  range [0, 59]
        5   tm_sec  range [0, 61]; see (2) in strftime() description
        6   tm_wday range [0, 6], Monday is 0
        7   tm_yday range [1, 366]
        8   tm_isdst    0, 1 or -1; see below
        N/A tm_zone abbreviation of timezone name
        N/A tm_gmtoff   offset east of UTC in seconds
        """

        t = (c_tm.tm_year, c_tm.tm_mon, c_tm.tm_mday, hr, mn, 0, 0, 0, 0)
        return round(time.mktime(t))

    # Class variable
    seconds_since_epoch_at_mkt_open = get_secs_since_epoch.__func__(9, 15)
    seconds_since_epoch_at_shop_close = get_secs_since_epoch.__func__(14, 45)
    seconds_since_epoch_at_trade_start = get_secs_since_epoch.__func__(9, 45)

    @staticmethod
    def get_next_run_time():
        """
        Run every 1 min 
        """
        period_sec = 60
        now = round(time.time())

        secs_since_mkt_open = now - Scheduler.seconds_since_epoch_at_mkt_open
        return ((period_sec - secs_since_mkt_open%period_sec) + 1)

    def __init__(self):
        pass

    def schedule(self, func):
        priority = 1
        next_run_time = self.get_next_run_time()
        self.s.enter(next_run_time, priority, func)

class Engine(Singleton):
    """
    Trade logic implemented as state machine
    """
    states = ['INIT', 'WAITING', 'PLACE_TRADE','TRADE_PLACED', 'IN_TRADE', 'EXIT']
    transitions = [
            { 'trigger': 'run', 'source': 'INIT', 'dest': 'WAITING', 'unless': 'resume_trade' },
            { 'trigger': 'run', 'source': 'INIT', 'dest': 'IN_TRADE', 'conditions': 'resume_trade' },
            { 'trigger': 'run', 'source': 'WAITING', 'dest': 'PLACE_TRADE', 'conditions': 'place_trade_cond' },
            { 'trigger': 'run', 'source': 'PLACE_TRADE', 'dest': 'WAITING', 'unless': 'place_trade_status_fn' },
            { 'trigger': 'run', 'source': 'PLACE_TRADE', 'dest': 'TRADE_PLACED', 'conditions': 'place_trade_status_fn' },
            { 'trigger': 'run', 'source': 'TRADE_PLACED', 'dest': 'IN_TRADE', 'conditions': 'in_trade_cond' },
            { 'trigger': 'run', 'source': 'PLACE_TRADE', 'dest': 'EXIT', 'unless': 'in_trade_cond' },
            { 'trigger': 'run', 'source': 'IN_TRADE', 'dest': 'EXIT', 'conditions': 'in_trade_to_exit' },
            { 'trigger': 'run', 'source': 'EXIT', 'dest': 'WAITING', 'conditions': 'exit_to_wait_cond'}
            ]
    df = pd.DataFrame()
    machine = None

    # Variables to track trailing.
    next_trail_at = None

    # To track if place trade succeeded.
    place_trade_status = None

    def __init__(self):
        if self.machine is None:
            # Initialize state machine
            self.machine = Machine(model=self, states=self.states,\
                    prepare_event='prepare',
                    finalize_event='finalize',
                    transitions=self.transitions,\
                    initial='INIT',\
                    auto_transitions=False, ignore_invalid_triggers=True,
                    queued=True)

    def __del__(self):
        pass

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    @classmethod
    def save_state(cls):
        logging.info('Saving state..')
        dump_to_file(Position(), 'position.pkl')

    @classmethod
    def restore_state(cls):
        logging.info('Restoring state..')
        position_obj = load_from_file('position.pkl')
        
        if position_obj is not None:
            set_position(position_obj.get_direction(),
                    position_obj.get_entry(),
                    position_obj.get_sl(),
                    position_obj.get_target())

    def prepare(self):
        print("""
        [{}] prepare
        """.format(Engine().state))
        query = 'SELECT difference(last("vtt")) AS "VolumeD", \
                 first("ltp") AS "Open", \
                 max("ltp") AS "High", \
                 min("ltp") AS "Low", \
                 last("ltp") AS "Close", \
                 last("atp") AS "ATP" \
                 FROM "FeedFull" \
                 WHERE ("symbol" =~ /^%s$/) AND \
                 time >= now() - 15m GROUP BY time(1m)' \
                 % Symbol().symbol_str

        client = Client().client
        result = client.query(query)
        data = result.raw

        try:
            self.df = pd.DataFrame(data['series'][0]['values'])
            self.df.columns = data['series'][0]['columns']
        except:
            pass

        # Compute the RSI.
        try:
            self.rsi = talib.RSI(self.df['Close'], timeperiod=14)
            logging.info("RSI: {}".format(self.rsi.iloc[-2]))
        except Exception as e:
            print("Failed to compute RSI: %s" % str(e))

        if RealMode().enabled() and (Engine().state == "IN_TRADE" or Engine().state == "TRADE_PLACED"):
            try:
                set_real_position(Upstox().u.get_positions())
            except Exception as e:
                print("get_positions() failed: %s" % str(e))

    @staticmethod
    def modify_slm_order(line):
        """
        <order_id> <>
        """
        args = line.split()

        order_id = args[0]
        price = args[1]

        request = {}

        request['order'] = order_id
        request['price'] = 0
        request['trigger_price'] = price

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 5001

        s.connect(('127.0.0.1', port))

        cmd = "modify_order " + str(request) + '\n'
        logging.info(cmd)
        s.send(cmd.encode())
        logging.info(s.recv(1024))
        s.close()

    def get_row(self):
        try:
            row = self.df.iloc[-2]
            return row
        except:
            return None

    def trail_stoploss(self):
        """
        Get Stoploss order ID
        Get the trail

        next_trail_at       Price at which we have to trail
        """
        logging.info("trail_stoploss() enter")
        trail_points = get_trail()

        (direction, entry, sl, target) = get_position()    

        if self.next_trail_at is None:
            # First time
            if direction is 'long':
                self.next_trail_at = entry + trail_points
            else:
                self.next_trail_at = entry - trail_points

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 5001

        s.connect(('127.0.0.1', port))

        line = 'get_slm_order_id'
        cmd = line + '\n'
        s.send(cmd.encode())
        data_bytes = s.recv(1024)
        s.close()

        try:
            slm_order_id = data_bytes.decode('utf-8')
            logging.info("slm_order_id: %s" % slm_order_id)
        except Exception as e:
            print("Failed to decode data_bytes: %s" % str(e))
            return

        if slm_order_id is None:
            logging.info("Received None slm order id. Returning.")
            return

        row = self.get_row()
        if direction == "long":
            """
            if (high - trail) > sl:
                update stoploss.
            """
            high = float(row.loc['High'])

            if high >= self.next_trail_at:
                new_sl = sl + trail_points
                logging.info("sl {} new_sl {}".format(sl, new_sl))
                """
                Place the modify order request
                Update the Positions object
                """
                line = "%s %s" % (slm_order_id, new_sl)
                self.modify_slm_order(line)
                set_position(direction=direction, Entry=entry,
                        Stoploss=new_sl, Target=target)
                self.next_trail_at += trail_points
            else:
                logging.info("High %f < next_trail_at %f. Returning." % (high, self.next_trail_at))
                return


        else:
            """
            if (low - trail) < sl:
                update stoploss.
            """
            low = float(row.loc['Low'])

            if low <= self.next_trail_at:
                # We will always trail by 1 window.
                new_sl = sl - trail_points
                logging.info("sl {} new_sl {}".format(sl,  new_sl))

                line = "%s %s" % (slm_order_id, new_sl)
                self.modify_slm_order(line)
                set_position(direction=direction, Entry=entry,
                        Stoploss=new_sl, Target=target)
                self.next_trail_at -= trail_points
            else:
                logging.info("Low %f > next_trail_at %f. Returning." % (low, self.next_trail_at))
                return

    def finalize(self):
        logging.info("""
        [{}] finalize
        """.format(Engine().state))
        Scheduler().schedule(worker_func)

        if RealMode().enabled() and not OCO_mode_enabled():
            if Engine().state == "IN_TRADE":
                """
                lets trail stoploss
                """
                self.trail_stoploss()
                return

        if Engine().state == "IN_TRADE":
            # Adjust stoploss if profit = SL.
            row = self.get_row()
            close = float(row.loc['Close'])
            (direction, entry, sl, target) = get_position()    

            if (sl != entry):
                if (abs(close - entry) > abs(entry - sl)):
                    logging.info("[SL ADJUST] direction: {} Entry: {} Stoploss: {} Target: {}"\
                            .format(direction, entry, sl, target))
                    set_position(direction=direction, Entry=entry,
                            Stoploss=entry, Target=target)

    def prepare_func(self):
        pass

    """
    Callbacks
    """
    def on_enter_WAITING(self):
        self.place_trade_status = False
        self.next_trail_at = None

    def on_enter_PLACE_TRADE(self):
        row = self.get_row()
        logging.info("on_enter_PLACE_TRADE: {}".format(row))

        rc = placeTrade(row.loc['Open'], row.loc['High'], row.loc['Low'], row.loc['Close'], row.loc['ATP'])

        if rc is True:
            logging.info("placeTrade returned True")
            # Go to TRADE_PLACED state.
            self.place_trade_status = True
        else:
            # Go back to waiting.
            logging.info("placeTrade returned False")
            self.place_trade_status = False

        self.run()

    def on_enter_IN_TRADE(self):
        logging.info("on_enter_IN_TRADE(): Enter")
        self.save_state();
        Countdown().reset()

    def on_enter_EXIT(self):
        try:
            os.remove("position.pkl")
        except:
            pass

    """
    Transition conditions
    """
    def place_trade_status_fn(self):
        # This variable should be initialized in WAITING state
        return self.place_trade_status

    def resume_trade(self):
        """
        if there is a position.pkl file, it implies, we are in trade
        """
        if os.path.isfile('position.pkl'):
            return True
        else:
            return False

    def exit_to_wait_cond(self):
        # We close the shop after 3 p.m.
        now = round(time.time())

        if now > Scheduler().seconds_since_epoch_at_shop_close:
            logging.info("Closing shop...")
            sys.exit(0)

        return True

    def place_trade_cond(self):
        """
        Don't start trade before 9:45 a.m.
        """
        s = Scheduler()
        now = round(time.time())
        if now < s.seconds_since_epoch_at_trade_start:
            return

        if now > s.seconds_since_epoch_at_shop_close:
            logging.info("Closing shop...")
            sys.exit(0)

        rc = False
        # Check VolumeD of row 1
        row = self.get_row()
        print("Place Trade Condition:")
        print(row)

        if UnitTestMode():
            set_position(direction='long', Entry=row.loc['Close'], Stoploss=row.loc['Low'], Target=row.loc['High'])
            return True

        try:
            volumeD = int(row.loc['VolumeD'])
        except Exception as e:
            print(str(e))
            return

        # Inline function to check entry..
        def checkEntry(Open, High, Low, Close, ATP):
            logging.info("checkEntry: Enter {} {} {} {} {}".format(Open, High, Low, Close, ATP))

            if (((Close > ATP) and bull_candle(High, Low, Close))) or \
                    (((Close < ATP) and bear_candle(High, Low, Close))):
                return True
            else:
                return False

        if volumeD > 50000:
            logging.info("Got a high volume candle...")
            rc = checkEntry(row.loc['Open'], row.loc['High'], row.loc['Low'], row.loc['Close'], row.loc['ATP'])

        return rc

    def in_trade_cond(self):
        if RealMode().enabled():
            if get_net_quantity() == 0:
                # We have exited position..
                return False
            else:
                # We are still in position..
                return True

    def in_trade_to_exit(self):
        # If we are in REAL mode, then just check if the positions
        if RealMode().enabled():
            if get_net_quantity() == 0:
                # We have exited position..
                return True
            else:
                # We are still in position..
                return False



def worker_func():
    print("""
    ############## WORKER #################
    """)
    Engine().run()

def main():
    parser = argparse.ArgumentParser("BNF Volume Breakout V1")
    parser.add_argument('-p', '--pp',
            help='pivot price')
    parser.add_argument('-u', action='store_true',
            help='Enable unit testing mode.')
    parser.add_argument('-o', action='store_true',
            help='Place trades using  Upstox OCO.')
    parser.add_argument('-r', action='store_true',
            help='Enable real mode. Trades will be taken.')
    parser.add_argument('-s', 
            help='Symbol to trade on.')
    parser.add_argument('-q', 
            help='Quantity to trade on.')
    parser.add_argument('-t', 
            help='Trail points.')
    parser.add_argument('-l', 
            help='Stoploss.')

    logging.basicConfig(filename="bnf_volume_breakout_trade.log", level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s')

    # args = vars(parser.parse_args())
    args = parser.parse_args()
    try:
        # pivot = int(args['pp'])
        pivot = int(args.pp)
        set_pivot(pivot)
    except:
        pass

    if args.u:
        UnitTestEnable()

    if args.o:
        OCO_mode_enable()

    if args.r:
        RealMode().enable()

        if args.s:
            set_symbol(args.s)
        else:
            print("Symbol mandatory in real mode.")
            sys.exit(0)

        if args.q:
            set_quantity(int(args.q))
        else:
            print("Quantity mandatory in real mode.")
            sys.exit(0)

        if args.t:
            set_trail(int(args.t))

        if args.l:
            set_stoploss(float(args.l))

    """Instantiate a connection to the InfluxDB."""
    # query = 'select Float_value from cpu_load_short;'
    # query_where = 'select Int_value from cpu_load_short where host=$host;'
    # query = 'SELECT last("ltp") FROM "FeedFull" WHERE time >= now() - 5m GROUP BY time(10s) fill(null)'
    # client = InfluxDBClient(host='localhost', port=8086, database='ticks')

    e = Engine()
    e.restore_state()

    s = Scheduler().s
    worker_func()
    s.run()


if __name__ == '__main__':
    main()
