import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('../data/nifty.csv')

df.set_index('Date', inplace=True)

df.index = pd.to_datetime(df.index)

monthly_df = pd.DataFrame()
monthly_df['Open'] = df.Open.resample('M').first()
monthly_df['High'] = df.High.resample('M').max()
monthly_df['Low'] = df.Low.resample('M').min()
monthly_df['Close'] = df.Close.resample('M').last()

monthly_df['Range'] = monthly_df['High'] - monthly_df['Low']
monthly_df['Range_per'] = (monthly_df['Range']*100)/monthly_df['Open']
monthly_df['O2C'] = monthly_df['Open'] - monthly_df['Close']
monthly_df['O2C_per'] = (monthly_df['O2C']*100)/monthly_df['Open']

print("""
        RANGE
        """)
print('median   ', monthly_df['Range'].median())
print('mode     ', monthly_df['Range'].mode())
print(monthly_df['Range'].describe())
monthly_df['Range'].hist(bins='auto', density=False, cumulative=False).figure.savefig('range.png')

print("""
        Open to Close
        """)
print('median   ', monthly_df['O2C'].median())
# print('mode     ', monthly_df['O2C'].mode())
print(monthly_df['O2C'].describe())

# https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.hist.html
# monthly_df['O2C'].hist(bins=10, density=True, cumulative=True).figure.savefig('o2c.png')
# bins=monthly_df['O2C'].quantile([0,0.1,0.20,0.30,0.40,0.5,0.6,0.70,0.80,0.90,1]).to_list()
# monthly_df['O2C'].hist(bins='auto', density=False, cumulative=False, rwidth=0.9).figure.savefig('monthly_o2c.png')

monthly_df[['O2C_per']].plot(kind='hist',bins=[-10, -7.5, -5, -2.5, 0, 2.5, 5, 7.5, 10], rwidth=0.9, density=True)
# plt.show()

plt.savefig('o2c_per.png')
