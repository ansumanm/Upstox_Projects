import sys
import time
from influxdb import InfluxDBClient
from collections import namedtuple

f = open('tradebot.log', 'r')

Instrument = namedtuple('Instrument', ['exchange', 'token', 'parent_token',
        'symbol', 'name', 'closing_price', 'expiry', 'strike_price', 'tick_size',
            'lot_size', 'instrument_type', 'isin'])

client = InfluxDBClient(host='localhost', port=8086)

# Create Ticks database
# client.create_database('ticks')

print(client.get_list_database())

for x in f:
    # publisher.sock_send('quote', x)
    data = eval(x)

    # Prepare influxdb entry
    """
{'timestamp': '1570096800000', 'exchange': 'NSE_FO', 'symbol': 'BANKNIFTY19O0330000CE', 'ltp': 0.05, 'close': 24.55, 'open': 7.55, 'high': 20.0, 'low': 0.05, 'vtt': 21571740.0, 'atp': 3.62, 'oi': 827820.0, 'spot_price': 28418.5, 'total_buy_qty': 21700, 'total_sell_qty': 226020, 'lower_circuit': 0.05, 'upper_circuit': 146.0, 'yearly_low': None, 'ltt': 1570096798000, 'bids': [{'quantity': 21700, 'price': 0.05, 'orders': 20}, {'quantity': 0, 'price': 0.0, 'orders': 0}, {'quantity': 0, 'price': 0.0, 'orders': 0}, {'quantity': 0, 'price': 0.0, 'orders': 0}, {'quantity': 0, 'price': 0.0, 'orders': 0}], 'asks': [{'quantity': 33560, 'price': 0.1, 'orders': 24}, {'quantity': 3100, 'price': 0.15, 'orders': 2}, {'quantity': 10600, 'price': 0.2, 'orders': 9}, {'quantity': 7620, 'price': 0.25, 'orders': 5}, {'quantity': 20, 'price': 0.3, 'orders': 1}], 'instrument': Instrument(exchange='NSE_FO', token=40527, parent_token=26009, symbol='banknifty19o0330000ce', name='', closing_price=24.55, expiry='1570041000000', strike_price=30000.0, tick_size=5.0, lot_size=20, instrument_type='OPTIDX', isin=None)}
    """
    point = {
            "measurement": "FeedFull",
            "tags" : {
                'exchange': data['instrument'].exchange,
                'symbol': data['instrument'].symbol,
                'token': data['instrument'].token,
                'parent_token': data['instrument'].parent_token,
                'name': data['instrument'].name,
                'expiry': data['instrument'].expiry,
                'strike_price': data['instrument'].strike_price,
                'tick_size': data['instrument'].tick_size,
                'lot_size': data['instrument'].lot_size,
                'instrument_type': data['instrument'].instrument_type,
                'isin': data['instrument'].isin,
                },
            "time": data['ltt'],
            "fields": {
                "ltp": data['ltp'],
                "close": data['close'],
                "open": data['open'],
                "high": data['high'],
                "low": data['low'],
                "vtt": data['vtt'],
                "atp": data['atp'],
                "oi": data['oi'],
                "spot_price": data['spot_price'],
                "total_buy_qty": data['total_buy_qty'],
                "total_sell_qty": data['total_sell_qty'],
                "lower_circuit": data['lower_circuit'],
                "upper_circuit": data['upper_circuit'],
                "yearly_low": data['yearly_low'],
                "bids_0_quantity": data['bids'][0]['quantity'],
                "bids_1_quantity": data['bids'][1]['quantity'],
                "bids_2_quantity": data['bids'][2]['quantity'],
                "bids_3_quantity": data['bids'][3]['quantity'],
                "bids_4_quantity": data['bids'][4]['quantity'],
                "bids_0_price": data['bids'][0]['price'],
                "bids_1_price": data['bids'][1]['price'],
                "bids_2_price": data['bids'][2]['price'],
                "bids_3_price": data['bids'][3]['price'],
                "bids_4_price": data['bids'][4]['price'],
                "bids_0_orders": data['bids'][0]['orders'],
                "bids_1_orders": data['bids'][1]['orders'],
                "bids_2_orders": data['bids'][2]['orders'],
                "bids_3_orders": data['bids'][3]['orders'],
                "bids_4_orders": data['bids'][4]['orders'],
                "asks_0_quantity": data['asks'][0]['quantity'],
                "asks_1_quantity": data['asks'][1]['quantity'],
                "asks_2_quantity": data['asks'][2]['quantity'],
                "asks_3_quantity": data['asks'][3]['quantity'],
                "asks_4_quantity": data['asks'][4]['quantity'],
                "asks_0_price": data['asks'][0]['price'],
                "asks_1_price": data['asks'][1]['price'],
                "asks_2_price": data['asks'][2]['price'],
                "asks_3_price": data['asks'][3]['price'],
                "asks_4_price": data['asks'][4]['price'],
                "asks_0_orders": data['asks'][0]['orders'],
                "asks_1_orders": data['asks'][1]['orders'],
                "asks_2_orders": data['asks'][2]['orders'],
                "asks_3_orders": data['asks'][3]['orders'],
                "asks_4_orders": data['asks'][4]['orders'],
                }
            }

    print(point)

    client.write_points([point], database='ticks')
    print("Wrote 1 point")
    time.sleep(2)
