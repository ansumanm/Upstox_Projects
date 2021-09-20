#!/usr/bin/env python3
import sys
import zmq
import signal
import pickle
from upstox_api.api import *
from transitions import Machine
import threading
import logging
import argparse
from cmd2 import Cmd
import socket
import time

"""
Generic asynchronous Order manager process for Upstox.
Version #1 It will exclusively simulate a bracket order only.
"""
def place_order_internal(mdict):
    logging.info("place_order_internal: {}".format(mdict))
    u_obj = Upstox().obj
    # Prepare to place order
    if mdict['ttype'] == 'BUY':
        ttype = TransactionType.Buy
    elif mdict['ttype'] == 'SELL':
        ttype = TransactionType.Sell
    else:
        print("Bad ttype: %s" % mdict['ttype'])
        sys.exit(0)
    
    try:
        symbol = u_obj.get_instrument_by_symbol(mdict['exchange'], mdict['symbol'])
    except Exception as e:
        print('Bad symbol: %s' % str(e))
        sys.exit(0)

    quantity = int(mdict['quantity'])

    if mdict['ordertype'] == 'MARKET':
        ordertype = OrderType.Market
    elif mdict['ordertype'] == 'LIMIT':
        ordertype = OrderType.Limit
    elif mdict['ordertype'] == 'SL':
        ordertype = OrderType.StopLossLimit
    elif mdict['ordertype'] == 'SLM':
        ordertype = OrderType.StopLossMarket
    else:
        print('Bad ordertype %s' % mdict['ordertype'])
        sys.exit(0)

    producttype = mdict['producttype']
    if mdict['producttype'] == 'INTRADAY':
        producttype = ProductType.Intraday
    elif mdict['producttype'] == 'CO':
        producttype = ProductType.CoverOrder
    elif mdict['producttype'] == 'OCO':
        producttype = ProductType.OneCancelsOther
    elif mdict['producttype'] == 'DELIVERY':
        producttype = ProductType.Delivery
    else:
        print('Bad product type: %s' % mdict['producttype'])
        sys.exit(0)

    price = 0.0
    if mdict['price']:
        price = float(mdict['price'])

    trigger_price = None
    if mdict['trigger_price']:
        trigger_price = float(mdict['trigger_price'])

    disclosed_quantity = 0
    if mdict['disclosed_quantity']:
        disclosed_quantity = int(mdict['disclosed_quantity'])

    duration = DurationType.DAY

    if mdict['stoploss']:
        stoploss = float(mdict['stoploss'])
    else:
        stoploss = None

    if mdict['square_off']:
        square_off = float(mdict['square_off'])
    else:
        square_off = None

    if mdict['trailing_ticks']:
        trailing_ticks = int(mdict['trailing_ticks'])
    else:
        trailing_ticks = None

    try:
        logging.info("place_order_internal:  Placing Order ...{}".format(mdict))
        result = u_obj.place_order(ttype,  # transaction_type
                         # u.get_instrument_by_symbol('NSE_FO', get_symbol()),  # instrument
                         symbol,
                         quantity,  # quantity
                         ordertype,  # order_type
                         producttype,  # product_type
                         price,  # price
                         trigger_price,  # trigger_price
                         disclosed_quantity,  # disclosed_quantity
                         duration,  # duration
                         stoploss,  # stop_loss
                         square_off,  # square_off
                         trailing_ticks)  # trailing_ticks 20 * 0.05

    except Exception as e:
        print("Place order failed: %s" % str(e))

    logging.info(str(result))
    return result
    

class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            print("Singleton.__new__(): Creating instance of %s" % str(cls))
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

# orders = {}
# Instead of making it a global variable, lets make it a global object
class OrdersDB(Singleton):
    obj = {}


class Order():
    """
    {'quantity': 20, 'exchange_order_id': '1100000015744822',
    'order_type': 'L', 'status': 'cancelled', 'transaction_type': 'S',
    'exchange': 'NSE_FO', 'trigger_pr ice': 0.0, 'symbol':
    'BANKNIFTY20MARFUT', 'traded_quantity': 0, 'is_amo': False, 'product':
    'OCO', 'order_request_id': '2', 'duration': None, 'price': 20886.4 5,
    'time_in_micro': '1584692911938515', 'parent_order_id': '200320000861199',
    'order_id': '200320000862560', 'message': '', 'exchange_time':
    '20-Mar-2020 13:5 8:22', 'disclosed_quantity': 20, 'token': 42620,
    'average_price': 0.0, 'instrument': Instrument(exchange='NSE_FO',
    token=42620, parent_token=26009, symbol='ba nknifty20marfut', name='',
    closing_price=20028.5, expiry='1585161000000', strike_price=None,
    tick_size=5.0, lot_size=20, instrument_type='FUTIDX', isin=None)}
    """
    u = None
    # Status to state mapping
    status_to_state = {
            'put order req received': 'PUT_ORDER_REQ_RECEIVED',
            'validation pending': 'VALIDATION_PENDING',
            'open pending': 'OPEN_PENDING',
            'open': 'OPEN',
            'trigger pending': 'TRIGGER_PENDING',
            'complete': 'COMPLETE',
            'rejected': 'REJECTED',
            'modify validation pending': 'MODIFY_VALIDATION_PENDING',
            'modify pending': 'MODIFY_PENDING', 
            'not modified': 'NOT_MODIFIED',
            'modified': 'MODIFIED',
            'cancel pending': 'CANCEL_PENDING',
            'not cancelled': 'NOT_CANCELLED',
            'cancelled': 'CANCELLED',
            'after market order req received': 'AFTER_MARKET_ORDER_REQ_RECEIVED', 
            'modify after market order req received': 'MODIFY_AFTER_MARKET_ORDER_REQ_RECEIVED',
            'cancelled after market order': 'CANCELLED_AFTER_MARKET_ORDER'
            }
    states = ['INIT', 'PUT_ORDER_REQ_RECEIVED',
            'VALIDATION_PENDING','OPEN_PENDING', 'OPEN', 'TRIGGER_PENDING',
            'COMPLETE', 'CANCEL_PENDING', 'CANCELLED', 'NOT_CANCELLED',
            'REJECTED', 'MODIFY_VALIDATION_PENDING', 'MODIFY_PENDING',
            'MODIFIED', 'NOT_MODIFIED', 'AFTER_MARKET_ORDER_REQ_RECEIVED',
            'MODIFY_AFTER_MARKET_ORDER_REQ_RECEIVED',
            'CANCELLED_AFTER_MARKET_ORDER']
    lock = threading.Lock()

    """
    We will not define the transitions table. Instead, we will use the
    to_<state> method to transition. Saves a lot of code.
    """

    def __init__(self):
        self.machine = Machine(model=self, states=self.states,
                send_event=True, initial='INIT', queued=True)

        self.quantity = None
        self.exchange_order_id = None
        self.order_type = None
        self.status = None
        self.transaction_type = None
        self.exchange = None
        self.trigger_price = None
        self.symbol = None
        self.traded_quantity = None
        self.is_amo = None
        self.product = None
        self.order_request_id = None
        self.duration = None
        self.price = None
        self.time_in_micro = None
        self.parent_order_id = None
        self.order_id = None
        self.message = None
        self.exchange_time = None
        self.disclosed_quantity = None
        self.token = None
        self.average_price = None
        self.instrument = None

        self.result = None


    def __del__(self):
        pass

    def __repr__(self):
        pass

    """
    State entry functions
    """
    def update_odr_details(self, update_d):
        self.quantity = update_d['quantity']
        self.exchange_order_id = update_d['exchange_order_id']
        self.order_type = update_d['order_type']
        self.transaction_type = update_d['transaction_type']
        self.trigger_price = update_d['trigger_price']
        self.symbol = update_d['symbol']
        self.traded_quantity = update_d['traded_quantity']
        self.product = update_d['product']
        self.order_request_id = update_d['order_request_id']
        self.price = update_d['price']
        self.parent_order_id = update_d['parent_order_id']
        self.order_id = update_d['order_id']
        self.message = update_d['message']
        self.exchange_time = update_d['exchange_time']

    def on_enter_PUT_ORDER_REQ_RECEIVED(self, event):
        """
        Initialize the variables.
        """
        update_d = event.kwargs.get('upd', None)
        self.update_odr_details(update_d)


    def entry_handler(self, event):
        update_d = event.kwargs.get('upd', None)
        self.update_odr_details(update_d)

    def on_enter_OPEN(self, event):
        self.entry_handler(event)

    def on_enter_TRIGGER_PENDING(self, event):
        self.entry_handler(event)

    def on_enter_COMPLETE(self, event):
        self.entry_handler(event)

    def on_enter_CANCELLED(self, event):
        self.entry_handler(event)

    def on_enter_NOT_CANCELLED(self, event):
        self.entry_handler(event)

    def on_enter_REJECTED(self, event):
        self.entry_handler(event)

    def on_enter_MODIFIED(self, event):
        self.entry_handler(event)

    def on_enter_NOT_MODIFIED(self, event):
        self.entry_handler(event)

"""
Topic subscriber class.
"""
class TopicSubscriber:
    def __init__(self):
        self.context = 0
        self.socket = 0
        self.topic = ""

    def __del__(self):
        """
        Destructor
        """
        self.context.destroy(linger=None)

    def init(self, topic, port):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect("tcp://localhost:%s" % port)
        self.topic = topic
        self.socket.setsockopt_string(zmq.SUBSCRIBE, self.topic)
        self.socket.setsockopt(zmq.RCVTIMEO, 1000) # Check every 1 sec if we need to exit.

    def sock_receive(self):
        try: 
            msg = self.socket.recv_string()
            # Need to remote topic from string before returning it.
            data = msg.split(' ', 1)[1]
            return data
        except:
            return None


def subscribe_to_ticks_publisher():
    """
    Subscribe to ticks collector.
    topic:  Topic we are interested in order updates.
    """
    topic = 'Order'
    publish_port = "5000"
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

def dump_db():
    print("********** dump_db enter **********")
    try:
        obj = OrdersDB().obj
        print(type(obj))
        print(obj)
    except Exception as e:
        print("dump_db(): %s" % str(e))

    print("********** dump_db exit **********")
        

def orders_update_processor():
    sub = subscribe_to_ticks_publisher()

    while True:
        try:
            update = sub.sock_receive()

            if update is None:
                # Timeout triggered. Check if we need to exit.
                if thread_control().stop_job == True:
                    print("orders_update_processor: Exiting...")
                    del sub
                    sys.exit(0)
                else:
                    continue

            logging.debug(update)
            update_d = eval(update)
        except Exception as e:
            print("""
            +++++++  Orders update processor... +++++++
            """)
            print(str(e))
            sys.exit(0)

        # Process the update..
        order_id = update_d['order_id']
        logging.info("orders_update_processor() order_id: %s" % order_id)

        try:
            print("try block: looking for order by id")
            dump_db()
            order = OrdersDB().obj[order_id]
            logging.info("Order object found...")
        except Exception as e:
            logging.info("Creating new order object...")
            print("except block: Creating new order object for id %s" % order_id)
            order = Order()
            OrdersDB().obj[order_id] = order
            dump_db()
            print((type(OrdersDB().obj)))

        state = order.status_to_state[update_d['status']]
        fstring = 'to_%s' % state
        method_to_call = getattr(order, fstring)
        method_to_call(upd=update_d)

        # Invoke the Bracket Order State machine.
        bo = BracketOrder()
        BracketOrder().process(odr=order) 



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

class thread_control(Singleton):
    stop_job = False

class Upstox(Singleton):
    obj = None

    def __init__(self):
        pass

    def init(self, loc):
        if not self.obj:
            self.obj = load_from_file(loc)
            self.obj.get_master_contract('NSE_EQ')
            self.obj.get_master_contract('NSE_FO')

class UnitTest(Singleton):
    ut = False

    def __init__(self):
        pass

    def enable(self):
        logging.info("enable(): Enabling unit test mode...")
        print("enable(): Enabling unit test mode...")
        self.ut = True

    def enabled(self):
        return self.ut

def UnitTestEnable():
    UnitTest().enable()

def UnitTestMode():
    return UnitTest().enabled()

class BracketOrder(Singleton):
    """
    Manage only one trade to begin with.
    """
    stoploss_points = None
    stoploss = None 

    trail = None 
    trailing_ticks = None

    square_off = None 
    square_off_points = None 

    limit_order_id = None
    limit_order_result = None

    slm_order_id = None
    slm_order_result = None

    target_order_id = None
    target_order_result = None

    sl_hit = None
    target_hit = None

    mdict = None
    
    states = ['INIT', 'BO_ORDER_RECEIVED', 'LIMIT_ORDER_PLACED',
            'SL_ORDER_PLACED', 'TARGET_ORDER_PLACED', 'ORDER_REJECTED',
            'ORDER_CANCELLED', 'EXIT']

    transitions = [
            {
                'trigger': 'new_order',
                'source': 'INIT',
                'dest': 'BO_ORDER_RECEIVED',
                'prepare': 'initialize_bo',
                'after': 'after_func'
                },
            #################################
            # source: BO_ORDER_RECEIVED
            #################################
            {
                'trigger': 'process',
                'source': 'BO_ORDER_RECEIVED',
                'dest': 'LIMIT_ORDER_PLACED',
                'conditions': 'limit_order_complete',
                'after': 'after_func'
                },
            {
                'trigger': 'process',
                'source': 'BO_ORDER_RECEIVED',
                'dest': 'ORDER_REJECTED',
                'conditions': 'order_rejected',
                'after': 'after_func'
                },
            {
                'trigger': 'process',
                'source': 'BO_ORDER_RECEIVED',
                'dest': 'ORDER_CANCELLED',
                'conditions': 'order_cancelled',
                'after': 'after_func'
                },
            #################################
            # source: ORDER_REJECTED
            #################################
            {
                'trigger': 'process',
                'source': 'ORDER_REJECTED',
                'dest': 'EXIT',
                'after': 'exit_handler'
                },
            #################################
            # source: ORDER_CANCELLED
            #################################
            {
                'trigger': 'process',
                'source': 'ORDER_CANCELLED',
                'dest': 'EXIT',
                'after': 'exit_handler'
                },
            #################################
            # source: LIMIT_ORDER_PLACED
            #################################
            {
                'trigger': 'process',
                'source': 'LIMIT_ORDER_PLACED',
                'dest': 'SL_ORDER_PLACED',
                'conditions': 'sl_order_placed',
                'after': 'after_func'
                },
            {
                'trigger': 'process',
                'source': 'LIMIT_ORDER_PLACED',
                'dest': 'ORDER_REJECTED',
                'conditions': 'order_rejected',
                'after': 'after_func'
                },
            {
                'trigger': 'process',
                'source': 'LIMIT_ORDER_PLACED',
                'dest': 'ORDER_CANCELLED',
                'conditions': 'order_cancelled',
                'after': 'after_func'
                },
            #################################
            # source: SL_ORDER_PLACED
            #################################
            {
                'trigger': 'process',
                'source': 'SL_ORDER_PLACED',
                'dest': 'ORDER_CANCELLED',
                'conditions': 'order_cancelled',
                'after': 'after_func'
                },
            {
                'trigger': 'process',
                'source': 'SL_ORDER_PLACED',
                'dest': 'ORDER_REJECTED',
                'conditions': 'order_rejected',
                'after': 'after_func'
                },
            {
                'trigger': 'process',
                'source': 'SL_ORDER_PLACED',
                'dest': 'TARGET_ORDER_PLACED',
                'conditions': 'target_order_placed',
                'after': 'after_func'
                },
            #################################
            # source: TARGET_ORDER_PLACED
            #################################
            {
                'trigger': 'process',
                'source': 'TARGET_ORDER_PLACED',
                'dest': 'ORDER_CANCELLED',
                'conditions': 'order_cancelled',
                'after': 'after_func'
                },
            {
                'trigger': 'process',
                'source': 'TARGET_ORDER_PLACED',
                'dest': 'ORDER_REJECTED',
                'conditions': 'order_rejected',
                'after': 'after_func'
                },
            {
                'trigger': 'process',
                'source': 'TARGET_ORDER_PLACED',
                'dest': 'EXIT',
                'conditions': 'trade_complete',
                'after': 'exit_handler'
                },
            {
                'trigger': 'new_order',
                'source': 'EXIT',
                'dest': 'BO_ORDER_RECEIVED',
                'prepare': 'initialize_bo',
                'conditions': 'new_bo_order_recieved',
                'after': 'after_func'
                },
            ]

    machine = None

    def __init__(self):
        if self.machine is None:
            self.machine = Machine(model=self, states=self.states,\
                    transitions=self.transitions,\
                    before_state_change='machine_before_state_change_func',
                    after_state_change='machine_after_state_change_func',
                    finalize_event='machine_finalize_event_func',
                    initial='INIT', send_event=True, queued=True)

    def machine_before_state_change_func(self, event):
        logging.info("machine_before_state_change_func {}".format(self.state))

    def machine_after_state_change_func(self, event):
        logging.info("machine_after_state_change_func {}".format(self.state))

    def machine_finalize_event_func(self, event):
        logging.info("machine_finalize_event_func State: {} ".format(self.state))

    def after_func(self, event):
        logging.info("after_func: state %s" % self.state)
        self.process(event)


    def new_bo_order_recieved(self, event):
        if self.mdict:
            return True

        return False

    def initialize_bo(self, event):
        """
        Parse the bracket order and break them in to SL, LIMT and TARGET
        """
        mdict = event.kwargs.get('odr', None)

        self.stoploss_points = float(mdict['stoploss'])
        self.square_off_points = float(mdict['square_off'])
        self.trailing_ticks = int(mdict['trailing_ticks'])
        self.entry_price = float(mdict['price'])

        if mdict['ttype'] == 'BUY':
            self.stoploss = self.entry_price - self.stoploss_points
            self.square_off = self.entry_price + self.square_off_points
        else: # SELL
            self.stoploss = self.entry_price - self.stoploss_points
            self.square_off = self.entry_price + self.square_off_points

    def place_limit_order(self, event):
        """
        Place a limit order
        """
        if self.limit_order_id is not None:
            # We have already placed a limit order. No need of placing 
            # another.
            logging.info("place_limit_order: {}".format(self.limit_order_id))
            return

        # mdict = event.kwargs.get('odr', None)
        mdict = self.mdict
        logging.debug("place_limit_order: {}".format(mdict))

        if mdict:
            # Make a copy so that the original is retained.
            new_mdict = dict(mdict)

            # Edit the new copy for limit order.
            new_mdict['ordertype'] = 'LIMIT'
            new_mdict['producttype'] = 'INTRADAY'
            new_mdict['stoploss'] = None
            new_mdict['square_off'] = None
            new_mdict['trailing_ticks'] = None
            new_mdict['trigger_price'] = None

            self.limit_order_result = place_order_internal(new_mdict)
            self.limit_order_id = self.limit_order_result['order_id']

    def on_enter_BO_ORDER_RECEIVED(self, event):
        self.place_limit_order(event)

    def limit_order_complete(self, event):
        odr = event.kwargs.get('odr', None)

        if odr:
            logging.info("limit_order_complete: id {} state {}".format(odr.order_id, odr.state))

        if not odr:
            return False

        if UnitTestMode():
            # Just running in unit testing mode.
            logging.info("limit_order_complete: Unit Test Mode: Returning True...")
            return True

        if (odr.order_id == self.limit_order_id) and \
            odr.state == 'COMPLETE':
            logging.info("limit_order_complete: True")
            return True
        else:
            logging.info("limit_order_complete: False")
            return False

    def target_order_open(self, event):
        odr = event.kwargs.get('odr', None)

        if odr:
            logging.info("target_order_open: id {} state {}".format(odr.order_id, odr.state))

        if not odr:
            return False

        if UnitTestMode():
            # Just running in unit testing mode.
            return True

        if (odr.order_id == self.target_order_id) and \
            odr.state == 'OPEN':
            logging.info("target_order_open: True")
            return True
        else:
            logging.info("target_order_open: False")
            return False

    def place_slm_order(self, event):
        """
        Place a Stoploss Market order
        """
        logging.debug("place_slm_order(): Sleeping for 2 seconds..")
        time.sleep(2) # Sleep for two secs, else the request might get throttled...
        if self.slm_order_id is not None:
            # We have already placed a limit order. No need of placing 
            # another.
            logging.info("place_slm_order: {}".format(self.slm_order_id))
            return

        # mdict = event.kwargs.get('odr', None)
        mdict = self.mdict
        logging.info("place_slm_order: {}".format(mdict))

        if mdict:
            new_mdict = dict(self.mdict)

            if new_mdict['ttype'] == 'BUY':
                new_mdict['ttype'] = 'SELL'
            else:
                new_mdict['ttype'] = 'BUY'

            # Edit the new copy for limit order.
            new_mdict['ordertype'] = 'SLM'
            new_mdict['producttype'] = 'INTRADAY'

            new_mdict['price'] = 0.0
            new_mdict['trigger_price'] = self.stoploss

            new_mdict['stoploss'] = None
            new_mdict['square_off'] = None
            new_mdict['trailing_ticks'] = None

            self.slm_order_result = place_order_internal(new_mdict)
            self.slm_order_id = self.slm_order_result['order_id']

    def on_enter_LIMIT_ORDER_PLACED(self, event):
        """
        Action function for LIMIT_ORDER_PLACED state.
        """
        self.place_slm_order(event)

    def sl_order_placed(self, event):
        odr = event.kwargs.get('odr', None)

        if odr:
            logging.info("sl_order_placed: id {} state {}".format(odr.order_id, odr.state))

        if not odr:
            logging.info("sl_order_placed:#1 Returning False...")
            return False

        if UnitTestMode():
            # Just running in unit testing mode.
            logging.info("sl_order_placed: Unit Test Mode: Returning True...")
            return True

        if (odr.order_id == self.slm_order_id) and \
            odr.state == 'TRIGGER_PENDING':
            logging.info("sl_order_placed:#1 Returning True...")
            return True
        else:
            logging.info("sl_order_placed:#2 Returning False...")
            return False

    def place_target_order(self, event):
        logging.debug("place_target_order(): Sleeping for 2 seconds..")
        time.sleep(2) # To prevent throttling..
        """
        Place a target order
        """
        if self.target_order_id is not None:
            # We have already placed a limit order. No need of placing 
            # another.
            logging.info("place_target_order: {}".format(self.target_order_id))
            return

        # mdict = event.kwargs.get('odr', None)
        mdict = self.mdict
        logging.info("target_order_id: {}".format(mdict))

        if mdict:
            new_mdict = dict(self.mdict)

            if new_mdict['ttype'] == 'BUY':
                new_mdict['ttype'] = 'SELL'
            else:
                new_mdict['ttype'] = 'BUY'

            # Edit the new copy for limit order.
            new_mdict['ordertype'] = 'LIMIT'
            new_mdict['producttype'] = 'INTRADAY'

            new_mdict['price'] = self.square_off
            new_mdict['trigger_price'] = None

            new_mdict['stoploss'] = None
            new_mdict['square_off'] = None
            new_mdict['trailing_ticks'] = None

            self.target_order_result = place_order_internal(new_mdict)
            self.target_order_id = self.target_order_result['order_id']

    def on_enter_SL_ORDER_PLACED(self, event):
        self.place_target_order(event)

    def target_order_placed(self, event):
        odr = event.kwargs.get('odr', None)

        if not odr:
            return False

        if (odr.order_id == self.target_order_id) and \
            odr.state == 'OPEN':
            return True
        else:
            return False

    def order_cancelled(self, event):
        odr = event.kwargs.get('odr', None)

        if odr:
            logging.info("order_cancelled: {} {}".format(odr.order_id, odr.state))

        if not odr:
            logging.info("order_cancelled #1: Returning False")
            return False

        if UnitTestMode():
            # Our Order is not cancelled.
            return False

        if odr.state == 'CANCELLED':
            logging.info("order_cancelled #1: Returning True")
            return True
        else:
            logging.info("order_cancelled #2: Returning False")
            return False


    def trail_support(self, event):
        # Not supporting trailing yet...
        return False

    def trade_complete(self, event):
        # Either SL order is complete.
        # Or Target order is complete.
        if OrdersDB().obj[self.slm_order_id].state == 'COMPLETE':
            self.sl_hit = True
            self.target_hit = False
            return True

        if OrdersDB().obj[self.target_order_id].state == 'COMPLETE':
            self.sl_hit = False
            self.target_hit = True
            return True

        return False

    def order_rejected(self, event):
        odr = event.kwargs.get('odr', None)

        if odr:
            logging.info("order_rejected: {} {}".format(odr.order_id, odr.state))

        if not odr:
            logging.info("order_rejected #1: Returning False")
            return False

        if UnitTestMode():
            # In UT mode, our order is not rejected.
            return False
 
        if odr.state == 'REJECTED':
            logging.info("order_rejected #1: Returning True")
            return True
        else:
            logging.info("order_rejected #2: Returning False")
            return False


    def on_enter_ORDER_CANCELLED(self, event):
        """
        If Entry order is rejected, its not much of a risk
        If SLM order is rejected, cancel entry order.
        If Target order is rejected, just log..
        """
        odr = event.kwargs.get('odr', None)

        if odr.order_id == self.limit_order_id:
            logging.info("Limit order cancelled: %s" % odr.message)
        elif odr.order_id == self.slm_order_id:
            logging.info("Stoploss order cancelled: %s" % odr.message)
            # Exit all trades. Cancel all orders.
            # self.to_EXIT()
        elif odr.order_id == self.target_order_id:
            logging.info("Target order cancelled: %s" % odr.message)
            # No point retrying coz most likely, it will get rejected again.
            # Let the user take over..

    def on_enter_ORDER_REJECTED(self, event):
        """
        If Entry order is rejected, its not much of a risk
        If SLM order is rejected, cancel entry order.
        If Target order is rejected, just log..
        """
        odr = event.kwargs.get('odr', None)

        if odr.order_id == self.limit_order_id:
            logging.info("Limit order rejected: %s" % odr.message)
        elif odr.order_id == self.slm_order_id:
            logging.info("Stoploss order rejected: %s" % odr.message)
            # Exit all trades. Cancel all orders.
            self.to_EXIT()
        elif odr.order_id == self.target_order_id:
            logging.info("Target order rejected: %s" % odr.message)
            # No point retrying coz most likely, it will get rejected again.
            # Let the user take over..


    def prepare_trail(self, event):
        pass

    def exit_handler(self, event):
        logging.info("exit_handler State: {}".format(self.state))
        """
        Cancel all orders.
        If we are in any trade, just exit.
        """
        u_obj = Upstox().obj
        u_obj.cancel_all_orders()

        self.stoploss_points = None
        self.stoploss = None 

        self.trail = None 
        self.trailing_ticks = None

        self.square_off = None 
        self.square_off_points = None 

        self.limit_order_id = None
        self.limit_order_result = None

        self.slm_order_id = None
        self.slm_order_result = None

        self.target_order_id = None
        self.target_order_result = None

        self.mdict = None
        # Rest BracketOrder variables. Prepare for next trade.


class Server(Cmd):
    """
    Not used. Just and example code.
    """
    use_rawinput = False 

    def __init__(self, port): 
        print('Initializing Order Manager on port 5001...')
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", port))

        # f = self.sock.makefile(mode='rw') 
        # cmd.Cmd.__init__(self, stdin=f, stdout=sys.stdout) 

    def start(self):
        self.run = True
        while self.run:
            print('Listenning...')
            self.sock.listen(1) # Now wait for client connection

            self.client, self.address = self.sock.accept()
            print("Got a connection from {} {}".format(self.client, self.address))
            f = self.client.makefile(mode='rw') 
            Cmd.__init__(self, stdin=f, stdout=sys.stdout, allow_cli_args=False) 
            Cmd.debug = True
            # Cmd.__init__(self, stdin=f, stdout=f) 
            try:
                print("Starting the cmdloop()")
                self.cmdloop()
            except Exception as e:
                print(str(e))

    def do_ping(self, line):    
        """
        Ping
        """
        print('Got Ping...Sending Pong...')
        reply = 'pong ' + line + '\n'
        self.client.send(reply.encode())

    def do_exit(self, line):    
        """
        Exit server...
        """
        print('Exiting...')
        self.client.send('OK\n'.encode())
        self.run = False

        # Send a signal to the child thread to exit.
        thread_control().stop_job = True

        for thread in threading.enumerate():
            if thread.name != 'MainThread':
                print("MainThread: Waiting for %s to exit..." % thread.name)
                thread.join()
                print("MainThread: Done...")


    def do_place_bracket_order(self, line):
        """
        Place bracket order
        """
        print('Placing a bracket order...')
        print(line)
        self.client.send('OK\n'.encode())

        mdict = eval(line)

        bo = BracketOrder()
        print(bo.state)
        bo.mdict = mdict
        bo.new_order(odr=mdict)

    def do_modify_order(self, line):
        """
        Modify order def modify_order(self, order_id, quantity = None,
        order_type = None, price = None, trigger_price = None,
        disclosed_quantity = None, duration = None):
        """
        print('Modifying order...')
        print(line)

        logging.info("modify_order: {}".format(line))
        u_obj = Upstox().obj

        try:
            mdict = eval(line)
        except Exception as e:
            print("Eval failed: %s" % str(e))
            return

        order = int(mdict['order'])

        if 'quantity' in mdict:
            quantity = int(mdict['quantity'])
        else:
            quantity = None

        if 'price' in mdict:
            price = float(mdict['price'])
        else:
            price = None

        if 'trigger_price' in mdict:
            trigger_price = float(mdict['trigger_price'])
        else:
            trigger_price = None

        result = None

        try:
            result = u_obj.modify_order(order,
                    quantity = quantity,
                    order_type = None,
                    price = price,
                    trigger_price = trigger_price,
                    disclosed_quantity = None,
                    duration = None
                    )
        except Exception as e:
            print("Modify order failed: %s" % str(e))

        reply = str(result) + "\n"
        self.client.send(reply.encode())


    @staticmethod
    def dump_order_by_id(order_id):
        print(OrdersDB().obj)
        try:
            order = OrdersDB().obj[order_id]
            reply += "symbol        : %s\n" % str(order.symbol)
            reply += "order id      : %s\n" % str(order.order_id)
            reply += "order type    : %s\n" % str(order.order_type)
            reply += "status        : %s\n" % str(order.order_type)
            reply += "message       : %s\n" % str(order.message)
            reply += "quantity      : %s\n" % str(order.quantity)
            reply += "price         : %s\n" % str(order.price)
            reply += "trigger_price : %s\n" % str(order.trigger_price)
        except Exception as e:
            return "%s not found." % order_id

        return reply

    def do_dump_orders(self, line):
        if len(OrdersDB().obj) == 0:
            self.client.send("No orders found\n".encode())
            return

        reply = "\n**************************************************\n"

        try:
            for order_id,order in OrdersDB().obj.items():
                print(order_id)
                print(type(order_id))
                reply += "symbol        : %s\n" % str(order.symbol)
                reply += "order id      : %s\n" % str(order.order_id)
                reply += "order type    : %s\n" % str(order.order_type)
                reply += "status        : %s\n" % str(order.order_type)
                reply += "message       : %s\n" % str(order.message)
                reply += "quantity      : %s\n" % str(order.quantity)
                reply += "price         : %s\n" % str(order.price)
                reply += "trigger_price : %s\n" % str(order.trigger_price)
                reply = "\n**************************************************\n"
                reply += self.dump_order_by_id(order_id)
        except Exception as e:
            print("do_dump_orders(): %s" % str(e))
            reply = str(e)

        self.client.send(reply.encode())
    

    def do_get_bo_state(self, line):
        reply = str(BracketOrder().state) + '\n'
        self.client.send(reply.encode())

    def do_get_orders_status(self, line):
        """
        Get Orders status.
        """
        bo = BracketOrder()

        data = {}
        orders = OrdersDB().obj

        if bo.limit_order_id:
            data['limit_order_id'] = bo.limit_order_id
            data['limit_order_status'] = orders[bo.limit_order_id].state
            data['l_message'] = orders[bo.limit_order_id].message

        if bo.slm_order_id:
            data['slm_order_id'] = bo.slm_order_id
            data['slm_order_status'] = orders[bo.slm_order_id].state
            data['s_message'] = orders[bo.slm_order_id].message

        if bo.target_order_id:
            data['target_order_id'] = bo.target_order_id
            data['target_order_status'] = orders[bo.target_order_id].state
            data['t_message'] = orders[bo.target_order_id].message

        reply = str(data) + '\n'
        self.client.send(reply.encode())

def signal_handler_function(signum, frame):
    pass

def server_thread():
    s = Server(5001)
    s.start()


def main():
    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(filename="logs/ordermanager.log",
            level=logging.INFO,
            format=FORMAT)
    logging.getLogger('transitions').setLevel(logging.CRITICAL)
    parser = argparse.ArgumentParser("Upstox order manager.")
    parser.add_argument('-u', help='Upstox session object pickle location')
    parser.add_argument('-t', action='store_true',
            help='Enable unit testing mode.')
    
    args = parser.parse_args()

    try:
        location = args.u
    except:
        print('Please pass the upstox session object location.')
        sys.exit(0)

    if args.t:
        print("Enabling unit test mode..")
        UnitTestEnable()

    try:
        u = Upstox()
        u.init(location)
        Order.u = u
    except Exception as e:
        print("Not able to create Upstox object")
        print(str(e))
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler_function)

    # One thread subscribes to ticks.
    t = threading.Thread(target=orders_update_processor)
    t.start()

    s = Server(5001)
    s.start()


if __name__ == '__main__':
    main()
