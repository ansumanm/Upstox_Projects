import sys
import configparser
import pickle
import pandas as pd
import io
import requests

class Configuration:
    def __init__(self):
        ConfigFile = "../config/kuber.conf"
        self.LoginConfFile = "../config/login.conf"
        self.kite_obj_loc = "../config/kite.pickle"
        self.cipher_obj_loc = "../config/cipher.pickle"

        config = configparser.ConfigParser()
        config.read(ConfigFile)

        self.log_file = config['SUPERTREND_PSAR']['supertrend_psar_log_file']
        self.strategy_st_psar_csv = config['SUPERTREND_PSAR']['supertrend_psar_out_file']
        self.supertrend_csv = config['SuperTrend']['supertrend_out_file']
        self.psar_csv = config['PSAR']['psar_out_file']
        self.multiplier = int(config['SuperTrend']['multiplier'])
        self.period = int(config['SuperTrend']['period'])
        self.candle_time = int(config['SuperTrend']['time_min'])
        self.cp_default_tf = int(config['CandlePublisher']['default_candle_time'])
        self.Inst_config = config['INSTRUMENT CONFIGURATION']
        self.Inst_Master_DB = config['TicksToMinutes']['instrument_master_db']
        self.Inst_folder = config['TicksToMinutes']['inst_folder']
        self.tradingsymbols_list = config['WS CONFIGURATION']['tradingsymbols'].split(',')
        self.sprtnd_psar_port = config['ZMQ CONFIGURATION']['sprtnd_psar_port']
        self.publish_port = config['ZMQ CONFIGURATION']['publish_port']
        self.data_folder = config['DATA CONFIGURATION']['data_folder']
        self.data_dir = self.data_folder + "/"
        self.candlesdb = config['DATA CONFIGURATION']['candlesdb']
        self.candles_table = config['DATA CONFIGURATION']['candles_table']
        self.candle_publish_port = config['ZMQ CONFIGURATION']['candle_publish_port']
        self.df_publish_port = config['ZMQ CONFIGURATION']['df_publish_port']
        self.plot_publish_port = config['ZMQ CONFIGURATION']['plot_publish_port']
        self.ema_period = config['BNF EMA']['ema_period']
        self.slow_ema_period = config['BNF EMA']['slow_ema_period']
        self.fast_ema_period = config['BNF EMA']['fast_ema_period']
        self.pb_port = config['POSTBACK']['pb_port']
        self.iDB = config['DATA CONFIGURATION']['InstrumentsDB']
        self.Trade_Bot_Key = config['XLOGGER']['Trade_Bot_Key']
        self.Update_Bot_Key = config['XLOGGER']['Update_Bot_Key']
        self.Chat_ID = config['XLOGGER']['Chat_ID']


        self.orders_ut_tc = config['ORDERS_UT CONFIGURATION']['tc']
        self.orders_ut_des = config['ORDERS_UT CONFIGURATION']['des']
        self.orders_ut_tsb = config['ORDERS_UT CONFIGURATION']['scrip']
        self.orders_ut_xch = config['ORDERS_UT CONFIGURATION']['xch']
        self.orders_ut_pdt = config['ORDERS_UT CONFIGURATION']['pdt']
        self.orders_ut_vld = config['ORDERS_UT CONFIGURATION']['vld']
        self.orders_ut_pri = config['ORDERS_UT CONFIGURATION']['pri']
        self.orders_ut_tgp = config['ORDERS_UT CONFIGURATION']['tgp']
        self.orders_ut_txn = config['ORDERS_UT CONFIGURATION']['txn']
        self.orders_ut_qty = config['ORDERS_UT CONFIGURATION']['qty']
        self.orders_ut_odt = config['ORDERS_UT CONFIGURATION']['odt']
        self.orders_ut_oid = config['ORDERS_UT CONFIGURATION']['oid']

        self.loginConfig = configparser.ConfigParser()
        self.loginConfig.read(self.LoginConfFile)

        self.api_key = self.loginConfig['Login Configuration']['api_key']
        self.api_secret = self.loginConfig['Login Configuration']['api_secret']
        self.req_token = self.loginConfig['Login Configuration']['request_token']
        self.access_token = self.loginConfig['ACCESS INFO']['access_token']
        self.user_id = self.loginConfig['ACCESS INFO']['user_id']
        self.Inst_conf_dict = {}
        for key in self.Inst_config:
            self.Inst_conf_dict[key] = eval(self.Inst_config[key])


    def get_api_key(self):
        return self.api_key

    def get_api_secret(self):
        return self.api_secret

    def get_request_token(self):
        return self.req_token

    def get_access_token(self):
        return self.access_token

    def get_candle_publish_port(self):
        return self.candle_publish_port

    def get_plot_publish_port(self):
        return self.plot_publish_port

    def get_ema_period(self):
        return int(self.ema_period)

    def get_slow_ema_period(self):
        return int(self.slow_ema_period)

    def get_fast_ema_period(self):
        return int(self.fast_ema_period)

    def get_supertrend_csv(self):
        return self.supertrend_csv

    def get_supertrend_multiplier(self, tradingsymbol):
        if tradingsymbol.lower() in self.Inst_conf_dict:
            ct, per, mul = (self.Inst_conf_dict[tradingsymbol.lower()]['ST_TxPxM']).split(',')
            # Multiplier
            mul = int(mul)
            return int(mul)
        else:
            return int(self.multiplier)

    def get_supertrend_period(self, tradingsymbol):
        if tradingsymbol.lower() in self.Inst_conf_dict:
            ct, per, mul = (self.Inst_conf_dict[tradingsymbol.lower()]['ST_TxPxM']).split(',')
            # Supertrend Period
            per = int(per)
            return int(per)
        else:
            return int(self.period)

    def get_supertrend_candle_time(self, tradingsymbol):
        if tradingsymbol.lower() in self.Inst_conf_dict:
            ct, per, mul = (self.Inst_conf_dict[tradingsymbol.lower()]['ST_TxPxM']).split(',')
            # Candle Period fed to ST
            ct = int(ct)
            # Supertrend Period
            #per = int(per)
            # Multiplier
            #mul = int(mul)
            # Candle Period in DB
            #cp = int(self.Inst_conf_dict[tradingsymbol.lower()]['candle_period'])
            return int(ct)
        else:
            return int(self.candle_time)

    def get_instrument_candle_period(self, tradingsymbol):
        if tradingsymbol.lower() in self.Inst_conf_dict:
            cp = int(self.Inst_conf_dict[tradingsymbol.lower()]['candle_period'])
            return int(cp)
        else:
            return 0

    def get_candle_publisher_period(self, tradingsymbol):
        if (self.get_instrument_candle_period(tradingsymbol) > 0):
            return self.get_instrument_candle_period(tradingsymbol)
        else:
            return (self.get_candle_publisher_default_timeframe_in_min())

    def get_candle_publisher_default_timeframe_in_min(self):
        return self.cp_default_tf

    def get_candle_publisher_default_timeframe_in_sec(self):
        return (self.cp_default_tf*60)

    def get_ws_publish_port(self):
        return int(self.publish_port)

    def get_pb_port(self):
        return int(self.pb_port)

    def get_trade_bot_key(self):
        return self.Trade_Bot_Key

    def get_update_bot_key(self):
        return self.Update_Bot_Key

    def get_chat_id(self):
        return self.Chat_ID


    def get_cipher_obj(self):
        with open(self.cipher_obj_loc, 'rb') as f:
            cipher = pickle.load(f)
            return cipher

    def get_kite_obj(self):
        with open(self.kite_obj_loc, 'rb') as f:
            kite = pickle.load(f)
            return kite

    def set_kite_obj(self, kite):
        with open(self.kite_obj_loc, 'wb') as f:
            pickle.dump(kite, f, pickle.HIGHEST_PROTOCOL)

    def set_login_conf(self, section_name, value):
        self.loginConfig[section_name] = value
        with open(self.LoginConfFile, 'w') as configfile:
            self.loginConfig.write(configfile)

