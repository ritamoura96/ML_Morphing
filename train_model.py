import pandas as pd
from utils_train import *

df = pd.read_pickle('dataset.pkl')

number_nodes = len(df['node_number'].unique())
number_frames = len(df['time'].unique())
number_simulations = len(df['simulation'].unique())
simulation_len = number_nodes * number_frames

X_train, y_train, X_test, y_test, scaler_fit = data_pre_processing(df, number_nodes, number_frames, features, coords, target, case)

models_to_train = load_models_to_train(X_train, y_train)

results = []

for model in models_to_train:

    m = model.get('model')
    name = model.get('name')
    params = model.get('parameters')
    
    # define cross validation
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    # use grid search method
    grid = GridSearchCV(m, params, cv=kf, scoring='neg_mean_absolute_error', verbose=10, n_jobs=16)

    # fit model
    grid.fit(X_train, y_train)
    model_fit = grid.best_estimator_

    # save best model
    joblib.dump(model_fit, f'{name}.joblib')

    # predict 
    all_predictions = make_predictions(case, name, X_test, scaler_fit, model_fit, simulation_len, number_frames, number_nodes, time_step, coords, features)

    # evaluate 
    mae = round(mean_absolute_error(y_test, all_predictions), 3)
    mae_x = round(mean_absolute_error(y_test[:, 0], all_predictions[:, 0]), 3)
    mae_y = round(mean_absolute_error(y_test[:, 1], all_predictions[:, 1]), 3)
    mae_z = round(mean_absolute_error(y_test[:, 2], all_predictions[:, 2]), 3)   
    mape = round(mean_absolute_percentage_error(y_test, all_predictions), 6)

    model_results = [name, mae, mae_x, mae_y, mae_z, mape]
    results.append(model_results)

df_results = pd.DataFrame(data=results, columns=['Model', 'MAE', 'MAE_x', 'MAE_y', 'MAE_z', 'MAPE'])
df_results.to_csv(f'results.csv')
