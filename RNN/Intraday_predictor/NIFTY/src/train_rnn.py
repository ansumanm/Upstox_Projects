import numpy as np
import pandas as pd

X_train_df = pd.read_csv('../data/train_X.csv', header=None)
Y_train_df = pd.read_csv('../data/train_Y.csv', header=None)

"""
Lets say, we take in to account last N days of data. Our first input will be
0 to N-1, 2nd input will be 1 to N and our last set will be len(df)-N to len(df)
"""
N = 60
no_of_records = len(Y_train_df)

X_train = []
Y_train = []

"""
Think of it like a sliding window containing N records.
"""
for i in range(N, no_of_records):
    X_train.append(X_train_df.values[i-N:i, :])
    Y_train.append(Y_train_df.values[i, :])

# List to np array
X_train, Y_train = np.array(X_train), np.array(Y_train)

"""
X_train.shape: (2717, 60, 6)
Y_train.shape: (2717, 3)
"""

# Build the RNN
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout

# Initialise the RNN
regressor = Sequential()

# First LSTM Layer: units = (parameters)^2 parameters=8 (OHLC,V,DV,Ot, VWAP)
regressor.add(LSTM(units = 64, return_sequences = True,
    input_shape=(N,6)))
regressor.add(Dropout(0.2))

# 2nd LSTM layer
regressor.add(LSTM(units = 64, return_sequences = True))
regressor.add(Dropout(0.2))

# 3nd LSTM layer
regressor.add(LSTM(units = 64, return_sequences = True))
regressor.add(Dropout(0.2))

# 4th LSTM layer
regressor.add(LSTM(units = 64, return_sequences = False))
regressor.add(Dropout(0.2))

# Add the output layer. We are predicting HLC
regressor.add(Dense(units = 3))

# Compile
regressor.compile(optimizer = 'adam', loss = 'mean_squared_error')

# Fit
regressor.fit(X_train, Y_train, epochs = 100, batch_size = 32)

# Save the model
regressor.save('../data/model.hdf5')

