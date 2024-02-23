import argparse
import math as m
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.svm import SVR
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from scikeras.wrappers import KerasRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

from nn_architecture import ANN_model

def load_models_to_train(X_train, y_train):

    models = [
        {
        'name': 'DT', 'model': DecisionTreeRegressor(),
        #'parameters': {'splitter': ['best', 'random'], 'max_depth': [5, 10, 50, 100, 200, None],
        #'min_samples_leaf': [0.3, 0.5, 1, 2, 3], 'min_samples_split': [0.5, 0.7, 1.0, 2]},
        #'name': 'RF', 'model': RandomForestRegressor(), 'parameters': {'n_estimators': [200], 'min_samples_leaf': [1], 'min_samples_split': [2]},
        #'name': 'XGBT', 'model': XGBRegressor(), 'parameters': {'max_depth': [15], 'multi_strategy': ['multi_output_tree']},

        #'name': 'SVR', 'model': SVR(), 'parameters': {'C': [3.0], 'gamma': ['scale'], 'kernel': ['rbf']},
        #'name': 'ANN', 'model': KerasRegressor(build_fn=ANN_model, verbose=1, learning_rate=None, activation_function=None,
        #                        num_neurons1=None, num_neurons2=None, num_neurons3=None, x_train=X_train, case=None),
        #                        'parameters': {'batch_size': [512], 'epochs': [100], 'learning_rate': [0.005],
        #                                       'activation_function': ['sigmoid'], 'num_neurons1': [200],
        #                                        'num_neurons2': [200], 'num_neurons3': [200], 'random_state': [42]},
        }

    ]
    return models


def data_pre_processing(df, number_nodes, number_frames, features, coords, target, case):

  # get features from dataset
  X = df.iloc[:, [0, 2, 3, 4, 5, 6, 7, 8, 9, 10]]

  # get target from dataset
  y = df.iloc[:, [11, 12, 13]]

  # stratification 
  X_feature = df.iloc[:, [0] + list(range(5, 9))]
  X_feature = X_feature.groupby('simulation').mean().values

  # group simulations before splitting
  X = np.array([X[k:k + number_nodes * number_frames] for k in range(0, len(X), number_nodes * number_frames)])
  y = np.array([y[k:k + number_nodes * number_frames] for k in range(0, len(y), number_nodes * number_frames)])

  # define % of data do train
  data_size = 0.1
  np.random.seed(42) 
  random_indices = np.random.choice(len(X), size=int(data_size * len(X)), replace=False)
  X = X[random_indices, :]
  y = y[random_indices, :]
  X_feature = X_feature[random_indices, 0]

  # definition of % of data for test set
  test_split = 0.1 
  # train test split with stratification 
  splitter = StratifiedShuffleSplit(n_splits=5, test_size=test_split, random_state=42)

  for train_index, test_index in splitter.split(np.zeros(X_feature.shape[0]), X_feature):
      X_train, X_test = X[train_index], X[test_index]
      y_train, y_test = y[train_index], y[test_index]

  # ungroup
  X_train = np.vstack(X_train)
  X_test = np.vstack(X_test)

  y_train = np.vstack(y_train)
  y_test = np.vstack(y_test)

  # data scaling 
  scaler = StandardScaler()
  scaler_fit = scaler.fit(X_train)
  X_train = scaler_fit.transform(X_train)

  return X_train, y_train, X_test, y_test, scaler_fit


def make_predictions(X_test, scaler_fit, model_fit):

    all_predictions = model_fit.predict(scaler_fit.transform(X_test))

    return all_predictions

