import os
import pandas as pd
from os.path import exists

from utils import *

start_dir = os.getcwd()

number_simulations = 6896  # change according to the total number of simulations
number_nodes = 5711  # (real value - 1) because python
step = 8  # select step to retrieve results

constitutive_parameters_row = 15
nodes_row = 1

df_list = []
dataset = pd.DataFrame()

for i in range(number_simulations):

    file_exists = exists(f'{start_dir}/sim_{i}/results_coordinates_AllFrames.csv')

    if file_exists:

        # ==================================== IMPORT FILES ======================================= #

        final_coordinates = pd.read_csv(f'{start_dir}/sim_{i}/results_coordinates_AllFrames.csv', header=None)
        # final_displacements = pd.read_csv(f'{start_dir}/sim_{i}/results_displacement_AllFrames.csv', header=None)
        # stresses = pd.read_csv(f'{start_dir}/sim_{i}/results_max_principal_stresses_AllFrames.csv', header=None)

        with open(f'{start_dir}/sim_{i}/muscles_info.inp') as f:
            muscles_info_file = f.readlines()

        with open(f'{start_dir}/sim_{i}/material_properties.inp') as g:
            mat_props_file = g.readlines()

        with open(f'{start_dir}/sim_{i}/input_file.sta') as f:
            sta_file = f.readlines()[5:-2]

        df_aux = pd.DataFrame()
        df_aux['simulation'] = []
        df_aux['node_number'] = final_coordinates[0][(number_nodes+1)*(step-1) : (number_nodes+1)*step]
        df_aux['simulation'] = i

        # ==================================== GET DATA ======================================= #

        df_aux = get_data_from_inp(muscles_info_file, mat_props_file, df_aux, number_nodes, nodes_row,
                                   constitutive_parameters_row)

        # only use nodes from selected pelvic floor path

        stretch_path = []
        with open('pfm_nodes_path.txt') as f:
            for line in f:
                stretch_path.append(int(line.rstrip()))

        number_nodes_path = len(stretch_path)

        stretch = df_aux['node_number'].isin(stretch_path)
        df_aux = df_aux[stretch]
        df_aux['node_position'] = df_aux['node_number'].map(lambda x: stretch_path.index(x))
        df_aux.sort_values(by='node_position', inplace=True)

        # get data from step 8 and 9 sta file and organize final sta

        final_sta, cleaned_sta_step8 = get_data_from_sta(sta_file)

        # organize final coordinates results file

        final_coordinates_organized = clean_results_coordinates(final_coordinates, number_nodes, cleaned_sta_step8,
                                                                stretch_path, number_nodes_path)

        # join sta and results information and resample

        df_resampled_all = resample(final_sta, number_nodes_path, final_coordinates_organized)

        # create final dataframe

        final_sim_dataframe = df_resampled_all.copy()
        columns_name = {1: 'x_final', 2: 'y_final', 3: 'z_final'}
        final_sim_dataframe.rename(columns=columns_name, inplace=True)
        cols = ['time', 'node_position', 'x_final', 'y_final', 'z_final']
        final_sim_dataframe = final_sim_dataframe[cols]
        final_sim_dataframe = final_sim_dataframe.drop(['node_position'], axis=1)

        df_aux_all_frames = pd.concat([df_aux]*(len(final_sim_dataframe)//number_nodes_path))

        df_aux_all_frames.reset_index(inplace=True, drop=True)
        final_sim_dataframe.reset_index(inplace=True, drop=True)

        dataset_by_simulation = pd.concat([df_aux_all_frames, final_sim_dataframe], axis=1)

        dataset = pd.concat([dataset, dataset_by_simulation], axis=0)

dataset.reset_index(inplace=True, drop=True)
dataset.to_csv('dataset.csv', index=False)
dataset.to_pickle('dataset.pkl')


