"""
event = {'quantity': 2000, 'exchange_order_id': '', 'order_type': 'L',
        'status': 'after market order req received', 'transaction_type': 'S',
        'exchange': 'NSE_FO', 'trigger_price': 0.0, 'symbol': 'ARVIND18OCTFUT',
        'traded_quantity': 0, 'is_amo': True, 'product': 'D',
        'order_request_id': '1', 'duration': None, 'price': 312.3,
        'time_in_micr o': '1539105046531842', 'parent_order_id': 'NA',
        'order_id': '181009000252547', 'message': '', 'exchange_time': '',
        'disclosed_qua ntity': 0, 'token': 48729, 'average_price': 0.0,
        'instrument': Instrument(exchange='NSE_FO', token=48729,
            parent_token=193, symbol ='arvind18octfut', name='',
            closing_price=302.5, expiry='1540405800000', strike_price=None,
            tick_size=5.0, lot_size=2000, instrument_type='FUTSTK', isin=None)}
"""
event = {'quantity': 2000, 'exchange_order_id': '', 'order_type': 'L',
        'status': 'after market order req received', 'transaction_type': 'S',
        'exchange': 'NSE_FO', 'trigger_price': 0.0, 'symbol': 'ARVIND18OCTFUT',
        'traded_quantity': 0, 'is_amo': True, 'product': 'D',
        'order_request_id': '1', 'duration': None, 'price': 312.3,
        'time_in_micr o': '1539105046531842', 'parent_order_id': 'NA',
        'order_id': '181009000252547', 'message': '', 'exchange_time': '',
        'disclosed_qua ntity': 0, 'token': 48729, 'average_price': 0.0}

print(type(event))
print(event['symbol'])
print(event['quantity'])
print(event['exchange'])
print(event['transaction_type'])
print(event['order_type'])
print(event['trigger_price'])
print(event['status'])
print(event['message'])
