#!/Users/ansuman/Github/Projects/python/virtualenv/bin/python

import sys
sys.path.append('../config')
sys.path.append('../execution_engine')
from ConfigurationClass import Configuration as cf
import ssl
import configparser
import pandas as pd
import sqlite3
import argparse
import json
import pandas
import requests
from io import StringIO
import prettytable
from fake_useragent import UserAgent
import io
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import logging

# Disable the warning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

ssl._create_default_https_context = ssl._create_unverified_context
ConfigFile = "../configuration/kuber.conf"

InstrumentsDB = "../db/instruments.db"

def df_print(df, columns):
    output = StringIO()
    df[columns].to_csv(output)
    output.seek(0)
    pt = prettytable.from_csv(output)
    print(pt)

def get_ohlc_of_tsb(tsb, segment):
    instruments = ["{}:{}".format(segment, tsb)]

    c = cf()
    kite = c.get_kite_obj()

    try:
        ohlc = kite.ohlc(instruments)
        return ohlc
    except Exception as e:
        print('get_ohlc_of_tsb(): {}'.format(e))
        return None

def get_mcx_symbols():
    c = cf()
    iDB = c.iDB
    symbol_list = list()

    sql = "SELECT * FROM instruments WHERE Segment LIKE 'MCX'"
    with sqlite3.connect(iDB) as conn:
        try:
            df = pd.read_sql_query(sql=sql, con=conn, index_col='index')
            if df.empty is True:
                return None
            return df

        except Exception as e:
            print(e)
            return None

def query_symbols_by_index(index):
    """
    Get the symbols from the index.
    Index: -
        nifty50
        niftyBank
        niftyPSUBank
    """
    c = cf()
    iDB = c.iDB
    symbol_list = list()

    sql = "SELECT Symbol FROM {}".format(index)
    with sqlite3.connect(iDB) as conn:
        try:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()

            for row in rows:
                symbol_list.append(row[0])

        except Exception as e:
            print(e)
            return None

    return symbol_list

def get_subscription_list_tokens():
    i_list = list()
    c = cf()
    nifty50_list = query_symbols_by_index('nifty50')
    bankNifty_list = query_symbols_by_index('niftyBank')
    tsb_list = c.tradingsymbols_list
    tsb_list = list(set(tsb_list + nifty50_list + bankNifty_list))
    tsb_list = list(set(nifty50_list + bankNifty_list))

    for tsb in tsb_list:
        token = query_token_by_tradingsymbol(tsb)
        if token:
            i_list.append(int(token))

    return i_list

def get_subscription_list():
    c = cf()
    nifty50_list = query_symbols_by_index('nifty50')
    bankNifty_list = query_symbols_by_index('niftyBank')
    tsb_list = c.tradingsymbols_list
    tsb_list = list(set(tsb_list + nifty50_list + bankNifty_list))

    return tsb_list

def query_db_otm(itm, price, ity):
    """
    Get in the money options.
    """

    if ity == 'CE':
        op = '>='
        acc = True
    else:
        op = '<='
        acc = False
    # First get closest in the money CE
    sql = """
          SELECT * FROM instruments WHERE tradingsymbol LIKE '%%%s%%'
          AND segment='NFO-OPT'
          AND strike%s%s
          AND instrument_type='%s'
          """ % (itm, op, price, ity)

    with sqlite3.connect(InstrumentsDB) as conn:
        try:
            df = pd.read_sql_query(sql=sql, con=conn, index_col='index')
            df.sort_values(by='strike', inplace=True, ascending=acc)
            # return df.head(n=6).to_json(orient='records')
            return df.to_json(orient='records')
        except Exception as e:
            print(e)
    return None

def query_db_itm(itm, price, ity):
    """
    Get in the money options.
    """

    if ity == 'CE':
        op = '<='
        acc = False
    else:
        op = '>='
        acc = True
    # First get closest in the money CE
    sql = """
          SELECT * FROM instruments WHERE tradingsymbol LIKE '%%%s%%'
          AND segment='NFO-OPT'
          AND strike%s%s
          AND instrument_type='%s'
          """ % (itm, op, price, ity)

    with sqlite3.connect(InstrumentsDB) as conn:
        try:
            df = pd.read_sql_query(sql=sql, con=conn, index_col='index')
            df.sort_values(by='strike', inplace=True, ascending=acc)
            return df.head(n=6).to_json(orient='records')
        except Exception as e:
            print(e)
    return None


def query_db_by_sql(query):
    """
    Query by instrument token.
    """

    with sqlite3.connect(InstrumentsDB) as conn:
        try:
            df = pd.read_sql_query(sql=query, con=conn, index_col='index')
            if df.empty is True:
                return None
            return df.to_json(orient='records')
        except Exception as e:
            print(e)
            return None


def query_db_by_string(trade_symbol):
    """
    Query by instrument trade_symbol.
    """

    sql = """
    SELECT * FROM instruments WHERE tradingsymbol LIKE '%%%s%%'
    """ % (trade_symbol)

    with sqlite3.connect(InstrumentsDB) as conn:
        try:
            df = pd.read_sql_query(sql=sql, con=conn, index_col='index')
            return df.to_json(orient='records')
        except Exception as e:
            print(e)
            return None


def query_db_by_token(token):
    """
    Query by instrument token.
    """

    sql = """
    SELECT * FROM instruments WHERE instrument_token='%s'
    """ % (token)

    with sqlite3.connect(InstrumentsDB) as conn:
        try:
            df = pd.read_sql_query(sql=sql, con=conn, index_col='index')
            return df.to_json(orient='records')
        except Exception as e:
            print(e)
            return None


def query_token_by_tradingsymbol(tsb):
    """
    tsb = trading symbol
    Return:
        instrument_token
    """

    sql = """
    SELECT instrument_token FROM instruments WHERE tradingsymbol='%s'
    """ % (tsb)

    with sqlite3.connect(InstrumentsDB) as conn:
        try:
            df = pd.read_sql_query(sql=sql, con=conn)
            if df.empty == False:
                return df.instrument_token[0]
        except Exception as e:
            print(e)

    return None


def query_token_to_trade_symbol(token):
    """
    Query by instrument token.
    """

    sql = """
    SELECT tradingsymbol FROM instruments WHERE instrument_token='%s'
    """ % (token)

    with sqlite3.connect(InstrumentsDB) as conn:
        try:
            df = pd.read_sql_query(sql=sql, con=conn)
            return df.tradingsymbol[0]
        except Exception as e:
            print(e)
            return None


def query_db_by_scrip(scrip):
    """
    Query instrument db.
    Schema:
    CREATE TABLE "instruments" (
        "index" INTEGER,
        "exchange" TEXT,
        "exchange_token" TEXT,
        "expiry" TEXT,
        "instrument_token" TEXT,
        "instrument_type" TEXT,
        "last_price" REAL,
        "lot_size" INTEGER,
        "name" TEXT,
        "segment" TEXT,
        "strike" REAL,
        "tick_size" REAL,
        "tradingsymbol" TEXT
    );
    """
    query_str = """
    SELECT * FROM instruments WHERE tradingsymbol='%s'
    """ % (scrip)

    with sqlite3.connect(InstrumentsDB) as conn:
        try:
            df = pd.read_sql_query(sql=query_str, con=conn, index_col='index')
            if df.empty is False:
                return df.to_json(orient='records')
        except Exception as e:
            print(e)
        return None


def create_indices_db():
    """
    Fetch the data from nseindia.com
    Create a table for each index.
    """
    indices = dict()
    # Add the list of indices for which we want to store data
    indices['nifty50'] = 'https://www.nseindia.com/content/indices/ind_nifty50list.csv'
    indices['niftyBank'] = 'https://www.nseindia.com/content/indices/ind_niftybanklist.csv'
    indices['niftyPSUBank'] = 'https://www.nseindia.com/content/indices/ind_niftypsubanklist.csv'

    c = cf()
    iDB = c.iDB

    with requests.Session() as s:
        ua = UserAgent()
        s.headers.update({'User-Agent': ua.firefox})

        for table, url in indices.items():
            try:
                resp = s.get(url)
            except Exception as e:
                print(e)
                sys.exit(1)

            try:
                df = pd.read_csv(io.StringIO(resp.text))
            except Exception as e:
                print(e)
                sys.exit(1)

            try:
                conn = sqlite3.connect(iDB)
                # Write dataframe into DB.
                df.to_sql(name=table, con=conn, if_exists='replace')
                conn.commit()
                conn.close()
            except Exception as e:
                print(e)
                sys.exit(1)

            logging.info("Updated {} table in {}".format(table, iDB))

def create_instruments_db():
    config = configparser.ConfigParser()
    config.read(ConfigFile)

    c = cf()
    # api_key = c.api_key
    # api_secret = c.api_secret
    InstrumentsDB = c.iDB

    try:
        # kite = KiteConnect(api_key, api_secret)
        kite = c.get_kite_obj()
    except Exception as e:
        print(e)
        sys.exit(1)

    instruments = kite.instruments()
    df = pd.DataFrame(instruments)

    """
    Create a sqlite database.
    """
    try:
        conn = sqlite3.connect(InstrumentsDB)

        """
        Write the dataframe to sqlite db
        """
        df.to_sql(name="instruments", con=conn, if_exists="replace")
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)
        sys.exit(1)

    logging.info("Updated instruments database.")


def main():
    logging.basicConfig(level=logging.DEBUG,
            filename='../logs/instruments.log',
            format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser("Update/Query the instruments.db")
    parser.add_argument('-u', '--update', action='store_true',
            help='Update the instruments database.')
    parser.add_argument('--update_indices', action='store_true',
            help='Update the indices in database.')
    parser.add_argument('--get_symbols_of_index',
            help='[nifty50 | niftyBank | niftyPSUBank]')
    parser.add_argument('-s', '--scrip',
            help='Query the instruments database.')
    parser.add_argument('-t', '--token',
            help='instrument to be queried.')
    parser.add_argument('-r', '--string',
            help='regular expression search')

    parser.add_argument('--mcx',
            help='--mcx <str>. Ex get everything:- python3 instruments.py --mcx ".*"')
    """
    A few example queries:-
    python3 instruments.py --mcx "SILVERM.*APR"
    python3 instruments.py --mcx "SILVER"
    python3 instruments.py --mcx ".*"
    """

    parser.add_argument('-q', '--query',
            help='sql query.')
    """
    python3 instruments.py -q 'SELECT * FROM instruments WHERE tradingsymbol LIKE "%BANK%" AND instrument_type != "CE" AND instrument_type != "PE"'
    """

    """
    Arguments related to options
    """
    parser.add_argument('-i', '--itm',
            help='Get nearest in the money options.\
                    Ex: python3 ./instruments.py --itm BANKNIFTY -p 24000')
    parser.add_argument('-o', '--otm',
            help='Get nearest in the money options.\
                    Ex: python3 ./instruments.py --otm BANKNIFTY -p 24000')
    parser.add_argument('--expiry',
            help='(near|next|far)\
                    Ex: python3 ./instruments.py --otm BANKNIFTY -p 24000 --expiry near')


    parser.add_argument('-n', '--indices', action='store_true', help='Get indices')
    parser.add_argument('-f', '--futures',
            help='Get Futures. Ex. -f MAR for march futures')
    parser.add_argument('-p', '--price',
            help='Current Market price.')
    parser.add_argument('-g', '--segment',
            help='NSE/BSE/NFO-OPT/BFO-OPT')
    parser.add_argument('-y', '--type',
            help='EQ/FUT/CE/PE')

    args = vars(parser.parse_args())

    if args['mcx']:
        mcx_df = get_mcx_symbols()

        if mcx_df is not None:
            """
            {'instrument_token': 53687303, 'exchange_token': '209716',
            'tradingsymbol': 'SILVER18DECFUT', 'name': 'Silver', 'last_price':
            0.0, 'expiry': '2018-12-05', 'strike': 0.0, 'tick_size': 1.0,
            'lot_size': 1, 'instrument_type': 'FUT', 'segment': 'MCX',
            'exchange': 'MCX'}
            """
            mcx_filter_df = mcx_df[mcx_df['tradingsymbol'].str.contains(args['mcx'])]
            df_print(mcx_filter_df, ['tradingsymbol', 'name', 'last_price', 'expiry', 'tick_size' ])
        else:
            print("Query returned None.")

        sys.exit(0)


    if args['futures']:
        query = 'SELECT * FROM instruments WHERE ( segment="NFO-FUT"\
                OR segment="BFO-FUT" ) AND tradingsymbol LIKE "%{}%"'\
                .format(args['futures'])

        print(query)

        try:
            data = json.loads(query_db_by_sql(query))
        except Exception as e:
            print("Query Failed: {}".format(e))
            sys.exit(0)

        df = pd.DataFrame(data)
        df.set_index('instrument_token', inplace=True)
        """
        Pandas(Index='219699973', exchange='BFO', exchange_token='858203',\
        expiry='2018-03-28', instrument_type='FUT', last_price=0.0,\
        lot_size=3500, name='', segment='BFO-FUT', strike=0.0,\
        tick_size=0.05, tradingsymbol='HNDL18MARFUT')
        """
        df.sort_values(by=['lot_size'], axis='index', ascending=False,
                inplace=True, kind='quicksort', na_position='last' )
        columns = ('Instrument Token', 'Trading Symbol', 'lot_size')
        print('{0:20} {1:30} {2:40}'.format(*columns))
        for row in df.itertuples():
            # print(row)
            # justification: < left ^ middle > right
            print('{0:20} {1:30} {2:<40}'.format(row[0], row[-1], row[-6]))
        sys.exit(0)

    if args['indices']:
        query = 'SELECT * FROM instruments WHERE segment="NSE-INDICES"'
        try:
            data = json.loads(query_db_by_sql(query))
        except Exception as e:
            print("Query Failed: {}".format(e))
            sys.exit(0)

        df = pd.DataFrame(data)
        df.set_index('instrument_token', inplace=True)
        # print(df[['exchange', 'instrument_type', 'name']])
        """
        Pandas(Index='260105', exchange='NSE', exchange_token='1016',\
                expiry='', instrument_type='EQ', last_price=0.0, lot_size=0,\
                name='NIFTY BANK', segment='NSE-INDICES', strike=0.0,\
                tick_size=0.0, tradingsymbol='NIFTY BANK')
        """
        columns = ('Instrument Token', 'Name', 'Trading Symbol')
        print('{0:20} {1:30} {2:40}'.format(*columns))
        for row in df.itertuples():
            print('{0:20} {1:30} {2:40}'.format(row[0], row[7], row[-1]))
        sys.exit(0)

    if args['scrip']:
        result = query_db_by_scrip(args['scrip'])

        if result is not None:
            data = json.loads(result)
            print(data)
            """
            df = pd.DataFrame(data)
            df.set_index('instrument_token', inplace=True)
            print(df[['exchange', 'instrument_type', 'name']])
            """
            sys.exit(0)
        else:
            print("No entry found in the database for the symbol")

    if args['token']:
        data = json.loads(query_db_by_token(args['token']))
        df = pd.DataFrame(data)
        df.set_index('instrument_token', inplace=True)
        print(df[['exchange', 'tradingsymbol', 'name']])
        sys.exit(0)

    if args['string']:
        sql = """
        SELECT * FROM instruments WHERE tradingsymbol LIKE '%{}%' \
                AND tradingsymbol NOT LIKE '%-BE%' \
                AND tradingsymbol NOT LIKE '%-BL%'
        """.format(args['string'])

        if args['segment']:
            sql += ' AND Segment="{}"'.format(args['segment'])

        if args['type']:
            sql += ' AND instrument_type="{}"'.format(args['type'])

        # print(sql)

        try:
            d = query_db_by_sql(sql)
            if d is not None:
                data = json.loads(d)
            else:
                print("No results for the query {}".format(sql))
                sys.exit(0)
        except Exception as e:
            print("Query Failed: {}".format(e))
            sys.exit(0)

        # data = json.loads(query_db_by_string(args['string']))
        df = pd.DataFrame(data)
        df.set_index('instrument_token', inplace=True)
        # print(df[['exchange', 'tradingsymbol', 'name']])
        columns = ('Instrument Token', 'Trading Symbol', 'Type','Segment')
        print('{0:^20} {1:30} {2:5} {3:5}'.format(*columns))
        for row in df.itertuples():
            print('{0:^20} {1:30} {2:5} {3:5}'.format(row[0], row[-1], row[4], row[-4]))
        sys.exit(0)

    if args['query']:
        try:
            data = json.loads(query_db_by_sql(args['query']))
        except Exception as e:
            print("Query Failed: {}".format(e))
            sys.exit(0)

            df = pd.DataFrame(data)
            df.set_index('instrument_token', inplace=True)
            # print(df[['exchange', 'instrument_type', 'name']])
            for row in df.itertuples():
                print(row)
            sys.exit(0)

    if args['itm']:
        if args['price']:
            data = json.loads(query_db_itm(args['itm'], args['price'], 'CE'))
            df = pd.DataFrame(data)
            df.set_index('instrument_token', inplace=True)
            print(df[['exchange', 'tradingsymbol', 'name']])

            data = json.loads(query_db_itm(args['itm'], args['price'], 'PE'))
            df = pd.DataFrame(data)
            df.set_index('instrument_token', inplace=True)
            print(df[['exchange', 'tradingsymbol', 'name']])
            sys.exit(0)

    if args['otm']:
        if args['price']:
            data = json.loads(query_db_otm(args['otm'], args['price'], 'CE'))
            df_ce = pd.DataFrame(data)
            df_ce.set_index('strike', inplace=True)

            data = json.loads(query_db_otm(args['otm'], args['price'], 'PE'))
            df_pe = pd.DataFrame(data)
            df_pe.set_index('strike', inplace=True)

            df = pd.concat([df_ce, df_pe], join='outer')
            # df.set_index('tradingsymbol', inplace=True)

            df_print(df, ['tradingsymbol', 'expiry', 'last_price'])
            sys.exit(0)

            if args["expiry"]:
                """
                ### Filter the output based on expiry dates.
                """
                if args["expiry"] is "near":
                    pass
                if args["expiry"] is "near":
                    pass
                if args["expiry"] is "near":
                    pass

            """
            Index(['exchange', 'exchange_token', 'expiry', 'instrument_type', 'last_price',
                   'lot_size', 'name', 'segment', 'strike', 'tick_size', 'tradingsymbol'],
                         dtype='object')
            """
            print("***** {} *****".format(args['otm']))
            df_print(df, ['tradingsymbol', 'expiry', 'strike', 'last_price'])
            sys.exit(0)

    if args['update']:
        create_instruments_db()
        sys.exit(0)

    if args['update_indices']:
        create_indices_db()
        sys.exit(0)

    if args['get_symbols_of_index']:
        symbol_list = query_symbols_by_index(args['get_symbols_of_index'])
        print(type(symbol_list))
        print(symbol_list)


if __name__ == '__main__':
    main()
