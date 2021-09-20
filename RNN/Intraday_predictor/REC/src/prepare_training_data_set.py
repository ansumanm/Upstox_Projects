"""
Open raw data and reformat it according to our training set.
"""
import numpy as np
import pandas as pd

df = pd.read_csv('../data/recltd.csv')

"""
Index(['Date', 'Symbol', 'Series', 'Prev Close', 'Open', 'High', 'Low', 'Last',
       'Close', 'VWAP', 'Volume', 'Turnover', 'Trades', 'Deliverable Volume',
       '%Deliverble'],
      dtype='object')
We drop the following columns from our training data.
Date
Symbol
Series
Prev Close
Last
Turnover
Trades
%Deliverable
"""
df.drop(['Date', 'Symbol', 'Series', 'Prev Close', 'Last',  'Turnover', 'Trades', '%Deliverble'], axis=1, inplace=True)

"""
We are left with the following columns
Index(['Open', 'High', 'Low', 'Close', 'VWAP', 'Volume', 'Deliverable Volume'], dtype='object')
"""
"""
Our training parameters are the following columns and the next day open price.
We try to predict the next day's High, Low and Close values.
"""

Open_df = df[['Open']]
Open_df = Open_df.iloc[1:,] # Delete the first row
Open_df.loc[len(Open_df) + 1] = 0

# Now append the Open_df to the df
df['Open_tomorrow'] = Open_df.values

"""
Before we proceed further, lets scale the dataset first.
SCALING the dataset:
We have two types of data: Price and Volume
We will use different scalers for Price and Volume
df[df.columns] = scaler.fit_transform(df[df.columns])
"""
from sklearn.preprocessing import MinMaxScaler
price_scaler = MinMaxScaler()
vol_scaler = MinMaxScaler()

price_columns = ['Open', 'High', 'Low', 'Close', 'VWAP', 'Open_tomorrow']
volume_columns = ['Volume', 'Deliverable Volume']
df[price_columns] = price_scaler.fit_transform(df[price_columns])
df[volume_columns] = vol_scaler.fit_transform(df[volume_columns])

train_Y = df
# Drop the last row from the df
df = df[:-1]

# Prepare the expected dataset
# We are predicting High, Low and Close
# So we drop rest of the columns
# Also, We drop the first row.
train_Y.drop(['Open', 'VWAP', 'Volume', 'Deliverable Volume', 'Open_tomorrow'], axis=1, inplace=True)
train_Y = train_Y.iloc[1:,] # Delete the first row

# Now we have two data frames.
# df: Input dataframe (X)
# train_Y: Predict dataframe (Y)

"""
Write the training data to csv files.
Write the scalers to files as pickle objects
"""
import pickle

with open('../data/price_scaler.pkl', 'wb') as f:
    pickle.dump(price_scaler, f)

with open('../data/vol_scaler.pkl', 'wb') as f:
    pickle.dump(vol_scaler, f)

df.to_csv('../data/train_X.csv', header=False, index=False)
train_Y.to_csv('../data/train_Y.csv', header=False, index=False)

