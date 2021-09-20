from collections import namedtuple

Instrument = namedtuple('Instrument', ['exchange', 'token', 'parent_token',
    'symbol', 'name', 'closing_price', 'expiry', 'strike_price', 'tick_size',
    'lot_size', 'instrument_type', 'isin'])

tick_str = """{'timestamp': '1567155949000', 'exchange': 'NSE_FO', 'symbol': 'BANKNIFTY19SEPFUT', 'ltp': 27454.0, 'close': 27435.2, 'open': 27501.15, 'high': 27686.0, 'low': 27151.5, 'vtt': 3908960.0, 'atp': 27421.18, 'oi': 1738320.0, 'spot_price': 27352.7, 'total_buy_qty': 211240, 'total_sell_qty': 511740, 'lower_circuit': 24691.7, 'upper_circuit': 30178.75, 'yearly_low': None, 'ltt': 1567155948000, 'bids': [{'quantity': 40, 'price': 27454.15, 'orders': 1}, {'quantity': 20, 'price': 27454.1, 'orders': 1}, {'quantity': 40, 'price': 27453.0, 'orders': 1}, {'quantity': 80, 'price': 27452.6, 'orders': 1}, {'quantity': 200, 'price': 27452.1, 'orders': 1}], 'asks': [{'quantity': 60, 'price': 27459.75, 'orders': 1}, {'quantity': 20, 'price': 27459.8, 'orders': 1}, {'quantity': 80, 'price': 27459.95, 'orders': 2}, {'quantity': 60, 'price': 27460.0, 'orders': 2}, {'quantity': 40, 'price': 27460.05, 'orders': 1}], 'instrument': Instrument(exchange='NSE_FO', token=44460, parent_token=26009, symbol='banknifty19sepfut', name='', closing_price=27435.2, expiry='1569436200000', strike_price=None, tick_size=5.0, lot_size=20, instrument_type='FUTIDX', isin=None)}"""

try:
    tick_data = eval(tick_str)
    print(type(tick_data))
    print((tick_data))
except Exception as e:
    print(str(e))

