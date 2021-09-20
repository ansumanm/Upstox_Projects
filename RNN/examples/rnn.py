# Recurrent Neural Network

# Data Preprocessing
import numpy as np
import pandas as pd

# Import the training set
dataset_train = pd.read_csv('training_set.csv')

# An np array of open values
training_set = dataset_train.iloc[:, 1:2].values

# Feature scaling (standardization and normalization)
# If there is sigmoid function, using normalization is better
from sklearn.preprocessing import MinMaxScaler
sc = MinMaxScaler(feature_range = (0,1))
training_set_scaled = sc.fit_transform(training_set)

# Create a datastructure with 60 timesteps and 1 output.
X_train = []
Y_train = []
for i in range(60, 83):
    X_train.append(training_set_scaled[i-60:i, 0])
    Y_train.append(training_set_scaled[i, 0])

# Convert list to numpy array
X_train, Y_train = np.array(X_train), np.array(Y_train)

# Reshaping (add more variables)
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))


# Building the RNN
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout

# Initialze the RNN
regressor = Sequential()

# Add the first LSTM layer and some Dropout regularization
regressor.add(LSTM(units = 50, return_sequences = True, input_shape = (X_train.shape[1], 1)))

regressor.add(Dropout(0.2)) # Drop 20% neurons

# Add the 2nd  LSTM layer and some Dropout regularization. No need to specify the input_shapes here after adding first layer.
regressor.add(LSTM(units = 50, return_sequences = True))
regressor.add(Dropout(0.2)) # Drop 20% neurons

# Add the 3rd  LSTM layer and some Dropout regularization. No need to specify the input_shapes here after adding first layer.
regressor.add(LSTM(units = 50, return_sequences = True))
regressor.add(Dropout(0.2)) # Drop 20% neurons

# Add the 4th  LSTM layer and some Dropout regularization. No need to specify the input_shapes here after adding first layer.
regressor.add(LSTM(units = 50, return_sequences = False))
regressor.add(Dropout(0.2)) # Drop 20% neurons

# Add the output layer
regressor.add(Dense(units = 1))

# Compile the RNN
# Optimizer RMSProp is recommended.
regressor.compile(optimizer = 'adam', loss = 'mean_squared_error')

# Fitting the RNN to the training set.
regressor.fit(X_train, Y_train, epochs = 100, batch_size = 32)


# Making the predictions
dataset_test = pd.read_csv('test_set.csv')
real_test_set = dataset_train.iloc[:, 1:2].values

# Getting the predicted stock prices
# Don't change the actual test values
# Vertical concatenation
dataset_total = pd.concat((dataset_train['Open'], dataset_test['Open']),
        axis = 0)
inputs = dataset_total[len(dataset_total) - len(dataset_test) - 60:].values
inputs = inputs.reshape(-1, 1)
# Directly call transform instead of fit_transform so that we use the previous scale
inputs = sc.transform(inputs)

# Create a test datastructure with 60 timesteps and 1 output.
X_test = []
for i in range(60, 87):
    X_test.append(inputs[i-60:i, 0])

X_test = np.array(X_test)
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

# Predict
predicted_set = regressor.predict(X_test)
predicted_set = sc.inverse_transform(predicted_set)

print(predicted_set)


# Error calculation
"""
import math
from sklearn.metrics import mean_squared_error
rmse = math.sqrt(mean_squared_error(real_stock_price, predicted_stock_price))
"""

"""
Improving the model:-
Getting more training data: we trained our model on the past 5 years of the Google Stock Price but it would be even better to train it on the past 10 years.
Increasing the number of timesteps: the model remembered the stock prices from the 60 previous financial days to predict the stock price of the next day. That’s because we chose a number of 60 timesteps (3 months). You could try to increase the number of timesteps, by choosing for example 120 timesteps (6 months).
Adding some other indicators: if you have the financial instinct that the stock price of some other companies might be correlated to the one of Google, you could add this other stock price as a new indicator in the training data.
Adding more LSTM layers: we built a RNN with four LSTM layers but you could try with even more.
Adding more neurones in the LSTM layers: we highlighted the fact that we needed a high number of neurones in the LSTM layers to respond better to the complexity of the problem and we chose to include 50 neurones in each of our 4 LSTM layers. You could try an architecture with even more neurones in each of the 4 (or more) LSTM layers.
"""
"""
Parameter Tuning for Regression is the same as Parameter Tuning for Classification which you learned in Part 1 - Artificial Neural Networks, the only difference is that you have to replace:

    scoring = 'accuracy'  

    by:

    scoring = 'neg_mean_squared_error' 

    in the GridSearchCV class parameters.
"""
