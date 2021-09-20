#!/home/mansuman/venv_angel/bin/python

import numpy as np
import pandas as pd

df = pd.read_csv('../data/banknifty.csv')

df.set_index('Date', inplace=True)

df.index = pd.to_datetime(df.index)


print(df.columns)
