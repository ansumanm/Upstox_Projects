'''
    Candle publisher version 3.0(2 threads only.)
    1) Subscribe to ticks publisher.
    2) Parse instrument configuration to get the publish period.
    3) Write one minute candles to DB.
    4) Publish the candles.
'''
import sys
import configparser
import argparse
import zmq
import json
import time
from datetime import datetime
import datetime as dt
import dateutil.parser
import os
import sqlite3
import numpy as np
import pandas as pd
import logging
from logging.handlers import RotatingFileHandler
import sched
from instruments import query_token_to_trade_symbol
from instruments import get_subscription_list
from ScripClass import Scrip
sys.path.append('../topic_pub_sub')
from TopicPubSub import TopicPublisher
from TopicPubSub import TopicSubscriber
import threading
from collections import namedtuple

Instrument = namedtuple('Instrument', ['exchange', 'token', 'parent_token',
    'symbol', 'name', 'closing_price', 'expiry', 'strike_price', 'tick_size',
    'lot_size', 'instrument_type', 'isin'])


dry_run = False

class Instrument_CP:
    """
    Class Variables shared by all instances.
    """
    print("Instrument_CP: Initializing Instrument_CP class.")
    ConfigFile = None

    tsb_list = None
    data_folder = None
    inst_conf = None

    day = None
    data_dir = None

    # Mapping between instrument symbol and instrument obj.
    instrument_symbol_to_obj_map = {}
    inst_conf_dict = {}
    seconds_since_epoch_at_mkt_open = {}
    publisher = None
    candle_publish_port = None
    ws_conf = None
    tradingsymbols = None

    # Blackholing detector logic
    last_ticks_timestamp = round(time.time() * 1000)

    @classmethod
    def init(cls):
        print("Instrument_CP initialization.")
        Instrument_CP.ConfigFile = "../config/kuber.conf"
        config = configparser.ConfigParser()
        config.read(Instrument_CP.ConfigFile)

        Instrument_CP.tsb_list = config['WS CONFIGURATION']['tradingsymbols'].split(',')
        Instrument_CP.data_folder = config['DATA CONFIGURATION']['data_folder']
        Instrument_CP.inst_conf = config['INSTRUMENT CONFIGURATION']
        Instrument_CP.ws_conf = config['WS CONFIGURATION']
        # Instrument_CP.tradingsymbols = Instrument_CP.ws_conf['tradingsymbols'].split(',')
        Instrument_CP.tradingsymbols = ['banknifty19sepfut']
        Instrument_CP.candle_publisher_default_ct = config['CandlePublisher']['default_candle_time']

        Instrument_CP.day = datetime.now().strftime('%Y-%m-%d')
        Instrument_CP.data_dir = Instrument_CP.data_folder + "/"

        """
        Initialize the per instrument configuration dictionary.
        """
        for tsb in Instrument_CP.tradingsymbols:
            """
            Initialize default configuration for all symbols.
            """
            Instrument_CP.inst_conf_dict[tsb] = {}

        for tsb in Instrument_CP.tradingsymbols:
            s = Scrip()
            s.init_from_tsb(tsb)
            """
            if tsb.lower() in Instrument_CP.inst_conf:
                Instrument_CP.inst_conf_dict[tsb] = eval(Instrument_CP.inst_conf[tsb.lower()])
            else:
                Instrument_CP.inst_conf_dict[tsb]['pre_publish'] = Instrument_CP.candle_publisher_default_ct * 60
                Instrument_CP.inst_conf_dict[tsb]['candle_period'] = Instrument_CP.candle_publisher_default_ct
            """
            Instrument_CP.inst_conf_dict[tsb]['pre_publish'] = int(Instrument_CP.candle_publisher_default_ct) * 60
            Instrument_CP.inst_conf_dict[tsb]['candle_period'] = int(Instrument_CP.candle_publisher_default_ct)

            s.exchange = 'NFO' # XXX Hardcoded
            Instrument_CP.inst_conf_dict[tsb]['xch'] = s.exchange
            Instrument_CP.seconds_since_epoch_at_mkt_open[tsb] = get_secs_since_epoch_at_mkt_open(s.exchange)
            """
            Create instrument objects and store in the map file.
            """
            # obj = Instrument_CP(tsb.upper())
            # Instrument_CP.instrument_symbol_to_obj_map[obj.tsb.upper()] = obj
            obj = Instrument_CP(tsb)
            Instrument_CP.instrument_symbol_to_obj_map[obj.tsb] = obj
            print("key {} value {}".format(tsb, Instrument_CP.inst_conf_dict[tsb]))

            """
            Also create a candles db for the instrument in the /dev/shm area.
            Populate it with 1000 candles.
            """
            # Create a candles db in /dev/shm also..
            sh_dir = ("/dev/shm/{}".format(tsb))
            try:
                os.stat(sh_dir)
            except Exception as e:
                print('Creating instrument directory %s' % (sh_dir))
                os.mkdir(sh_dir)

            # Read last 1000 candles.
            sql = """
                SELECT * FROM (SELECT * FROM %s ORDER BY Timestamp DESC LIMIT %s) sub 
                    ORDER BY Timestamp ASC
                        """ % ("candles", 1000)

            df = pd.DataFrame()
            with sqlite3.connect(obj.file_name) as conn:
                try:
                    df = pd.read_sql_query(sql=sql, con=conn)
                    # df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
                    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                    df = df.set_index('Timestamp', drop=True)
                except Exception as e:
                    print("[{}]Could not read candles:{}".format(obj.tsb, e))

            if df.empty is False:
                """
                Write candles to shared memory area.
                """
                with sqlite3.connect(obj.shm_file) as conn:
                    try:
                        df.to_sql(name='candles', con=conn, if_exists='replace')
                        print("Successfully updated shared memory for {}".format(obj.tsb))
                    except Exception as e:
                        print("[{}]Could not write candles to shm:{}".format(obj.tsb, e))

        zmq_conf = config['ZMQ CONFIGURATION']
        Instrument_CP.candle_publish_port = zmq_conf['candle_publish_port']
        Instrument_CP.publisher = TopicPublisher()
        Instrument_CP.publisher.init(Instrument_CP.candle_publish_port)


    def __init__(self, tsb):
        print("""
        Creating instrument obj: %s
        """ % tsb)
        """
        Create a connection to its sql database and store the connection.
        tsb: trading symbol.
        """
        self.s = Scrip()
        self.s.init_from_tsb(tsb)
        self.tsb = tsb
        self.instrument_dir = Instrument_CP.data_dir + self.tsb

        if dry_run is False:
            self.file_name = Instrument_CP.data_dir + self.tsb + "/candles.db"
            self.shm_file = '/dev/shm/{}/candles.db'.format(self.tsb)
        else:
            self.file_name = "./candles.db"
            self.shm_file = "./candles_shm.db"

        self.lock = threading.Lock()

        # Create data dir if not present.
        try:
            os.stat(self.instrument_dir)
        except Exception as e:
            print('Creating instrument directory %s' % (self.instrument_dir))
            os.mkdir(self.instrument_dir)

        # Create a candles db in /dev/shm also..
        try:
            sh_dir = ("/dev/shm/{}".format(self.tsb))
            os.stat(sh_dir)
        except Exception as e:
            print('Creating instrument directory %s' % (sh_dir))
            os.mkdir(sh_dir)


        self.pre_publish = 60
        self.candle_period_in_min = 1
        self.candle_period = 60
        self.xch = 'NFO'

        """
        Initialize dataframe
        """
        self.df = pd.DataFrame()
        self.spilldf = pd.DataFrame()

        """
        Add object to map.
        """
        Instrument_CP.instrument_symbol_to_obj_map[tsb] = self
        print("Init complete...")

    def __repr__(self):
        return "tsb {} pre_publish {} candle_period {} xch {}".format(self.tsb, self.pre_publish, self.candle_period, self.xch)

    def set_pre_publish(self, pre_publish):
        self.pre_publish = pre_publish

    def set_candle_period(self, candle_period):
        self.candle_period_in_min = candle_period
        self.candle_period = int(self.candle_period_in_min)*60

    def append(self, df):
        if self.df.empty is True:
            self.df = df
        else:
            self.df = pd.concat([self.df, df], ignore_index=True)

    @classmethod
    def get_obj(cls, tsb):
        """
        If the object exists in the map, return it.
        """
        if tsb in Instrument_CP.instrument_symbol_to_obj_map:
            return Instrument_CP.instrument_symbol_to_obj_map[tsb]
        else: 
            return cls(tsb)


secs_since_epoch_at_mkt_open = 0

def getDateTimeFromISO8601String(s):
    d = dateutil.parser.parse(s)
    return d

def subscribe_to_ticks_publisher(topic):
    """
    Subscribe to ticks publisher.
    topic:  Topic we are interested in to get updates.
    """
    ConfigFile = "../config/kuber.conf"
    config = configparser.ConfigParser()
    config.read(ConfigFile)

    zmq_conf = config['ZMQ CONFIGURATION']
    publish_port = zmq_conf['publish_port']

    print("Subscribing to topic %s at %s" % (topic, publish_port))
    sub = TopicSubscriber()

    try: 
        sub.init(topic, publish_port)
    except Exception as e:
        print("""
        Subscriber init failed: {}
        """.format(e))
        sys.exit(0)

    # Return the subscriber context.
    return sub


def ticks_subscriber():
    print("""
            ##### Subscriber thread. #####
          """)

    sub = subscribe_to_ticks_publisher('quote')

    # For eval() to succeed.
    true = True

    while True:
        try:
            quote = sub.sock_receive()
            new_tick = eval(quote)
        except Exception as e:
            print("""
            +++++++  Ticks Subscriber... +++++++
            """)
            print(str(e))
            sys.exit(0)

        tick = {}
        print("Tick Tock")

        try:
            tsb = new_tick['instrument'].symbol
            tick['instrument_token'] = new_tick['instrument'].token
            tick['last_price'] = new_tick['ltp']
            tick['High'] = new_tick['high']
            tick['Open'] = new_tick['open']
            tick['Low'] = new_tick['low']
            tick['Close'] = new_tick['close']
            tick['tsp'] = new_tick['ltt']
            tick['volume'] = new_tick['vtt']
            tick['oi'] = new_tick['oi']
            tick['atp'] = new_tick['atp']
            tick['total_buy_qty'] = new_tick['total_buy_qty']
            tick['total_sell_qty'] = new_tick['total_sell_qty']
            tick['tradingsymbol'] = tsb
        except Exception as e:
            print("ticks_subscriber: {}".format(e))
            continue

        df = pd.DataFrame(tick, index=[0])

        # Store the last tick timestamp
        Instrument_CP.last_ticks_timestamp = round(time.time() * 1000)

        df['tsp'] = pd.to_datetime(df['tsp'], unit='ms')
        df.tsp = df.tsp + pd.Timedelta('05:30:00')

        inst_obj = Instrument_CP.get_obj(tsb)

        inst_obj.lock.acquire()
        inst_obj.append(df)
        inst_obj.lock.release()

def get_mkt_close_time(xch):
    if xch == 'NFO':
        hr = 15
        mn = 30
    else:
        hr = 23
        mn = 55
    return hr,mn

def get_secs_since_epoch_at_mkt_close(xch='NFO'):
    # Compute secs from epoch at market open time.
    # Market opens at 9:15 a.m for NFO and 10 a.m
    # for MCX.
    c_tm = time.localtime(time.time())

    hr, mn = get_mkt_close_time(xch)

    t = (c_tm.tm_year, c_tm.tm_mon, c_tm.tm_mday, hr, mn, 0, 0, 0, 0)
    return round(time.mktime(t))

secs_at_mkt_close = {"NFO": get_secs_since_epoch_at_mkt_close("NFO"),\
        "MCX": get_secs_since_epoch_at_mkt_close("MCX"),\
        "BSE": get_secs_since_epoch_at_mkt_close("NFO")}

def get_mkt_open_time(xch):
    if xch == 'NFO':
        hr = 9
        mn = 15
    else:
        hr = 10
        mn = 00
    return hr,mn

def get_secs_since_epoch_at_mkt_open(xch='NFO'):
    # Compute secs from epoch at market open time.
    # Market opens at 9:15 a.m for NFO and 10 a.m
    # for MCX.
    c_tm = time.localtime(time.time())

    hr,mn = get_mkt_open_time(xch)

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

def get_secs_to_mkt_close(xch):
    """
    Period is in minutes.
    The same function works for MCX exchange also
    as MCX opens at 10 a.m.
    """
    now = round(time.time())

    # Number of secs that has elapsed since mkt open.
    secs_to_mkt_close = secs_at_mkt_close[xch] - now

    return secs_to_mkt_close

def get_next_run_time(period, inst):
    """
    Period is in minutes.
    The same function works for MCX exchange also
    as MCX opens at 10 a.m.
    """
    period_sec = int(period)
    now = round(time.time())
    # Dry run mode.
    if dry_run is True:
        print("Running in {} secs".format(now%period_sec))
        return (now%period_sec)


    # Number of secs that has elapsed since mkt open.
    secs_since_mkt_open = now - Instrument_CP.seconds_since_epoch_at_mkt_open[inst.tsb]

    """
    If we started before market open, schedule at market_open + period
    Note: We pass the number of seconds from now.
    """

    if (get_secs_to_mkt_close(inst.xch) < 0):
        logging.debug("sec to mkt close %d" % (get_secs_to_mkt_close(inst.xch)))
        logging.debug("market closed")
        return 0

    if secs_since_mkt_open < 0:
        logging.debug("market will open in %d" % secs_since_mkt_open)
        return (-(secs_since_mkt_open))
    else:
        # Period in secs.
        logging.debug("next tun time %d" % (period_sec - secs_since_mkt_open%period_sec))
        return ((period_sec - secs_since_mkt_open%period_sec) + 1)

def makeCandle(df, freq, xch):
    freq = int(freq)/60
    basevar = 0
    if (xch == 'NFO'):
        hr, mn = get_mkt_open_time(xch)
        basevar = mn%freq
    else:
        basevar = 0
    if(freq > 15):
        if (xch == 'NFO'):
            basevar = 15
        else:
            basevar = 0

    ResampledDF = pd.DataFrame()
    if 'tsp' in df.columns:
        df['tsp'] = pd.to_datetime(df['tsp'], unit='ms')
        df = df.set_index('tsp')
        candle_period = str(freq) + "T"
        ResampledDF['Open'] = df.last_price.resample(candle_period, base=basevar).first()
        ResampledDF['High'] = df.last_price.resample(candle_period, base=basevar).max()
        ResampledDF['Low'] = df.last_price.resample(candle_period, base=basevar).min()
        ResampledDF['Close'] = df.last_price.resample(candle_period, base=basevar).last()
        ResampledDF['instrument_token'] = df.instrument_token.resample(candle_period, base=basevar).first()
        ResampledDF['tradingsymbol'] = df.tradingsymbol.resample(candle_period, base=basevar).first()
        #if 'volume' in ResampledDF:
        ResampledDF['volume'] = df.volume.resample(candle_period, base=basevar).sum()
        ResampledDF.index.names = ['Timestamp']
    else:
        ResampledDF = ResampledDF.iloc[0:0]
    return ResampledDF

def makeSpillCandle(df, freq, xch):
    df = df.reset_index()
    logging.debug("freq = %d" % freq)
    freq = int(freq)/60
    logging.debug("freq = %d" % freq)
    basevar = 0
    if (xch == 'NFO'):
        hr, mn = get_mkt_open_time(xch)
        basevar = mn%freq
    else:
        basevar = 0
    if(freq > 15):
        if (xch == 'NFO'):
            basevar = 15
        else:
            basevar = 0
    ResampledDF = pd.DataFrame()
    logging.debug(list(df.columns))
    if 'Timestamp' in list(df.columns):
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df = df.set_index('Timestamp', drop=True)
        candle_period = str(freq) + "T"
        ResampledDF['Open'] = df.Open.resample(candle_period, base=basevar).last()
        ResampledDF['High'] = df.High.resample(candle_period, base=basevar).max()
        ResampledDF['Low'] = df.Low.resample(candle_period, base=basevar).min()
        ResampledDF['Close'] = df.Close.resample(candle_period, base=basevar).first()
        ResampledDF['instrument_token'] = df.instrument_token.resample(candle_period, base=basevar).first()
        ResampledDF['tradingsymbol'] = df.tradingsymbol.resample(candle_period, base=basevar).first()
        #if 'volume' in ResampledDF:
        ResampledDF['volume'] = df.volume.resample(candle_period, base=basevar).sum()
        ResampledDF.index.names = ['Timestamp']
    else:
        ResampledDF = ResampledDF.iloc[0:0]
    logging.debug("resampled df")
    logging.debug(ResampledDF)
    return ResampledDF

def write_df_to_candle_db(inst, mdf):
    file_name = inst.file_name

    logging.debug("Inside write_df_to_candle_db: %s" % file_name)

    with sqlite3.connect(file_name) as conn:
        mdf.to_sql("candles", conn, if_exists="append", index_label="Timestamp")
        conn.commit()

    # Also write the candle to shared memory.
    with sqlite3.connect(inst.shm_file) as conn:
        mdf.to_sql("candles", conn, if_exists="append", index_label="Timestamp")
        conn.commit()

def makeCandleUsingTimestamp(df, candle_period, xch, from_timestamp, to_timestamp):
    freq = int(candle_period)/60
    basevar = 0

    if (xch == 'NFO'):
        hr, mn = get_mkt_open_time(xch)
        basevar = mn%freq
    else:
        basevar = 0

    if(freq > 15):
        if (xch == 'NFO'):
            basevar = 15
        else:
            basevar = 0

    logging.debug("""
    makeCandleUsingTimestamp:
    =========================
    index: {}
    columns: {}
    tsp: {}
    """.format(df.index, df.columns, df['tsp']))

    ResampledDF = pd.DataFrame()
    if 'tsp' in df.columns:
        # df['tsp'] = pd.to_datetime(df['tsp'], unit='ms')
        from_tsp_dt = pd.Timestamp(from_timestamp, unit='ms', tz='Asia/Kolkata').to_datetime64() + pd.Timedelta('05:30:00')
        to_tsp_dt = pd.Timestamp(to_timestamp, unit='ms', tz='Asia/Kolkata').to_datetime64() + pd.Timedelta('05:30:00')
        logging.debug("""
        ################
        from: {}
        to: {}
        """.format(from_tsp_dt, to_tsp_dt))

        try:
            periodDF = df.loc[(df.tsp >= from_tsp_dt) & 
                    (df.tsp < to_tsp_dt)]
        except Exception as e:
            logging.debug("""
            Failed to create periodDF: {}
            """.format(e))
            return

        periodDF = periodDF.set_index('tsp')
        logging.debug("""
        makeCandleUsingTimestamp:
        {}
        """.format(str(periodDF)))

        candle_period = str(freq) + "T"
        ResampledDF['Open'] = periodDF.last_price.resample(candle_period, base=basevar).first()
        ResampledDF['High'] = periodDF.last_price.resample(candle_period, base=basevar).max()
        ResampledDF['Low'] = periodDF.last_price.resample(candle_period, base=basevar).min()
        ResampledDF['Close'] = periodDF.last_price.resample(candle_period, base=basevar).last()
        ResampledDF['instrument_token'] = periodDF.instrument_token.resample(candle_period, base=basevar).first()
        ResampledDF['tradingsymbol'] = periodDF.tradingsymbol.resample(candle_period, base=basevar).first()
        ResampledDF['volume'] = periodDF.volume.resample(candle_period, base=basevar).sum()
        ResampledDF['oi'] = periodDF.oi.resample(candle_period, base=basevar).sum()
        ResampledDF.index.names = ['Timestamp']
    else:
        ResampledDF = ResampledDF.iloc[0:0]
    return ResampledDF

def publish_candle(inst, run_type):
    """
    1) Get the previous candle period timestamp (from and to).
    2) Make candle with dataframe rows between from and to.
    3) Delete all rows of dataframe before to.
    """
    now = round(time.time()) 
    to_timestamp = now - now%inst.candle_period
    from_timestamp = to_timestamp - inst.candle_period

    logging.debug("""
    publish_candle: now {} from_timestamp {} to_timestamp {}
    """.format(time.ctime(now), time.ctime(from_timestamp), time.ctime(to_timestamp)))

    to_timestamp_ms = to_timestamp*1000
    from_timestamp_ms = from_timestamp*1000

    logging.debug("""
    Inside new publish candle
    """)
    if inst.df.empty:
        return

    inst.lock.acquire()
    try:
        mdf = makeCandleUsingTimestamp(inst.df, inst.candle_period, inst.xch,
                from_timestamp_ms, to_timestamp_ms)

    except Exception as e:
        logging.debug("makeCandleUsingTimestamp Failed: {}".format(e))
    finally:
        pass

    try:
        # Drop all rows before to_timestamp
        inst.df.drop(inst.df[inst.df['tsp'] < pd.Timestamp(to_timestamp_ms).to_datetime64()].index, inplace = True)
    except Exception as e:
        logging.debug("Rows delete Failed: {}".format(e))
    finally:
        pass

    logging.debug("""
    OHLC from {} to {} 
    ==================
    {}
    """.format(datetime.fromtimestamp(from_timestamp),
        datetime.fromtimestamp(to_timestamp),
        mdf))

    try:
        # Write to DB
        if (len(mdf.index) > 0):
            write_df_to_candle_db(inst, mdf)
            Instrument_CP.publisher.sock_send(inst.tsb, mdf.to_json(orient='records'))
        else:
            logging.debug("Nothing to write...Empty dataframe received.")
    except Exception as e:
        logging.debug("""
        Failed to publish: {}
        """.format(str(e)))
    finally:
        inst.lock.release()

def publish_candle_old(inst, run_type):
    logging.debug("[PUBLISH CANDLE START]%s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
    logging.info('{}'.format(inst.tsb))

    publishdf = pd.DataFrame()
    #logging.info(inst.df)

    inst.lock.acquire()
    logging.debug("""
    publish_candle: {}
    """.format(list(inst.df.columns)))

    try:
        if inst.df.empty is False: 
            logging.debug(run_type)
            candle_period = inst.candle_period
            mdf = makeCandle(inst.df, candle_period, inst.xch)
            logging.debug(mdf)
            inst.df = inst.df.iloc[0:0]
            if (len(inst.spilldf.index) > 0):
                logging.debug("###adding to spill df \n %s" % inst.spilldf)
                mdf.reset_index(inplace=True)
                logging.debug("mdf \n %s" % mdf)
                mdf = pd.concat([mdf, inst.spilldf], sort=True)
                logging.debug("after concat mdf \n %s" % mdf)
                mdf = makeSpillCandle(mdf, candle_period, inst.xch)
                inst.spilldf = inst.spilldf.iloc[0:0]
                logging.debug(mdf)

            mdf = mdf.dropna()    
            pmdf = mdf.copy(deep=True)
            p = candle_period/60
            logging.debug("candle_period ##### %d" % p)

            if run_type == 'candle':
                logging.debug("00000OOOOOOOO")
                # Write to candles database.
                '''
                now - 2p == timestamp
                now - p == timestamp
                now == timestamp
                '''
                mdf.reset_index(inplace=True)
                pmdf.reset_index(inplace=True)
                time_now = datetime.now()
                hr, mn = get_mkt_open_time(inst.xch) 
                mkt_open = time_now.replace(hour=hr, minute=mn, second=0, microsecond=0)
                hr, mn = get_mkt_close_time(inst.xch) 
                mkt_close = time_now.replace(hour=hr, minute=mn, second=0, microsecond=0)
                for i, row in mdf.iterrows():
                    time_now = datetime.now()
                    time_now = time_now.replace(second=0, microsecond=0)
                    logging.debug("##### %d" % p)
                    if (pd.to_datetime(time_now - dt.timedelta(minutes = (2*p))) == (pd.to_datetime(mdf.iloc[i]['Timestamp']))):
                        logging.debug("ignore... candle already published")
                        logging.debug(pmdf)
                        logging.debug("dropping row 0")
                        pmdf.drop(pmdf.index[[0]], inplace=True)
                        logging.debug(pmdf)
                    elif (pd.to_datetime(time_now - dt.timedelta(minutes = p)) == (pd.to_datetime(mdf.iloc[i]['Timestamp']))):
                        logging.debug("Write and Publish")
                        logging.debug(pmdf)
                        pmdf.set_index('Timestamp', drop=True, inplace=True)
                        publishdf = pmdf.head(1).copy(deep=True)
                        write_df_to_candle_db(inst, publishdf)
                        pmdf.reset_index(inplace=True)
                        pmdf.drop(pmdf.index[[0]], inplace=True)
                        logging.debug(publishdf)
                        logging.debug(pmdf)
                    elif (pd.to_datetime(time_now) == (pd.to_datetime(mdf.iloc[i]['Timestamp']))):
                        logging.debug("Black Sheep")
                        logging.debug(pmdf)
                        inst.spilldf = inst.spilldf.iloc[0:0]
                        logging.debug(inst.spilldf)
                        copydf = pmdf.head(1).copy(deep=True)
                        inst.spilldf = copydf.copy(deep=True)
                        pmdf.drop(pmdf.index[[0]], inplace=True)
                        logging.debug(copydf)
                        logging.debug(inst.spilldf)
                        logging.debug(pmdf)
                    elif (((pd.to_datetime(mdf.iloc[i]['Timestamp'])) <= mkt_close) and ((pd.to_datetime(mdf.iloc[i]['Timestamp'])) > mkt_open)):
                        logging.debug("Random candle before Mkt close: Write and Publish")
                        logging.debug(pmdf)
                        pmdf.set_index('Timestamp', drop=True, inplace=True)
                        publishdf = pmdf.head(1).copy(deep=True)
                        write_df_to_candle_db(inst, publishdf)
                        pmdf.drop(pmdf.index[[0]], inplace=True)
                        pmdf.reset_index(inplace=True)
                        logging.debug(publishdf)
                        logging.debug(pmdf)
                    elif ((pd.to_datetime(mdf.iloc[i]['Timestamp'])) < mkt_open):
                        logging.debug("Before Mkt open ..... ignore... ")
                        logging.debug(pmdf)
                        logging.debug("dropping row 0")
                        pmdf.drop(pmdf.index[[0]], inplace=True)
                        logging.debug(pmdf)
                    else:
                        print("******black swan******")
                        logging.debug("******black swan******")
                        logging.debug(pmdf)
                        pmdf.drop(pmdf.index[[0]], inplace=True)
                        logging.debug(pmdf)
                        print("pmdf: %s" % pmdf)
                        logging.debug("pmdf: %s" % pmdf)
                        print("mdf: %s" % mdf)
                        logging.debug("mdf: %s" % mdf)

            # Publish the candle
            if (len(publishdf.index) > 0):
                publishdf.reset_index(inplace=True)
                logging.debug("Publishing df inst : %s df: %s" % (inst.tsb, publishdf))
                Instrument_CP.publisher.sock_send(inst.tsb, publishdf.to_json(orient='records'))

    except KeyboardInterrupt:
        # except Exception as e:
        print("Exception #1")
        print(e)
        sys.exit(1)
    finally:
        inst.lock.release()
        print("[{}] Done publish for {} {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),\
                inst.tsb, run_type))


def worker_func(inst=None, s=0, run_type='publish'):
    """
    #spawn a thread
    logging.debug("Starting worker function for instrument %s" % (inst.tsb))
    t = threading.Thread(target=publish_candle, args=(inst, run_type))
    t.start()
    """
    # BLACKHOLING DETECTOR
    now = round(time.time() * 1000)
    delta = now - Instrument_CP.last_ticks_timestamp

    # Ideally we should pass xch as NSE, but I have subscribed to 
    # commodities only. Time is in ms
    logging.info("last_ticks_timestamp {} now {} delta {}"\
            .format(Instrument_CP.last_ticks_timestamp, now, delta))

    if (delta > 30000) \
            and (now > get_secs_since_epoch_at_mkt_open(xch='MCX')*1000) \
            and (now < get_secs_since_epoch_at_mkt_close(xch='MCX')*1000):
        # Restart ourselves.
        logging.error("TICKS BLACKHOLING DETECTED!!! RESTARTING..")
        spawn_ticks_collector()


    logging.debug("##########START################")
    publish_candle(inst, run_type)

    pre_publish = inst.pre_publish
    candle_period = inst.candle_period

    #publish_run_time = get_next_run_time(pre_publish, inst)
    candle_run_time = get_next_run_time(candle_period, inst)
    priority = 1

    if (candle_run_time == 0):
        logging.debug("Ticks for %s are done for the day.." % inst.tsb)
        return

    next_run_time = candle_run_time
    run_type = 'candle'

    if dry_run is False:
        if next_run_time > get_secs_to_mkt_close(inst.xch):
            logging.debug("Market closing before next run..")
            next_run_time = get_secs_to_mkt_close(inst.xch) + 2
            logging.debug("next_run_time : %d" % next_run_time)

    # Done schedule if next run time falls after market run.
    if (next_run_time > 0):
        #<= get_secs_to_mkt_close(inst.xch):
        logging.debug("[%s]next run time in secs: %d" % (inst, next_run_time))
        s.enter(next_run_time, priority, worker_func, kwargs={"inst": inst, \
                "s":s, "run_type":run_type})
    else:
        logging.debug("%s done for the day.." % inst.tsb)


def main():
    global dry_run

    parser = argparse.ArgumentParser("Candle  Publisher")
    parser.add_argument('--dry_run', action='store_true',
            help='Run in test mode...', required=False)

    args = vars(parser.parse_args())

    if args['dry_run'] is True:
        print("Dry run mode on..")
        dry_run = True
    else:
        print("REAL mode on..")
        dry_run = False

    ConfigFile = "../config/kuber.conf"
    config = configparser.ConfigParser()
    config.read(ConfigFile)
    log_dir = config['LOGGING CONFIGURATION']['log_dir']
    log_file = log_dir + '/candle_publisher.log'
    handler = RotatingFileHandler(log_file, maxBytes=2**20, backupCount=2)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug('Initializing...')

    global secs_since_epoch_at_mkt_open

    # secs_since_epoch_at_mkt_open = get_secs_since_epoch_at_mkt_open()
    # Initialize the Instrument_CP class.
    Instrument_CP.init()
    
    print("Instrument_CP INIT DONE....")
    for tsb in Instrument_CP.tradingsymbols:
        obj = Instrument_CP.get_obj(tsb)
    

    # One thread subscribes to ticks.
    t = threading.Thread(target=ticks_subscriber)
    t.start()

    """
    Now run a scheduler to Flush the ticks every publish seconds.
    And write the candles to db every 1 min.
    Our schedule should sync with this time
    and not the time when we start the process.
    """
    s = sched.scheduler(time.time, time.sleep)
    try:
        """
        For each instrument in inst_conf_dict,
        There are two important parameters:-
        a) candle_period:- We need to generate ohlc data
        periodically in this time frame.
        b) Reschedule it to run again.
        """
        for inst in Instrument_CP.instrument_symbol_to_obj_map.values():
            """
            1) Publish an ohlc candle immediately
            2) Schedule next run.
            """
            worker_func(inst=inst, s=s, run_type='candle')

        """ Schedule jobs to run. """
        s.run()
    except KeyboardInterrupt as e:
        # except Exception as e:
        print ("Exception in main thread: ")
        print(e)
        print("Cancelling all scheduled event.")
        for ev in s.queue:
            s.cancel(ev)

def spawn_ticks_collector():
    try:
        cmd = ['bash', 'ticks_start']
        os.execvp(cmd[0], cmd)
    except Exception as e:
        print("Failed to spawn ticks_start: {}".format(e))
        sys.exit(0)

if __name__ == '__main__':
    main()
