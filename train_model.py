import pandas as pd
from utils_train import *


df = pd.read_pickle('dataset_length.pkl')
number_nodes = len(df['node_number'].unique())
number_frames = len(df['time'].unique())

# Stratified train test split
X_train, X_test, y_train, y_test = split_train_test(df, number_nodes, number_frames)

# Scaling
X_train, X_test = scaling_data(X_train, X_test)

# Load models to train
models_to_train = load_models_to_train(X_train, y_train)
results = []

for model in models_to_train:

    # Get model and parameters
    m = model.get('model')
    name = model.get('name')
    params = model.get('parameters')

    # Cross-validation
    model_fit = hyperparameter_opt_cv(m, params, X_train, y_train)

    # Test
    mse, mse_x, mse_y, mse_z, mae, mae_x, mae_y, mae_z = test_model(X_test, y_test, model_fit)

    # Save model
    # dump(model_fit, f'/models/{name}.joblib')

    # Output results
    model_results = [name, mse, mse_x, mse_y, mse_z, mae, mae_x, mae_y, mae_z]
    results.append(model_results)

df_results = pd.DataFrame(data=results, columns=['Model', 'MSE', 'MSE_x', 'MSE_y', 'MSE_z',
                                                 'MAE', 'MAE_x', 'MAE_y', 'MAE_z'])
df_results.to_csv(f'train_results.csv')

print()