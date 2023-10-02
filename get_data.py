import os
import pandas as pd
from os.path import exists

from utils import *

start_dir = os.getcwd()

number_simulations = 1  # change according to the total number of simulations
number_nodes = 5711  # (real value - 1) because python
step = 8  # select step to retrieve results

constitutive_parameters_row = 15
nodes_row = 1

df_list = []

for i in range(number_simulations):

    file_exists = exists(f'{start_dir}/sim_{i}/results_coordinates.csv')

    if file_exists:

        final_coordinates = pd.read_csv(f'{start_dir}/sim_{i}/results_coordinates_AllFrames.csv', header=None)
        final_displacements = pd.read_csv(f'{start_dir}/sim_{i}/results_displacement_AllFrames.csv', header=None)
        # stresses = pd.read_csv(f'{start_dir}/sim_{i}/results_max_principal_stresses_AllFrames.csv', header=None)

        df_aux = pd.DataFrame()
        df_aux['simulation'] = []

        df_aux['node_number'] = final_coordinates[0][(number_nodes+1)*(step-1) : (number_nodes+1)*step]
        df_aux['simulation'] = i

        # ==================================== FROM MUSCLES INP ======================================= #

        with open(f'{start_dir}/sim_{i}/muscles_info.inp') as f:
            muscles_info_file = f.readlines()

        coord_x = []
        coord_y = []
        coord_z = []

        for j in range(number_nodes + 1):

            arr = muscles_info_file[j + nodes_row]
            new_arr_x = list(map(float, arr.split(',')))[1]
            new_arr_y = list(map(float, arr.split(',')))[2]
            new_arr_z = list(map(float, arr.split(',')))[3]
            coord_x.append(new_arr_x)
            coord_y.append(new_arr_y)
            coord_z.append(new_arr_z)

        df_aux['x_initial'] = coord_x
        df_aux['y_initial'] = coord_y
        df_aux['z_initial'] = coord_z

        # ============================== FROM MATERIAL PROPERTIES INP ================================= #

        with open(f'{start_dir}/sim_{i}/material_properties.inp') as g:
            mat_props_file = g.readlines()

        df_aux['c'] = float(mat_props_file[constitutive_parameters_row].split('=')[1])
        df_aux['b'] = float(mat_props_file[constitutive_parameters_row + 1].split('=')[1])

        df_aux.reset_index(inplace=True, drop=True)

        # only use nodes from selected pelvic floor path

        stretch_path = [15, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323,
                        324, 325, 326, 327, 328, 329, 330, 331, 16, 542, 541, 540, 539, 538, 537, 536, 535, 534, 533,
                        532, 531, 530, 529, 528, 527, 526, 525, 524, 523, 522, 521, 520, 519, 518, 517, 19]

        stretch = df_aux['node_number'].isin(stretch_path)
        df_aux = df_aux[stretch]
        df_aux['node_position'] = df_aux['node_number'].map(lambda x: stretch_path.index(x))
        df_aux.sort_values(by='node_position', inplace=True)

        # ==================================== FROM STA FILE ======================================= #

        with open(f'{start_dir}/sim_{i}/input_file.sta') as f:
            sta_file = f.readlines()[5:-2]

        sta8, sta9 = get_data_from_sta(sta_file)

        # resampled_step8 = resample_step(sta8)

        # eliminate the first frame of each step (5712 * 2 nodes) -> abaqus saves extra frame at the beginning of each
        # step equal to the last frame of the previous step

        final_coordinates = final_coordinates.iloc[number_nodes + 1:]
        final_coordinates = final_coordinates.drop(
            final_coordinates.index[len(sta8) * (number_nodes + 1): len(sta8) * (number_nodes + 1) + number_nodes + 1])

        # keep only the nodes of the pelvic floor path

        nodes_path_coords = final_coordinates[0].isin(stretch_path)
        final_coords = final_coordinates[nodes_path_coords]
        final_coords['node_position'] = final_coords[0].map(lambda x: stretch_path.index(x))

        number_nodes_path = 55
        num_groups = len(final_coordinates) // number_nodes_path

        # group and sort by node position

        sorted_coordinates = pd.DataFrame()

        for group_index in range(num_groups):
            group_start = group_index * number_nodes_path
            group_end = (group_index + 1) * number_nodes_path
            group = final_coords.iloc[group_start:group_end]
            sorted_group = group.sort_values(by='node_position')
            sorted_coordinates = pd.concat([sorted_coordinates, sorted_group])

        sorted_coordinates.reset_index(inplace=True, drop=True)

        sorted_coordinates_step8 = sorted_coordinates.iloc[:len(sta8)*number_nodes_path]
        sorted_coordinates_step9 = sorted_coordinates.iloc[len(sta8) * number_nodes_path:]

        val = pd.Timestamp(year=2023, month=1, day=1, hour=0, minute=0, second=0)
        sta8[7] = sta8[7].astype(float)
        sta8['time'] = sta8[7].apply(lambda x: val + pd.DateOffset(seconds=x))
        sta8 = sta8.set_index('time')

        sta8 = sta8.reindex(sta8.index.repeat(number_nodes_path)).reset_index(drop=False)

        df_step8_to_resample = pd.concat([sta8, sorted_coordinates_step8.iloc[:, 1:5]], axis=1)

        final_resampling_all_nodes = []

        df_resampled_all = pd.DataFrame()
        for k in range(number_nodes_path):
            df_resampled = df_step8_to_resample[df_step8_to_resample['node_position'] == k]
            df_resampled = df_resampled.set_index('time')
            final_resampling_single_node = df_resampled.resample('10S').last()
            final_resampling_single_node['time'] = list(range(final_resampling_single_node.index.shape[0]))
            df_resampled_all = pd.concat([df_resampled_all, final_resampling_single_node])

        df_resampled_all.reset_index(inplace=True, drop=True)
        df_resampled_all = df_resampled_all.sort_values(['time', 'node_position'])

        # todo: drop das primeiras duas colunas
        # todo: alterar nomes das variáves
        # todo: organizar código por funções
        # todo: juntar step 9 com tudo o que está feito para o 8
        # todo: comentar e organizar código

        print()

