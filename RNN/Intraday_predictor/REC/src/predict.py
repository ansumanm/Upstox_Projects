"""
Improvement plans: Get the error rate and using that come up with the range that the HLC can take.
"""
import numpy as np
import pandas as pd

N = 60
today_open_price = 143.55

df = pd.read_csv('../data/stock_data.csv')
df = df.iloc[-N:]
df.drop(['Date', 'Symbol', 'Series', 'Prev Close', 'Last',  'Turnover', 'Trades', '%Deliverble'], axis=1, inplace=True)

Open_df = df[['Open']]
Open_df = Open_df.iloc[1:,] # Delete the first row

Open_df.loc[N-1] = today_open_price
df['Open_tomorrow'] = Open_df.values

# Scale our data with the scalers we trained with
from sklearn.preprocessing import MinMaxScaler
import pickle

with open('../data/price_scaler.pkl', 'rb') as f:
    price_scaler = pickle.load(f)

with open('../data/vol_scaler.pkl', 'rb') as f:
    vol_scaler = pickle.load(f)

price_columns = ['Open', 'High', 'Low', 'Close', 'VWAP', 'Open_tomorrow']
volume_columns = ['Volume', 'Deliverable Volume']
df[price_columns] = price_scaler.transform(df[price_columns])
df[volume_columns] = vol_scaler.transform(df[volume_columns])

# Building the RNN
from keras.models import load_model
regressor = load_model('../data/model.hdf5')

X_test = df.values
X_test = np.reshape(X_test, (1, X_test.shape[0], X_test.shape[1]))
predicted_set = regressor.predict(X_test)
print(predicted_set)
print(type(predicted_set))

High = predicted_set[0][0]
Low = predicted_set[0][1]
Close = predicted_set[0][2]
Y_test = [[0, High, Low, Close, 0, 0]]
print(Y_test)
Y_test = price_scaler.inverse_transform(Y_test)
print(Y_test)
