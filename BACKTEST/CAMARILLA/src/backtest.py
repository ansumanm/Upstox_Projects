#!/usr/bin/env python3
"""
Camarilla pivots backtest
"""
import os
import atexit
import readline
import pickle
from cmd2 import Cmd

from datetime import date
from datetime import datetime as dt
from datetime import timedelta

from nsepy import get_history

import numpy as np
import pandas as pd

history_file = os.path.expanduser('~/.backtest_history')
if not os.path.exists(history_file):
    with open(history_file, "w") as fobj:
        fobj.write("")
readline.read_history_file(history_file)
atexit.register(readline.write_history_file, history_file)

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


class REPL(Cmd):
    prompt = "backtest>"
    intro = """
	Backtest CLI 
    """

    def __init__(self):
        Cmd.__init__(self)
        self.scrip = None

    def do_get_index_data(self, line):
        """
        Get data from 2008 till date.
        Usage: get_index_data <SCRIP>
        """
        idx_history = get_history(symbol=str(line),
                start=date(2008,1,1), 
                end=date(2020,1,10),
                index=True)

        filename = '../data/' + line.replace(" ", "_") + '.csv'
        idx_history.to_csv(filename, header=True, index=False)

    def do_get_stock_data(self, line):
        """
        Get data from 2008 till date.
        Usage: get_stock_data <SCRIP>
        """
        idx_history = get_history(symbol=str(line),
                start=date(2008,1,1), 
                end=date(2020,1,10))

        filename = '../data/' + str(line).replace(" ", "_") + '.csv'
        idx_history.to_csv(filename, header=True, index=True)

    def update_data(self, line, index=False):
        line=str(line)
        filename = '../data/' + line.replace(" ", "_") + '.csv'

        df = pd.read_csv(filename)

        # Get the last date till we have data.
        last_data_date_str = df.iloc[-1].Date
        last_data_date = dt.strptime(last_data_date_str, '%Y-%m-%d')
        from_date = last_data_date.date() + timedelta(days=1)
        to_date = date.today()

        idx_history = get_history(symbol=line,
                start=from_date, 
                end=to_date,
                index=index)
        idx_history = idx_history.reset_index()

        updated_df = pd.concat([df, idx_history])
        updated_df = updated_df.reset_index(drop=True)

        updated_df.to_csv(filename, header=True, index=True)

    def do_update_index_data(self, line):
        """
        If we have already fetched the data once for the scrip, use this to update it.
        Usage: update_index_data <SCRIP>
        """
        self.update_data(line, index=True)

    def do_update_stock_data(self, line):
        """
        If we have already fetched the data once for the scrip, use this to update it.
        Usage: update_stock_data <SCRIP>
        """
        self.update_data(line, index=False)

    def do_set_scrip(self, line):
        """
        A set the scrip name 
        Usage: set_scrip <SCRIP>
        """
        line=str(line)
        self.scrip = line
        print("Scrip set to %s" % line)

    def do_make_camarilla_pivots(self, line):
        """
        Prepare the pivots. Set the scrip first.
        Scrip name is not required if we have set scrip.
        Usage: make_camarilla_pivots [SCRIP]
        """
        line=str(line)
        if self.scrip is None:
            scrip = line
            self.scrip = scrip
            print("Scrip set to %s" % line)
        else:
            scrip = self.scrip

        filename = '../data/' + scrip.replace(" ", "_") + '.csv'

        df = pd.read_csv(filename)

        # Prepare a new dataframe where we have only the relevant data
        cam_df = pd.DataFrame()
        cam_df['Open'] = df['Open']
        cam_df['High'] = df['High']
        cam_df['Low'] = df['Low']
        cam_df['Close'] = df['Close']

        cam_df['pHigh'] = cam_df['High'].shift()
        cam_df['pLow'] = cam_df['Low'].shift()
        cam_df['pClose'] = cam_df['Close'].shift()

        # Delete the first row, coz we dont have the pivots for that.
        cam_df.drop([0], axis=0, inplace=True)

        # Calculate the pivots
        cam_df['pRange'] = cam_df['pHigh'] - cam_df['pLow']
        """
        H6 = [H/L] * C
        H5 = [H6+H4] / 2
        H4 = [0.55*(H-L)] + C
        H3 = [0.275*(H-L)] + C
        H2 = [0.183*(H-L)] + C
        H1 = [0.0916*(H-L)] + C
        L1 = C - [0.0916*(H-L)]
        L2 = C - [0.183*(H-L)]
        L3 = C - [0.275*(H-L)]
        L4 = C - [0.55*(H-L)]
        L5 = [L4 + L6] / 2
        L6 = C - [H6-C]
        """
        cam_df['PIVOT'] = (cam_df['pHigh'] + cam_df['pLow'] + cam_df['pClose'])/3
        cam_df['L1'] = cam_df['pClose'] - 0.0916*cam_df['pRange']
        cam_df['H1'] = cam_df['pClose'] + 0.0916*cam_df['pRange']

        cam_df['L2'] = cam_df['pClose'] - 0.183*cam_df['pRange']
        cam_df['H2'] = cam_df['pClose'] + 0.183*cam_df['pRange']

        cam_df['L3'] = cam_df['pClose'] - 0.275*cam_df['pRange']
        cam_df['H3'] = cam_df['pClose'] + 0.275*cam_df['pRange']

        cam_df['L4'] = cam_df['pClose'] - 0.55*cam_df['pRange']
        cam_df['H4'] = cam_df['pClose'] + 0.55*cam_df['pRange']

        cam_df['H6'] = (cam_df['pHigh']/cam_df['pLow']) * cam_df['pClose']
        cam_df['H5'] = (cam_df['H6'] + cam_df['H4'])/2

        cam_df['L6'] = cam_df['pClose']*2 - cam_df['H6']
        cam_df['L5'] = (cam_df['L4'] + cam_df['L6'])/2

        # Now that we have calculated the pivots, lets drop the previous day columns
        cam_df.drop('pHigh', axis=1, inplace=True)
        cam_df.drop('pLow', axis=1, inplace=True)
        cam_df.drop('pClose', axis=1, inplace=True)

        # Rearrange the columns
        cam_df = cam_df[['Open', 'High', 'Low', 'Close', 'L6', 'L5', 'L4', 'L3', 'L2', 'L1', 'PIVOT', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6']]

        # Write this data to a file, so that we can load it later and run our tests
        pivot_file = '../data/' + scrip.replace(' ', '_') + '_pivots.csv'
        cam_df.to_csv(pivot_file, header=True, index=False)

        # Make it a object variable so that it can be used in other functions.
        self.pivots_df = cam_df

    def do_load_pivot_table(self, line):
        """
        Load the pivots table. 
        Usage: load_pivot_table <SCRIP>
        """
        line=str(line)

        if self.scrip is None:
            scrip = line
            self.scrip = scrip
            print("Scrip set to %s" % line)
        else:
            scrip = self.scrip

        filename = '../data/' + scrip.replace(" ", "_") + '_pivots.csv'

        try:
            self.pivots_df = pd.read_csv(filename)
        except Exception as e:
            print("Failed to load %s: %s" %(filename, str(e)))
            return

    def do_stats_h1p(self, line):
        """
        Display stats for open price between h1 and p
        """
        print("""
        ++++++++++++++++++++++++
        Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)

        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))

        print("How many times price opened between h1 and p")
        filter_df = self.pivots_df[(self.pivots_df.PIVOT < self.pivots_df.Open) & (self.pivots_df.Open < self.pivots_df.H1)].copy()
        open_between_h1p_count = len(filter_df)
        print("{}\t{}%".format(open_between_h1p_count, open_between_h1p_count*100/trades_count))

        print("How many times price opened between h1 and p and high above h5")
        filter_h5_df = filter_df[(filter_df.High > filter_df.H5)]
        filter_h5_df_count = len(filter_h5_df)
        print("{}\t{}%".format(filter_h5_df_count, filter_h5_df_count*100/open_between_h1p_count))

        print("How many times price opened between h1 and p and high above h4")
        filter_h4_df = filter_df[(filter_df.High > filter_df.H4)]
        filter_h4_df_count = len(filter_h4_df)
        print("{}\t{}%".format(filter_h4_df_count, filter_h4_df_count*100/open_between_h1p_count))

        print("How many times price opened between h1 and p and high above h3")
        filter_h3_df = filter_df[(filter_df.High > filter_df.H3)]
        filter_h3_df_count = len(filter_h3_df)
        print("{}\t{}%".format(filter_h3_df_count, filter_h3_df_count*100/open_between_h1p_count))

        print("How many times price opened between h1 and p and high above h3 and low below L3")
        filter_h3l3_df = filter_h3_df[(filter_h3_df.Low < filter_h3_df.L3)]
        filter_h3l3_df_count = len(filter_h3l3_df)
        print("{}\t{}%".format(filter_h3l3_df_count, filter_h3l3_df_count*100/open_between_h1p_count))

        print("How many times price opened between h1 and p and high above h3 and low below L2")
        filter_h3l2_df = filter_h3_df[(filter_h3_df.Low < filter_h3_df.L2)]
        filter_h3l2_df_count = len(filter_h3l2_df)
        print("{}\t{}%".format(filter_h3l2_df_count, filter_h3l2_df_count*100/open_between_h1p_count))

        print("How many times price opened between h1 and p and high above h3 and low below L1")
        filter_h3l1_df = filter_h3_df[(filter_h3_df.Low < filter_h3_df.L1)]
        filter_h3l1_df_count = len(filter_h3l1_df)
        print("{}\t{}%".format(filter_h3l1_df_count, filter_h3l1_df_count*100/open_between_h1p_count))

        print("How many times price opened between h1 and p and high above h3 and low below PIVOT")
        filter_h3p_df = filter_h3_df[(filter_h3_df.Low < filter_h3_df.PIVOT)]
        filter_h3p_df_count = len(filter_h3p_df)
        print("{}\t{}%".format(filter_h3p_df_count, filter_h3p_df_count*100/open_between_h1p_count))



    def do_stats_h2l2(self, line):
        """
        Display stats for open price between h2 and l2
        """
        print("""
        ++++++++++++++++++++++++
        Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)

        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))

        print("How many times price opened between h2 and l2")
        filter_df = self.pivots_df[(self.pivots_df.L2 < self.pivots_df.Open) & (self.pivots_df.Open < self.pivots_df.H2)].copy()
        open_between_h2l2_count = len(filter_df)
        print("{}\t{}%".format(open_between_h2l2_count, open_between_h2l2_count*100/trades_count))

        print("How many times Price ranged across H3 and L3")
        range_h3l3_df = filter_df[(filter_df.L3 > filter_df.Low) & (filter_df.H3 < filter_df.High)].copy()
        range_h3l3_count = len(range_h3l3_df)
        print("{}\t{}%".format(range_h3l3_count, range_h3l3_count*100/open_between_h2l2_count))

        """
        print("How many times low below l2 and high h2")
        filter_hl_df = filter_df[(filter_df.Low < filter_df.L2) & (filter_df.High > filter_df.H2)]
        filter_hl_df_count = len(filter_hl_df)
        print("{}\t{}%".format(filter_hl_df_count, filter_hl_df_count*100/open_between_h2l2_count))
        
        print("How many times low below l2 and high h2 and high above H3")
        filter_hl_h3_df = filter_hl_df[(filter_hl_df.High > filter_hl_df.H3)]
        filter_hl_h3_df_count = len(filter_hl_h3_df)
        print("{}\t{}%".format(filter_hl_h3_df_count, filter_hl_h3_df_count*100/filter_hl_df_count))

        print("How many times low below l2 and high h2 and low below L3")
        filter_hl_l3_df = filter_hl_df[(filter_hl_df.Low < filter_hl_df.L3)]
        filter_hl_l3_df_count = len(filter_hl_l3_df)
        print("{}\t{}%".format(filter_hl_l3_df_count, filter_hl_l3_df_count*100/filter_hl_df_count))
        
        print("How many times low below l2 and high h2 and high above H4")
        filter_hl_h4_df = filter_hl_df[(filter_hl_df.High > filter_hl_df.H4)]
        filter_hl_h4_df_count = len(filter_hl_h4_df)
        print("{}\t{}%".format(filter_hl_h4_df_count, filter_hl_h4_df_count*100/filter_hl_df_count))

        print("How many times low below l2 and high h2 and low below L4")
        filter_hl_l4_df = filter_hl_df[(filter_hl_df.Low < filter_hl_df.L4)]
        filter_hl_l4_df_count = len(filter_hl_l4_df)
        print("{}\t{}%".format(filter_hl_l4_df_count, filter_hl_l4_df_count*100/filter_hl_df_count))
        
        print("How many times low below l2 and high h2 and high above H5")
        filter_hl_h5_df = filter_hl_df[(filter_hl_df.High > filter_hl_df.H5)]
        filter_hl_h5_df_count = len(filter_hl_h5_df)
        print("{}\t{}%".format(filter_hl_h5_df_count, filter_hl_h5_df_count*100/filter_hl_df_count))

        print("How many times low below l2 and high h2 and low below L5")
        filter_hl_l5_df = filter_hl_df[(filter_hl_df.Low < filter_hl_df.L5)]
        filter_hl_l5_df_count = len(filter_hl_l5_df)
        print("{}\t{}%".format(filter_hl_l5_df_count, filter_hl_l5_df_count*100/filter_hl_df_count))
        """




    def do_stats_h2h3(self, line):
        """
        Display stats for open price between h2 and h3
        """
        print("""
        ++++++++++++++++++++++++
        Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)

        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))

        print("How many times price opened between h2 and l2")
        filter_df = self.pivots_df[(self.pivots_df.H2 < self.pivots_df.Open) & (self.pivots_df.Open < self.pivots_df.H3)].copy()
        open_between_h2h3_count = len(filter_df)
        print("{}\t{}%".format(open_between_h2h3_count, open_between_h2h3_count*100/trades_count))

    def do_stats_l2l3(self, line):
        """
        Display stats for open price between l2 and l3
        """
        print("""
        ++++++++++++++++++++++++
        Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)

        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))

        print("How many times price opened between h2 and l2")
        filter_df = self.pivots_df[(self.pivots_df.L3 < self.pivots_df.Open) & (self.pivots_df.Open < self.pivots_df.L2)].copy()
        open_between_l2l3_count = len(filter_df)
        print("{}\t{}%".format(open_between_l2l3_count, open_between_l2l3_count*100/trades_count))

    def do_stats_h3h4(self, line):
        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))
        print("""
        +++++++++++ H3-H4 STATS +++++++++++
        """)
        print("How many times Price opened between H3 and H4")
        filter_df_2 = self.pivots_df[(self.pivots_df.H3 < self.pivots_df.Open) & (self.pivots_df.Open < self.pivots_df.H4)]
        open_between_h3h4_count = len(filter_df_2)
        print("{}\t{}%".format(open_between_h3h4_count, open_between_h3h4_count*100/trades_count))

        print("How many times L3 was achieved")
        filter_df_2_l3 = filter_df_2[filter_df_2.Low < filter_df_2.L3]
        filter_df_2_l3_count = len(filter_df_2_l3)
        print("{}\t{}".format(filter_df_2_l3_count, filter_df_2_l3_count*100/open_between_h3h4_count))

        print("How many times L2 was achieved")
        filter_df_2_l2 = filter_df_2[filter_df_2.Low < filter_df_2.L2]
        filter_df_2_l2_count = len(filter_df_2_l2)
        print("{}\t{}".format(filter_df_2_l2_count, filter_df_2_l2_count*100/open_between_h3h4_count))

        print("How many times L1 was achieved")
        filter_df_2_l1 = filter_df_2[filter_df_2.Low < filter_df_2.L1]
        filter_df_2_l1_count = len(filter_df_2_l1)
        print("{}\t{}".format(filter_df_2_l1_count, filter_df_2_l1_count*100/open_between_h3h4_count))

    def do_stats_l3l4(self, line):
        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))
        print("""
        +++++++++++ L3-L4 STATS +++++++++++
        """)
        print("How many times Price opened between L3 and L4")
        filter_df_3 = self.pivots_df[(self.pivots_df.L4 < self.pivots_df.Open) & (self.pivots_df.Open < self.pivots_df.L3)]
        open_between_l3l4_count = len(filter_df_3)
        print("{}\t{}%".format(open_between_l3l4_count, open_between_l3l4_count*100/trades_count))

        print("How many times H3 was achieved")
        filter_df_3_h3 = filter_df_3[filter_df_3.High > filter_df_3.H3]
        filter_df_3_h3_count = len(filter_df_3_h3)
        print("{}\t{}".format(filter_df_3_h3_count, filter_df_3_h3_count*100/open_between_l3l4_count))

        print("How many times H2 was achieved")
        filter_df_3_h2 = filter_df_3[filter_df_3.High > filter_df_3.H2]
        filter_df_3_h2_count = len(filter_df_3_h2)
        print("{}\t{}".format(filter_df_3_h2_count, filter_df_3_h2_count*100/open_between_l3l4_count))

        print("How many times H1 was achieved")
        filter_df_3_h1 = filter_df_3[filter_df_3.High > filter_df_3.H1]
        filter_df_3_h1_count = len(filter_df_3_h1)
        print("{}\t{}".format(filter_df_3_h1_count, filter_df_3_h1_count*100/open_between_l3l4_count))

    def do_stats_h6(self, line):
        """
        Display h6 stats
        """
        print("""
        ++++++++++++++++++++++++
        Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)

        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))

        print("How many times Price opened above H6")
        filter_df = self.pivots_df[(self.pivots_df.H6 < self.pivots_df.Open)].copy()
        open_above_h6_count = len(filter_df)
        print("{}\t{}%".format(open_above_h6_count, open_above_h6_count*100/trades_count))

    def do_stats_h4l4(self, line):
        """
        Display h4l4 stats
        """
        print("""
        ++++++++++++++++++++++++
        Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)

        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))

        print("""
        +++++++++++ L3-H3 STATS +++++++++++
        """)
        print("How many times Price opened between H4 and L4")
        filter_df = self.pivots_df[(self.pivots_df.L4 < self.pivots_df.Open) & (self.pivots_df.Open < self.pivots_df.H4)].copy()
        open_between_h4l4_count = len(filter_df)
        print("{}\t{}%".format(open_between_h4l4_count, open_between_h4l4_count*100/trades_count))

        print("How many times Price ranged across H3 and L3")
        range_h3l3_df = filter_df[(filter_df.L3 > filter_df.Low) & (filter_df.H3 < filter_df.High)].copy()
        range_h3l3_count = len(range_h3l3_df)
        print("{}\t{}%".format(range_h3l3_count, range_h3l3_count*100/open_between_h4l4_count))


    def do_stats_h3l3(self, line):
        """
        Display h3l3 stats
        """
        print("""
        ++++++++++++++++++++++++
        Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)

        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))

        print("""
        +++++++++++ L3-H3 STATS +++++++++++
        """)
        print("How many times Price opened between H3 and L3")
        filter_df = self.pivots_df[(self.pivots_df.L3 < self.pivots_df.Open) & (self.pivots_df.Open < self.pivots_df.H3)].copy()
        open_between_h3l3_count = len(filter_df)
        print("{}\t{}%".format(open_between_h3l3_count, open_between_h3l3_count*100/trades_count))

        print("How many times Price ranged across H3 and L3")
        filter_df = self.pivots_df[(self.pivots_df.L3 > self.pivots_df.Low) & (self.pivots_df.H3 < self.pivots_df.High)].copy()
        range_h3l3_count = len(filter_df)
        print("{}\t{}%".format(range_h3l3_count, range_h3l3_count*100/trades_count))

        """
        filter_df['L3_H3_points'] = filter_df['H3'] - filter_df['L3']
        filter_df['L3_H1_points'] = filter_df['H1'] - filter_df['L3']
        filter_df['L3_L4_points'] = filter_df['L3'] - filter_df['L4']
        filter_df['H3_L1_points'] = filter_df['H3'] - filter_df['L1']
        filter_df['H3_H4_points'] = filter_df['H4'] - filter_df['H3']


        print("How many times H3 to L3 and vice versa target was met")
        filter_h3l3 = filter_df[(filter_df.Low < filter_df.L3) & (filter_df.High > filter_df.H3)]
        h3l3_target_meet_count = len(filter_h3l3)
        print("{}\t{}%".format(h3l3_target_meet_count, h3l3_target_meet_count*100/open_between_h3l3_count))

        print(" H3 L3 target and SL stats ")
        print(filter_df['L3_H3_points'].mean())
        print(filter_h3l3['H3_H4_points'].mean())
        print(filter_h3l3['L3_L4_points'].mean())

        print(" Short RR stats ")
        print(filter_h3l3['H3_L1_points'].mean())
        print(filter_h3l3['H3_H4_points'].mean())
        print(" Long RR stats ")
        print(filter_h3l3['L3_H1_points'].mean())
        print(filter_h3l3['L3_L4_points'].mean())

        print("L3 to H2")
        filter_l3h2 = filter_df[(filter_df.Low < filter_df.L3) & (filter_df.High > filter_df.H2)]
        filter_l3h2_count = len(filter_l3h2)
        print("{}\t{}%".format(filter_l3h2_count, (filter_l3h2_count*100)/open_between_h3l3_count))

        print("L3 to H1")
        filter_l3h1 = filter_df[(filter_df.Low < filter_df.L3) & (filter_df.High > filter_df.H1)]
        filter_l3h1_count = len(filter_l3h1)
        print("{}\t{}%".format(filter_l3h1_count, filter_l3h1_count*100/open_between_h3l3_count))

        print("H3 to L2")
        filter_h3l2 = filter_df[(filter_df.High > filter_df.H3) & (filter_df.Low < filter_df.L2)]
        filter_h3l2_count = len(filter_h3l2)
        print("{}\t{}%".format(filter_h3l2_count, filter_h3l2_count*100/open_between_h3l3_count))

        print("H3 to L1")
        filter_h3l1 = filter_df[(filter_df.High > filter_df.H3) & (filter_df.Low < filter_df.L1)]
        filter_h3l1_count = len(filter_h3l1)
        print("{}\t{}%".format(filter_h3l1_count, filter_h3l1_count*100/open_between_h3l3_count))
        """

    def do_stats_pivot(self, line):
        """
        Pivot stats
        """
        print("""
        ++++++++++++++++++++++++
        Pivot Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)
        pivots_df = self.pivots_df.copy()

        pivots_df['H6_P'] = pivots_df['H6'] - pivots_df['PIVOT']
        pivots_df['H5_P'] = pivots_df['H5'] - pivots_df['PIVOT']
        pivots_df['H4_P'] = pivots_df['H4'] - pivots_df['PIVOT']
        pivots_df['H3_P'] = pivots_df['H3'] - pivots_df['PIVOT']
        pivots_df['H2_P'] = pivots_df['H2'] - pivots_df['PIVOT']
        pivots_df['H1_P'] = pivots_df['H1'] - pivots_df['PIVOT']

        pivots_df['L1_P'] = pivots_df['PIVOT'] - pivots_df['L1']
        pivots_df['L2_P'] = pivots_df['PIVOT'] - pivots_df['L2']
        pivots_df['L3_P'] = pivots_df['PIVOT'] - pivots_df['L3']
        pivots_df['L4_P'] = pivots_df['PIVOT'] - pivots_df['L4']
        pivots_df['L5_P'] = pivots_df['PIVOT'] - pivots_df['L5']
        pivots_df['L6_P'] = pivots_df['PIVOT'] - pivots_df['L6']

        print("Pivot to H6 average: {}".format(pivots_df['H6_P'].mean()))
        print("Pivot to H5 average: {}".format(pivots_df['H5_P'].mean()))
        print("Pivot to H4 average: {}".format(pivots_df['H4_P'].mean()))
        print("Pivot to H3 average: {}".format(pivots_df['H3_P'].mean()))
        print("Pivot to H2 average: {}".format(pivots_df['H2_P'].mean()))
        print("Pivot to H1 average: {}".format(pivots_df['H1_P'].mean()))
        print("PIVOT mean: {}".format(pivots_df['PIVOT'].mean()))
        print("Pivot to L1 average: {}".format(pivots_df['L1_P'].mean()))
        print("Pivot to L2 average: {}".format(pivots_df['L2_P'].mean()))
        print("Pivot to L3 average: {}".format(pivots_df['L3_P'].mean()))
        print("Pivot to L4 average: {}".format(pivots_df['L4_P'].mean()))
        print("Pivot to L5 average: {}".format(pivots_df['L5_P'].mean()))
        print("Pivot to L6 average: {}".format(pivots_df['L6_P'].mean()))

    def do_stats(self, line):
        """
        Some stats
        """
        print("""
        ++++++++++++++++++++++++
        Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)

        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))

        print("How many times the range has crossed the Pivots")
        filter_df = self.pivots_df[(self.pivots_df.Low < self.pivots_df.PIVOT) & (self.pivots_df.PIVOT < self.pivots_df.High)]
        pivot_cross_count = len(filter_df)
        print("{}\t{}%".format(pivot_cross_count, pivot_cross_count*100/trades_count))

        filter_open_above_pivot_df = self.pivots_df[(self.pivots_df.PIVOT < self.pivots_df.Open)]
        filter_open_below_pivot_df = self.pivots_df[(self.pivots_df.PIVOT > self.pivots_df.Open)]
        filter_open_equals_pivot_df = self.pivots_df[(self.pivots_df.PIVOT == self.pivots_df.Open)]

        filter_open_above_pivot_count = len(filter_open_above_pivot_df)
        filter_open_below_pivot_count = len(filter_open_below_pivot_df)
        filter_open_equals_pivot_count = len(filter_open_equals_pivot_df)

        print("Open above pivot: {} {}".format(filter_open_above_pivot_count, filter_open_above_pivot_count*100/trades_count))
        print("Open below pivot: {} {}".format(filter_open_below_pivot_count, filter_open_below_pivot_count*100/trades_count))
        print("Open equal pivot: {} {}".format(filter_open_equals_pivot_count, filter_open_equals_pivot_count*100/trades_count))

        print("""
        +++++++++++ GENERIC STATS H3 to L1 and L3 to H1 +++++++++++
        """)
        rev_trades_df = self.pivots_df[(self.pivots_df.H3 > self.pivots_df.Low) | (self.pivots_df.L3 < self.pivots_df.High)]
        rev_trades_count = len(rev_trades_df)
        print("No of trades: {} {}%".format(rev_trades_count, rev_trades_count*100/trades_count))

        print("H3 to L1")
        filter_df = self.pivots_df[(self.pivots_df.H3 < self.pivots_df.High) & (self.pivots_df.L1 > self.pivots_df.Low)].copy()
        filter_df_count = len(filter_df)
        print("{}\t{}%".format(filter_df_count, filter_df_count*100/rev_trades_count))

        filter_df['H3_L1_points'] = filter_df['H3'] - filter_df['L1']
        filter_df['H3_H4_points'] = filter_df['H4'] - filter_df['H3']
        print("""
        ===================
        Target points stat
        ===================
        """)
        print(filter_df['H3_L1_points'].mean())

        print("""
        ===================
        Stoploss points stat
        ===================
        """)
        print(filter_df['H3_H4_points'].mean())


        print("L3 to H1")
        filter_df = self.pivots_df[(self.pivots_df.L3 > self.pivots_df.Low) & (self.pivots_df.H1 < self.pivots_df.High)].copy()
        filter_df_count = len(filter_df)
        print("{}\t{}%".format(filter_df_count, filter_df_count*100/rev_trades_count))
        filter_df['L3_H1_points'] = filter_df['H1'] - filter_df['L3']
        filter_df['L3_L4_points'] = filter_df['L3'] - filter_df['L4']

        print("""
        ===================
        Target points stat
        ===================
        """)
        print(filter_df['L3_H1_points'].mean())

        print("""
        ===================
        Stoploss points stat
        ===================
        """)
        print(filter_df['L3_L4_points'].mean())

    def do_stats_h2h4_l2l4(self, line):
        """
        Display stats for price open between h2h4 and l2l4
        """
        print("""
        ++++++++++++++++++++++++
        Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)

        trades_count = len(self.pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))

        print("""
        +++++++++++ L3-H3 STATS +++++++++++
        """)
        print("How many times Price opened between H2 and H4 or L2 and L4")
        filter_df = self.pivots_df[((self.pivots_df.H2 < self.pivots_df.Open) & (self.pivots_df.Open < self.pivots_df.H4))
                | ((self.pivots_df.L4 < self.pivots_df.Open) & (self.pivots_df.Open < self.pivots_df.L2))].copy()
        count = len(filter_df)
        print("{}\t{}%".format(count, count*100/trades_count))

        print("How many times Price ranged across H3 and L3")
        range_h3l3_df = filter_df[(filter_df.L3 > filter_df.Low) & (filter_df.H3 < filter_df.High)].copy()
        range_h3l3_count = len(range_h3l3_df)
        print("{}\t{}%".format(range_h3l3_count, range_h3l3_count*100/count))

    def do_stats_h2h3_5_l2l3_5(self, line):
        """
        Display stats for price open between h2,h3.5 and l2,l3.5
        """
        print("""
        ++++++++++++++++++++++++
        Stats for %s
        ++++++++++++++++++++++++
        """ % self.scrip)

        pivots_df = self.pivots_df.copy()
        trades_count = len(pivots_df)
        print("{} trades count:\t{}".format(self.scrip, trades_count))

        pivots_df['H3_5'] = (pivots_df['H3'] + pivots_df['H4'])/2
        pivots_df['L3_5'] = (pivots_df['L3'] + pivots_df['L4'])/2
        print("""
        +++++++++++ L3-H3 STATS +++++++++++
        """)
        print("How many times Price opened between H2 and H3_5 or L2 and L3_5")
        filter_df = pivots_df[((pivots_df.H2 < pivots_df.Open) & (pivots_df.Open < pivots_df.H3_5))
                | ((pivots_df.L3_5 < pivots_df.Open) & (pivots_df.Open < pivots_df.L2))].copy()
        count = len(filter_df)
        print("{}\t{}%".format(count, count*100/trades_count))

        print("How many times Price ranged across H3 and L3")
        range_h3l3_df = filter_df[(filter_df.L3 > filter_df.Low) & (filter_df.H3 < filter_df.High)].copy()
        range_h3l3_count = len(range_h3l3_df)
        print("{}\t{}%".format(range_h3l3_count, range_h3l3_count*100/count))





if __name__ == '__main__':
    app = REPL()
    app.cmdloop()
