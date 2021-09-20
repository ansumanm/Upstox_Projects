import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('../data/banknifty.csv')

df.set_index('Date', inplace=True)

df.index = pd.to_datetime(df.index)

weekly_df = pd.DataFrame()
weekly_df['Open'] = df.Open.resample('W-FRI').first()
weekly_df['High'] = df.High.resample('W-FRI').max()
weekly_df['Low'] = df.Low.resample('W-FRI').min()
weekly_df['Close'] = df.Close.resample('W-FRI').last()

weekly_df['Range'] = weekly_df['High'] - weekly_df['Low']
weekly_df['Range_per'] = (weekly_df['Range']*100)/weekly_df['Open']
weekly_df['O2C'] = weekly_df['Open'] - weekly_df['Close']
weekly_df['O2C_per'] = (weekly_df['O2C']*100)/weekly_df['Open']

print("""
        RANGE
        """)
print('median   ', weekly_df['Range'].median())
print('mode     ', weekly_df['Range'].mode())
print(weekly_df['Range'].describe())

# weekly_df['Range'].hist(bins=10, density=True, cumulative=True).figure.savefig('range.png')

print("""
        Open to Close
        """)
print('median   ', weekly_df['O2C'].median())
# print('mode     ', weekly_df['O2C'].mode())
print(weekly_df['O2C'].describe())

# https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.hist.html
# weekly_df['O2C'].hist(bins=10, density=True, cumulative=True).figure.savefig('o2c.png')
# bins=weekly_df['O2C'].quantile([0,0.1,0.20,0.30,0.40,0.5,0.6,0.70,0.80,0.90,1]).to_list()
weekly_df['O2C'].hist(bins='auto', density=False, cumulative=False, rwidth=0.9).figure.savefig('weekly_o2c.png')

# weekly_df[['O2C_per']].plot(kind='hist',bins=[-10, -7.5, -5, -2.5, 0, 2.5, 5, 7.5, 10], rwidth=0.9, density=True)
# plt.show()

plt.savefig('output.png')
