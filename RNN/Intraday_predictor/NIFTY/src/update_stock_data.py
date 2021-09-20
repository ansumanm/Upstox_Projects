#!/home/mansuman/venv_angel/bin/python

from datetime import date
from datetime import datetime as dt
from datetime import timedelta

from nsepy import get_history
import numpy as np
import pandas as pd

"""
Download missing data
"""
df = pd.read_csv('../data/nifty.csv')

# Get the last date till we have data.
last_data_date_str = df.iloc[-1].Date
last_data_date = dt.strptime(last_data_date_str, '%Y-%m-%d')
from_date = last_data_date.date() + timedelta(days=1)
# to_date = date.today() - timedelta(days=1)
to_date = date.today()

bnf = get_history(symbol='NIFTY 50',
        start=from_date, 
        end=to_date,
        index=True)
bnf = bnf.reset_index()

updated_df = pd.concat([df, bnf])
updated_df = updated_df.reset_index(drop=True)

# updated_df contains data till date. Updated the csv file.
updated_df.to_csv('../data/nifty.csv', header=True, index=False)
