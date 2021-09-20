import numpy as np
import pandas as pd

df = pd.read_csv('../data/banknifty.csv')

df.set_index('Date', inplace=True)

df.index = pd.to_datetime(df.index)

df['Range'] = df['High'] - df['Low']
df['O2L'] = df['Open'] - df['Low']
df['O2H'] = df['High'] - df['Open']

dfp = pd.DataFrame()
dfp['Rangep'] = df['Range']*100/df['Open']
dfp['O2Lp'] = df['O2L']*100/df['Open']
dfp['O2Hp'] = df['O2H']*100/df['Open']

print("""
        RANGE
        """)
print('median   ', df['Range'].median())
# print('mode     ', df['Range'].mode())
print(df['Range'].describe())

# df['Rangep'].hist(bins=10, density=False, cumulative=False, histtype='step').figure.savefig('daily_range.png')

print("""
        Open to Low
        """)
print('median   ', df['O2L'].median())
# print('mode     ', weekly_df['O2C'].mode())
print(df['O2L'].describe())

# weekly_df['O2C'].hist(bins=10, density=True, cumulative=True).figure.savefig('o2c.png')
# df['O2Lp'].hist(bins=10, density=False, cumulative=False, histtype='step').figure.savefig('daily_o2l.png')

print("""
        Open to High
        """)
print('median   ', df['O2H'].median())
# print('mode     ', weekly_df['O2C'].mode())
print(df['O2H'].describe())

# weekly_df['O2C'].hist(bins=10, density=True, cumulative=True).figure.savefig('o2c.png')
# df['O2Hp'].hist(bins=10, density=False, cumulative=False, histtype='step').figure.savefig('daily_o2h.png')
# dfp.hist(bins='auto', density=False, cumulative=False).figure.savefig('daily_stats.png')
bins=[.5, 1, 1.50, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10, 10.5] 
# dfp['Rangep'].hist(bins=bins, density=False, cumulative=False, rwidth=0.75).figure.savefig('daily_rangep.png')
# dfp['O2Hp'].hist(bins=bins, density=False, cumulative=False, rwidth=0.75).figure.savefig('daily_o2hp.png')
dfp['O2Lp'].hist(bins=bins, density=False, cumulative=False, rwidth=0.75).figure.savefig('daily_o2lp.png')

"""
for p in np.nditer(plot,flags=["refs_ok"]):
"""
