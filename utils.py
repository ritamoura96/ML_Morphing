import re
import numpy as np
import pandas as pd


def get_data_from_inp(inp_file_muscles, inp_file_props, df_aux, number_nodes, nodes_row, constitutive_parameters_row):

    # muscles info

    coord_x = []
    coord_y = []
    coord_z = []

    for j in range(number_nodes + 1):
        arr = inp_file_muscles[j + nodes_row]
        new_arr_x = list(map(float, arr.split(',')))[1]
        new_arr_y = list(map(float, arr.split(',')))[2]
        new_arr_z = list(map(float, arr.split(',')))[3]
        coord_x.append(new_arr_x)
        coord_y.append(new_arr_y)
        coord_z.append(new_arr_z)

    df_aux['x_initial'] = coord_x
    df_aux['y_initial'] = coord_y
    df_aux['z_initial'] = coord_z

    # properties info

    df_aux['c'] = float(inp_file_props[constitutive_parameters_row].split('=')[1])
    df_aux['b'] = float(inp_file_props[constitutive_parameters_row + 1].split('=')[1])

    df_aux.reset_index(inplace=True, drop=True)

    return df_aux


def get_data_from_sta(sta_file):

    df_sta = pd.DataFrame([re.split(r'\s+', line.strip()) for line in sta_file])

    steps = ['8', '9']
    values = ['1U', '2U', '3U', '4U', '5U']
    columns_to_drop = [0, 1, 2, 3, 4, 5, 6]

    sta_step8 = df_sta[df_sta[0] == steps[0]].copy()
    mask_step8 = ~sta_step8[2].isin(values)  # ignore lines that have not completed the increment
    sta_step8 = sta_step8[mask_step8]
    sta_step8 = sta_step8.drop(columns_to_drop, axis=1)  # drop all columns except from time step and increment

    sta_step9 = df_sta[df_sta[0] == steps[1]].copy()
    mask_step9 = ~sta_step9[2].isin(values)
    sta_step9 = sta_step9[mask_step9]
    sta_step9 = sta_step9.drop(columns_to_drop, axis=1)

    sta_step8.reset_index(inplace=True, drop=True)
    sta_step9.reset_index(inplace=True, drop=True)

    columns_name = {7: 'time_step', 8: 'increment'}
    sta_step8.rename(columns=columns_name, inplace=True)
    sta_step9.rename(columns=columns_name, inplace=True)

    # operation to join with step 8

    sta_step9['time_step'] = sta_step9['time_step'].astype(float)
    sta_step9['time_step'] = sta_step9['time_step'] + 600

    final_sta = pd.concat([sta_step8, sta_step9], axis=0)

    return final_sta, sta_step8


def clean_results_coordinates(final_coordinates, number_nodes, cleaned_sta_step8, stretch_path, number_nodes_path):

    # final coordinates file has the final coordinates of each node of the pfm mesh for each frame

    # eliminate the first frame of each step (5712 * 2 nodes) -> abaqus saves extra frame at the beginning of each
    # step equal to the last frame of the previous step

    final_coordinates = final_coordinates.iloc[number_nodes + 1:]
    final_coordinates = final_coordinates.drop(
        final_coordinates.index[len(cleaned_sta_step8) * (number_nodes + 1): len(cleaned_sta_step8) *
                                                                             (number_nodes + 1) + number_nodes + 1])
    # keep only the nodes of the pelvic floor path

    nodes_path_coords = final_coordinates[0].isin(stretch_path)
    final_coords = final_coordinates[nodes_path_coords]
    final_coords['node_position'] = final_coords[0].map(lambda x: stretch_path.index(x))  # final coordinates of each node of the pfm belonging to the path for each frame

    group_size = number_nodes_path
    grouped = [final_coords[i:i + group_size] for i in range(0, len(final_coords), group_size)]
    sorted_groups = [group.sort_values(by='node_position') for group in grouped]
    final_coordinates_organized = pd.concat(sorted_groups, ignore_index=True)
    final_coordinates_organized.reset_index(inplace=True, drop=True)

    return final_coordinates_organized


def resample(final_sta, number_nodes_path, final_coordinates_organized):

    val = pd.Timestamp(year=2023, month=1, day=1, hour=0, minute=0, second=0)
    sta_to_resample = final_sta.copy()
    sta_to_resample['time_step'] = sta_to_resample['time_step'].astype(float)
    sta_to_resample['time'] = sta_to_resample['time_step'].apply(lambda x: val + pd.DateOffset(seconds=x))
    sta_to_resample = sta_to_resample.set_index('time')
    sta_to_resample = sta_to_resample.reset_index(drop=False)
    sta_to_resample = sta_to_resample.loc[sta_to_resample.index.repeat(number_nodes_path)]
    sta_to_resample = sta_to_resample.reset_index(drop=True)

    data_to_resample = pd.concat([sta_to_resample, final_coordinates_organized.iloc[:, 1:5]], axis=1)

    df_resampled_all = pd.DataFrame()

    for k in range(number_nodes_path):
        df_resampled = data_to_resample[data_to_resample['node_position'] == k]
        df_resampled = df_resampled.set_index('time')
        final_resampling_single_node = df_resampled.resample('10S').last()
        final_resampling_single_node['time'] = list(range(final_resampling_single_node.index.shape[0]))
        df_resampled_all = pd.concat([df_resampled_all, final_resampling_single_node])

    df_resampled_all.reset_index(inplace=True, drop=True)
    df_resampled_all = df_resampled_all.sort_values(['time', 'node_position'])

    df_resampled_all = df_resampled_all.drop(['time_step', 'increment'], axis=1)

    return df_resampled_all
