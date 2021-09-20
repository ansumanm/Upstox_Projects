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

"""
We evaluate our model on last 20 days of data.
So we trim our dataset to last 20+60 days of data.
"""
X_train_df = X_train_df.tail(80)
Y_train_df = Y_train_df.tail(80)
no_of_records = 80

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
X_train.shape: (2717, 60, 8)
Y_train.shape: (2717, 3)
"""
# Scale our data with the scalers we trained with
from sklearn.preprocessing import MinMaxScaler
import pickle

# Building the RNN
from keras.models import load_model
regressor = load_model('../data/model.hdf5')

# Evaluate model.
scores = regressor.evaluate(X_train, Y_train)
print(scores)
print(type(scores))
print(regressor.metrics_names)

print("""
        {}
        """.format(regressor.layers[0].get_weights()))
