import copy
import argparse
from upstox_api.api import *
from datetime import datetime
from pprint import pprint
import os, sys
import time
from tempfile import gettempdir
import logging
from logging.config import fileConfig
import pickle
import requests
import signal

from influxdb_client import Point, InfluxDBClient, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from influx_line_protocol import Metric, MetricCollection

u = None
s = None

upstox_settings = dict()
influx_cloud_url = 'https://us-west-2-1.aws.cloud2.influxdata.com'
influx_cloud_token = 'vxdOLg2pfVu1lBzo_kovCNPGlnBeN8NsYa6XJYYOfa3vrjZ4lRsxuwI3uCAZSfm9In102YzZYe-KlrFeK6guxg=='
bucket = 'ticksB'
org = 'ansuman.mohanty@gmail.com'

"""
https://github.com/influxdata/influxdb-client-python
"""

try:
    client = InfluxDBClient(url=influx_cloud_url, token=influx_cloud_token)
except Exception as e:
    print("Could not create client: {}".format(str(e)))
    sys.exit(0)

try:
    # write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api = client.write_api(write_options=WriteOptions(batch_size=500,
        flush_interval=10000, # the number of milliseconds before the batch is written
        jitter_interval=2000, # the number of milliseconds to increase the batch flush interval by a random amount
        retry_interval=5000)) # the number of milliseconds to retry unsuccessful write. The retry interval is used when the InfluxDB server does not specify "Retry-After" header.
except Exception as e:
    print("Could not create write API: {}".format(str(e)))
    sys.exit(0)

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

def my_on_order_update_handler (event):
    msg = """
    symbol: {}
    quantity: {}
    transaction_type: {}
    order_type: {}
    price: {}
    trigger_price: {}
    exchange: {}
    status: {}
    message: {}
    """.format(event['symbol'], event['quantity'], \
            event['transaction_type'], event['order_type'], \
            event['price'], event['trigger_price'], \
            event['exchange'], event['status'], event['message'])

    logging.critical(msg)
    # telegram_handler(event, "on_order_update")

def my_on_trade_update_handler (event):
    msg = """
    symbol: {}
    traded_quantity: {}
    transaction_type: {}
    order_type: {}
    traded_price: {}
    exchange: {}
    """.format(event['symbol'], event['traded_quantity'], \
            event['transaction_type'], event['order_type'], \
            event['traded_price'], \
            event['exchange'])

    logging.critical(msg)
    # telegram_handler(event, "on_trade_update")

def my_on_quote_update_handler (event):
    logging.info("%s" % str(event))

    try:
        data = eval(str(event))
    except Exception as e:
        print("Error: {}".format(str(e)))
        return

    # "time": datetime.fromtimestamp(data['ltt']/1000).isoformat('T'),
    try:
        collection = MetricCollection()
        metric = Metric('FeedFull')

        metric.add_tag('exchange', data['instrument'].exchange)
        metric.add_tag('symbol', data['instrument'].symbol)
        metric.add_tag('token', data['instrument'].token)
        metric.add_tag('parent_token', data['instrument'].parent_token)

        if data['instrument'].name:
            metric.add_tag('name', data['instrument'].name)

        metric.add_tag('expiry', data['instrument'].expiry)
        metric.add_tag('strike_price', data['instrument'].strike_price)
        metric.add_tag('tick_size', data['instrument'].tick_size)
        metric.add_tag('lot_size', data['instrument'].lot_size)
        metric.add_tag('instrument_type', data['instrument'].instrument_type)
        metric.add_tag('isin', data['instrument'].isin)

        metric.add_value( "ltp", data['ltp'])
        metric.add_value( "close", data['close'])
        metric.add_value("open", data['open'])
        metric.add_value("high", data['high'])
        metric.add_value("low", data['low'])
        metric.add_value("vtt", data['vtt'])
        metric.add_value("atp", data['atp'])
        metric.add_value("oi", data['oi'])
        metric.add_value("spot_price", data['spot_price'])
        metric.add_value("total_buy_qty", data['total_buy_qty'])
        metric.add_value("total_sell_qty", data['total_sell_qty'])
        metric.add_value("lower_circuit", data['lower_circuit'])
        metric.add_value("upper_circuit", data['upper_circuit'])
        metric.add_value("yearly_low", data['yearly_low'])
        metric.add_value("bids_0_quantity", data['bids'][0]['quantity'])
        metric.add_value("bids_1_quantity", data['bids'][1]['quantity'])
        metric.add_value("bids_2_quantity", data['bids'][2]['quantity'])
        metric.add_value("bids_3_quantity", data['bids'][3]['quantity'])
        metric.add_value("bids_4_quantity", data['bids'][4]['quantity'])
        metric.add_value("bids_0_price", data['bids'][0]['price'])
        metric.add_value("bids_1_price", data['bids'][1]['price'])
        metric.add_value("bids_2_price", data['bids'][2]['price'])
        metric.add_value("bids_3_price", data['bids'][3]['price'])
        metric.add_value("bids_4_price", data['bids'][4]['price'])
        metric.add_value("bids_0_orders", data['bids'][0]['orders'])
        metric.add_value("bids_1_orders", data['bids'][1]['orders'])
        metric.add_value("bids_2_orders", data['bids'][2]['orders'])
        metric.add_value("bids_3_orders", data['bids'][3]['orders'])
        metric.add_value("bids_4_orders", data['bids'][4]['orders'])
        metric.add_value("asks_0_quantity", data['asks'][0]['quantity'])
        metric.add_value("asks_1_quantity", data['asks'][1]['quantity'])
        metric.add_value("asks_2_quantity", data['asks'][2]['quantity'])
        metric.add_value("asks_3_quantity", data['asks'][3]['quantity'])
        metric.add_value("asks_4_quantity", data['asks'][4]['quantity'])
        metric.add_value("asks_0_price", data['asks'][0]['price'])
        metric.add_value("asks_1_price", data['asks'][1]['price'])
        metric.add_value("asks_2_price", data['asks'][2]['price'])
        metric.add_value("asks_3_price", data['asks'][3]['price'])
        metric.add_value("asks_4_price", data['asks'][4]['price'])
        metric.add_value("asks_0_orders", data['asks'][0]['orders'])
        metric.add_value("asks_1_orders", data['asks'][1]['orders'])
        metric.add_value("asks_2_orders", data['asks'][2]['orders'])
        metric.add_value("asks_3_orders", data['asks'][3]['orders'])
        metric.add_value("asks_4_orders", data['asks'][4]['orders'])

        metric.with_timestamp(data['ltt'])
        collection.append(metric)

    except Exception as e:
        print("Point error: {}".format(str(e)))

    try:
        # curl -XPOST "http://localhost:9999/api/v2/write?org=YOUR_ORG&bucket=YOUR_BUCKET&precision=s" \
        # --header "Authorization: Token YOURAUTHTOKEN" \
        # --data-raw "mem,host=host1 used_percent=23.43234543 1556896326" 
        write_api.write(bucket=bucket, org=org, record=str(collection), write_precision='ms')
        print("Wrote one point...")
    except Exception as e:
        print("write_points error:[{}] {}".format(e.__class__.__name__, str(e)))
        # client.create_database('ticks')
        sys.exit(0)
    

def my_on_disconnect_handler (event):
    my_generic_event_handler(event, "on_disconnect")

def my_on_error_handler (ws, event):
    print("Error: {}".format(event))

def my_generic_event_handler (event):
    print ("%s" % str(event))


def signal_handler(sig, frame):
    print('sig {} frame {}'.format(sig, frame))

    print("Closing client...")
    write_api.__del__()
    client.__del__()

    print("Clean Exit...")
    sys.exit(0)


def main():
    # parser = argparse.ArgumentParser("Instrument subscribe")
    # parser.add_argument('-s', '--str',help='instrument to subscribe')
    # args = vars(parser.parse_args())
    # inst_str = args['str']
    # logging.basicConfig(filename="tradebot_ws.log", level=logging.DEBUG)
    fileConfig('logging_config.ini')
    global publisher

    u = load_from_file('upstox.pickle')
    u.get_master_contract('MCX_FO') # get contracts for MCX FO
    u.get_master_contract('NSE_EQ')
    u.get_master_contract('BSE_EQ')
    u.get_master_contract('NSE_FO')

    u.set_on_order_update (my_generic_event_handler)
    u.set_on_quote_update (my_on_quote_update_handler)

    """
    try:
        u.subscribe(u.get_instrument_by_symbol('MCX_FO', inst_str), LiveFeedType.Full)
    except Exception as e:
        print("Could not subscribe: {}".format(e))
    """
    print("""
            Starting websocket...
            """)

    u.start_websocket(False)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
