"""
Order class to manager orders.
"""
import sys
sys.path.append('../config')
sys.path.append('../ticks_collection')
from ConfigurationClass import Configuration as cf
from ScripClass import Scrip
import logging
from upstox_api.api import *

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


class Order:
    def __init__(self):
        self.c = cf()
        self.u = load_from_file('upstox.pickle')
        self.u.get_master_contract('MCX_FO') # get contracts for MCX FO
        self.u.get_master_contract('NSE_EQ')
        self.u.get_master_contract('BSE_EQ')
        self.u.get_master_contract('NSE_FO')

        """
        Full documentation available at:-
        https://github.com/upstox/upstox-python
        """

    def init(self, tsb, pdt='MIS', vld=None,
            fake=False, var=None):
        s = Scrip()
        s.init_from_tsb(tsb)

        print("##### tsb: %s pdt %s vld %s var %s fake %d" %(tsb,pdt,vld,var,fake))

        self.var = var
        self.vld = vld
        self.tsb = tsb
        self.fake = fake

        """
        TODO Set the product type
        """
        self.pdt = ProductType.Intraday

        """
        Set the exchange.
        """
        self.xch = s.xch

    def place_market_order(self, txn, qty):
        self.odr_id = None
        if self.fake is True:
            return 12345

	if txn == 'BUY':
	    ttype = TransactionType.Buy
	else:
	    ttype = TransactionType.Sell

        try:
	    self.odr_id = self.u.place_order(TransactionType.Buy,  # transaction_type
		    self.u.get_instrument_by_symbol(self.xch, self.tsb),  # instrument
		    qty,  # quantity
		    OrderType.Market,  # order_type
		    self.pdt, # ProductType.Intraday,  # product_type
		    0.0,  # price
		    None,  # trigger_price
		    0,  # disclosed_quantity
		    DurationType.DAY,  # duration
		    None,  # stop_loss
		    None,  # square_off
		    None  )# trailing_ticks
	    )

        except Exception as e:
            logging.error(e)
        finally:
            return self.odr_id

    def place_update_limit_order(self, txn, qty, pri, oid=0):
        self.odr_id = None
	if txn == 'BUY':
	    ttype = TransactionType.Buy
	else:
	    ttype = TransactionType.Sell

        logging.info("place_update_limit_order(): {} {} {} {}".format(txn, qty, pri, oid))
        if self.fake is True:
            return 12345

        try:
            if oid == 0:
                self.odr_id = self.kite.place_order(variety=self.var,
                        exchange=self.xch,
                        tradingsymbol=self.tsb,
                        transaction_type=self.ttype,
                        quantity=qty,
                        product=self.pdt,
                        order_type=self.kite.ORDER_TYPE_LIMIT,
                        price=pri,
                        validity=None,
                        disclosed_quantity=None,
                        trigger_price=None,
                        squareoff=None,
                        stoploss=None,
                        trailing_stoploss=None,
                        tag=None)
            else:
                self.kite.modify_order(variety=self.var,
                        order_id=oid, parent_order_id=None,
                        quantity=qty, price=pri,
                        order_type=self.kite.ORDER_TYPE_LIMIT,
                        trigger_price=None, validity=None,
                        disclosed_quantity=None)
                self.odr_id = oid
        except Exception as e:
            logging.error(e)
        finally:
            return self.odr_id
        
    def place_update_slm_order(self, txn, qty, tgp, oid=0):
        self.odr_id = None

        txn_str = 'self.ttype = self.kite.TRANSACTION_TYPE_{}'.format(txn)
        exec(txn_str)
        
        if self.fake is True:
            return 12345

        try:
            if oid == 0:
                self.odr_id = self.kite.place_order(variety=self.var,
                        exchange=self.xch,
                        tradingsymbol=self.tsb,
                        transaction_type=self.ttype,
                        quantity=qty,
                        product=self.pdt,
                        order_type=self.kite.ORDER_TYPE_SLM,
                        price=None,
                        validity=None,
                        disclosed_quantity=None,
                        trigger_price=tgp,
                        squareoff=None,
                        stoploss=None,
                        trailing_stoploss=None,
                        tag=None)
            else:
                self.kite.modify_order(variety=self.var,
                        order_id=oid, parent_order_id=None,
                        quantity=qty, price=None,
                        order_type=self.kite.ORDER_TYPE_SLM,
                        trigger_price=tgp, validity=None,
                        disclosed_quantity=None)
                self.odr_id = oid
        except Exception as e:
            logging.error(e)
        finally:
            return self.odr_id

    def place_update_sl_order(self, txn, qty, pri, tgp, oid=0):
        self.odr_id = None

        txn_str = 'self.ttype = self.kite.TRANSACTION_TYPE_{}'.format(txn)
        exec(txn_str)

        if self.fake is True:
            return 12345

        try:
            if oid == 0:
                self.odr_id = self.kite.place_order(variety=self.var,
                        exchange=self.xch,
                        tradingsymbol=self.tsb,
                        transaction_type=self.ttype,
                        quantity=qty,
                        product=self.pdt,
                        order_type=self.kite.ORDER_TYPE_SL,
                        price=pri,
                        validity=None,
                        disclosed_quantity=None,
                        trigger_price=tgp,
                        squareoff=None,
                        stoploss=None,
                        trailing_stoploss=None,
                        tag=None)
            else:
                self.kite.modify_order(variety=self.var,
                        order_id=oid, parent_order_id=None,
                        quantity=qty, price=pri,
                        order_type=self.kite.ORDER_TYPE_SL,
                        trigger_price=tgp, validity=None,
                        disclosed_quantity=None)
                self.odr_id = oid
        except Exception as e:
            logging.error(e)
        finally:
            return self.odr_id

    def cancel_order(self, oid):
        if self.fake is True:
            return

        self.kite.cancel_order(self.var, oid)

    def get_positions(self):
        return self.u.get_positions()

    def get_trades(self):
        return self.kite.trades()

    def get_orders(self):
        return self.kite.orders()

    def get_order_trades(self, oid):
        return self.kite.order_trades(oid)

    def get_order_history(self, oid):
        try:
            return self.kite.order_history(oid)
        except Exception as e:
            print("get_order_history failed.")
            print(e)
            return None

    def get_equity_margins(self):
        return self.kite.margins(Kite.MARGIN_EQUITY)

    def get_commodity_margins(self):
        return self.kite.margins(Kite.MARGIN_COMMODITY)

    def is_order_executed(self, odr_id):
        if self.fake is True:
            return True

        if len(self.get_order_trades(odr_id)) > 0:
            return True
        else:
            return False

    def is_order_successful(self, odr_id):
        return self.is_order_executed(odr_id)

    def is_order_complete(self, odr_id):
        status = False
        if self.fake is True:
            return True

        if odr_id == 0:
            logging.debug("odr_id is 0.")
            return False

        jdata = self.get_order_history(odr_id)

        if jdata is None:
            logging.critical("get_order_history failed for odr_id {}".format(odr_id))
            return False

        for d in jdata:
            if (d['status'] == 'COMPLETE') and (d['price'] > 0):
                status = True
            if (d['status'] == 'REJECTED'):
                print(jdata)
                logging.critical("Order {} REJECTED.".format(odr_id))
                logging.critical("Reason: {} ..".format(d['status_message']))
                sys.exit(0)
        return status

    def get_order_price(self, tsb, odr_id):
        price = 0

        if self.fake is True:
            s = Scrip()
            s.init_from_tsb(tsb)
            instruments = s.exchange + ":" + tsb
            instruments = ''.join(instruments)
            data = self.kite.ltp([instruments])
            data = data[instruments]
            logging.info("Executed price: {}".format(data['last_price']))
            return float(data['last_price'])

        jdata = self.get_order_history(odr_id)
        for d in jdata:
            if (d['status'] == 'COMPLETE') and (d['price'] > 0):
                price = d['price']
        return price

    def set_fake_mode(self):
        print("OrderClass: FAKE MODE ON")
        self.fake = True
