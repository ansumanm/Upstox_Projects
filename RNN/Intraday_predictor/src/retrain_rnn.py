import numpy as np
import pandas as pd


def VersionFile(file_spec, vtype='rename'):
    import os, shutil

    if os.path.isfile(file_spec):
        # or, do other error checking:
        if vtype not in ('copy', 'rename'):
            vtype = 'copy'

        # Determine root filename so the extension doesn't get longer
        n, e = os.path.splitext(file_spec)

        # Is e an integer?
        try:
            num = int(e)
            root = n
        except ValueError:
            root = file_spec

        # Find next available file version
        for i in range(10):
            new_file = '%s.%02d' % (root, i)
            if not os.path.isfile(new_file):
                if vtype == 'copy':
                    shutil.copy(file_spec, new_file)
                else:
                    os.rename(file_spec, new_file)
                return 1
    return 0

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
X_train.shape: (2717, 60, 8)
Y_train.shape: (2717, 3)
"""
# Scale our data with the scalers we trained with
from sklearn.preprocessing import MinMaxScaler
import pickle

# Building the RNN
from keras.models import load_model
regressor = load_model('../data/model.hdf5')

# Make a backup
VersionFile('../data/model.hdf5')

# Fit
regressor.fit(X_train, Y_train, epochs = 100, batch_size = 32)

# Save the model
regressor.save('../data/model.hdf5')

