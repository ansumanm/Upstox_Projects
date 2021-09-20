"""
Volume breakout strategy:
    Check delta volume every 1 min.
    If volume > 40K, check the candle type.
    In case of BULL candle, enter BUY,
    In case of BEAR candle, enter SELL.

    TODO: Add ATR consumed logic.
"""
from influxdb import InfluxDBClient
import pandas as pd
import time
import sched
import argparse
import logging
import sys


"""
Implement Global variables as singleton objects.
"""
class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

class Client(Singleton):
    client = InfluxDBClient(host='localhost', port=8086, database='ticks')
    def __init__(self):
        pass

class Position(Singleton):
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

def set_position(direction, Entry, Stoploss, Target):
    logging.info("[{}][ENTER] direction: {} Entry: {} Stoploss: {} Target: {}"\
            .format(time.ctime(), direction, Entry, Stoploss, Target))
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
    def get_secs_since_epoch_at_mkt_open(xch='NFO'):
        # Compute secs from epoch at market open time.
        # Market opens at 9:15 a.m for NFO and 10 a.m
        # for MCX.
        c_tm = time.localtime(time.time())

        hr = 9
        mn = 15

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
    seconds_since_epoch_at_mkt_open = get_secs_since_epoch_at_mkt_open.__func__()
    # seconds_since_epoch_at_mkt_open = get_secs_since_epoch_at_mkt_open()

    @staticmethod
    def get_next_run_time():
        """
        Run every 1 min 
        """
        period_sec = 60
        now = round(time.time())

        secs_since_mkt_open = now - Scheduler.seconds_since_epoch_at_mkt_open
        print("get_next_run_time: now {} Scheduler.seconds_since_epoch_at_mkt_open {}".format(now, Scheduler.seconds_since_epoch_at_mkt_open))
        print("secs_since_mkt_open {}".format(secs_since_mkt_open))
        return ((period_sec - secs_since_mkt_open%period_sec) + 1)

    def __init__(self):
        pass

    def schedule(self, func):
        print("Scheduling..{}".format(func))
        priority = 1
        next_run_time = self.get_next_run_time()
        print("Next run time in {} sec".format(next_run_time))
        self.s.enter(next_run_time, priority, func)
        print("Queue: {}".format(self.s.queue))

def bull_candle(pHigh, pLow, pClose):
    var1 = pHigh - pLow
    var2 = pHigh - pClose
    if (var2 != 0):
        ratio = var1/var2
    else:
        ''' Close = High, Indicates a Bull candle. ''' 
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

def enter_trade(go_long, Open, High, Low, Close):
    # Test mode
    # Just Create position object
    if go_long is True:
        """
        Place limit Buy order at close price.
        Place Stoploss order at Low price
        Target is double the risk.
        """
        target = Close + (Close - Low)*3
        set_position(direction='long', Entry=Close, Stoploss=Low, Target=target)
    else:
        """
        Place limit Sell order at close price.
        Place Stoploss order at High price
        Target is double the risk.
        """
        target = Close - (High - Close)*3
        set_position(direction='short', Entry=Close, Stoploss=High, Target=target)

    Countdown().reset()

def processCandle(Open, High, Low, Close):
    print("processCandle: Enter")
    pp = get_pivot()
    print("processCandle: pivot: {}".format(pp))

    if (Close > pp) and bull_candle(High, Low, Close):
        enter_trade(True, Open, High, Low, Close)
    elif (Close < pp) and bear_candle(High, Low, Close):
        enter_trade(False, Open, High, Low, Close)
    else:
        print("processCandle: Returning without entering trade...")
        return False

    Scheduler().schedule(intrade_func)
    return True

def intrade_func():
    print("""

    ############# IN TRADE ############

    """)
    query = 'SELECT difference(last("vtt")) AS "VolumeD", first("ltp") AS "Open", max("ltp") AS "High", min("ltp") AS "Low", last("ltp") AS "Close", last("asks_0_price") AS "Ask", last("bids_0_price") AS "Bid" FROM "FeedFull" WHERE time >= now() - 2m GROUP BY time(1m)'

    client = Client().client
    result = client.query(query)
    data = result.raw

    df = pd.DataFrame(data['series'][0]['values'])
    df.columns = data['series'][0]['columns']
    print(df)

    # Check if SL is hit, or target is complete.
    row = df.iloc[1]
    (direction, entry, sl, target) = get_position()    

    low = float(row.loc['Low'])
    high = float(row.loc['High'])
    close = float(row.loc['Close'])
    # open_ = float(row.low['Open'])

    sl_hit = False
    target_hit = False
    if direction == 'long':
        if low <= sl:
            sl_hit = True
        elif high >= target:
            target_hit = True
    else:
        if high >= sl:
            sl_hit = True
        elif low <= target:
            target_hit = True

    if (sl_hit == True) or (target_hit == True):
        if target_hit == True:
            pnl = "(Profit) " + str(abs(target - entry))

        if sl_hit == True:
            pnl = "(Loss) " + str(abs(sl - entry))

        logging.info("[{}][EXIT] direction: {} Entry: {} Stoploss: {}\
                Target: {} target_hit: {} sl_hit: {} Pnl: {}"\
                .format(time.ctime(), direction, entry,\
                sl, target, target_hit, sl_hit, pnl))
        # Prepare for next trade
        Scheduler().schedule(worker_func)
    else:
        # We exit in max 30 mins if our target is not met.
        if Countdown().get() <= 0:
            logging.info("[{}][COUNTDOWN EXIT] direction: {} Entry: {} Stoploss: {}\
                    Target: {} LTP: {} "\
                    .format(time.ctime(), direction, entry,\
                    sl, target, close))
            Scheduler.schedule(worker_func)
            return
        else:
            Countdown().dec()


        # Adjust stoploss if profit = SL.
        if (sl != entry):
            if (abs(close - entry) > abs(entry - sl)):
                logging.info("[{}][SL ADJUST] direction: {} Entry: {} Stoploss: {} Target: {}"\
                        .format(time.ctime(), direction, entry, sl, target))
                set_position(direction=direction, Entry=entry,
                        Stoploss=entry, Target=target)

        Scheduler().schedule(intrade_func)

def worker_func():
    print("""

    ############## WORKER #################

    """)
    query = 'SELECT difference(last("vtt")) AS "VolumeD", first("ltp") AS "Open", max("ltp") AS "High", min("ltp") AS "Low", last("ltp") AS "Close", last("asks_0_price") AS "Ask", last("bids_0_price") AS "Bid" FROM "FeedFull" WHERE time >= now() - 2m GROUP BY time(1m)'

    client = Client().client
    result = client.query(query)
    data = result.raw

    df = pd.DataFrame(data['series'][0]['values'])
    df.columns = data['series'][0]['columns']
    print(df)

    # Check VolumeD of row 1
    row = df.iloc[1]
    print(row)

    try:
        volumeD = int(row.loc['VolumeD'])
    except Exception as e:
        print(str(e))
        Scheduler().schedule(worker_func)
        return

    if volumeD > 40000:
        rc = processCandle(row.loc['Open'], row.loc['High'], row.loc['Low'], row.loc['Close'])
        if rc is True:
            # Would have scheduled another function to handle in trade
            # condition
            return

    Scheduler().schedule(worker_func)

def main(host='localhost', port=8086):
    parser = argparse.ArgumentParser("BNF Volume Breakout V1")
    parser.add_argument('-p', '--pp',
            help='pivot price')

    logging.basicConfig(filename="bnf_volume_breakout_trade.log", level=logging.INFO)

    args = vars(parser.parse_args())
    try:
        pivot = int(args['pp'])
        set_pivot(pivot)
    except:
        print("Please pass the pivot value")
        sys.exit(0)
    """Instantiate a connection to the InfluxDB."""
    # query = 'select Float_value from cpu_load_short;'
    # query_where = 'select Int_value from cpu_load_short where host=$host;'
    # query = 'SELECT last("ltp") FROM "FeedFull" WHERE time >= now() - 5m GROUP BY time(10s) fill(null)'
    # client = InfluxDBClient(host='localhost', port=8086, database='ticks')

    s = Scheduler().s
    worker_func()
    print("Queue: {}".format(s.queue))
    print(s)
    s.run()


if __name__ == '__main__':
    main()
