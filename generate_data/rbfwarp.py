import numpy as np
import sys


def rbf(d, r):
    """

    :param d:
    :param r:
    :return:
    """
    ko = np.exp(-d/(r**2))
    return ko


def ThinPlate(ri):
    """

    :param ri:
    :return:
    """
    r1i = np.where(ri == 0, sys.float_info[3], ri)  # corresponds to the smallest positive float value - same as realmin in matlab
    ko = np.multiply(ri, np.log(r1i))
    return ko


def calculate_transformation_matrix(fixed_moving_nodes, new_nodes, method):

    # define length of fixed/moving nodes and new nodes
    len_new_nodes = len(new_nodes)
    len_fixed_moving_nodes = len(fixed_moving_nodes)

    # create matrix with length dimensions
    K = np.zeros((len_new_nodes, len_fixed_moving_nodes))

    # calculate distance from moving nodes to new nodes
    for i in range(len_new_nodes):
        distance = fixed_moving_nodes - np.ones((len_fixed_moving_nodes, 1)) * new_nodes[i, :]
        K[:, i] = np.sum(distance ** 2, axis=1)

    # K matrix suffers warping method - smoothed values that approximates the input values
    if method == 'gau':
        r = 1
        K = rbf(K, r)
    elif method == 'thin':
        K = ThinPlate(K)

    # operations to obtain old nodes matrix to be used in the equation system
    P = np.insert(fixed_moving_nodes, 0, 1, axis=1)  # addition of 1's to account for translation component
    L1 = np.concatenate((K, P), axis=1)
    P_transpose = np.transpose(P)
    L2 = np.concatenate((P_transpose, np.zeros((4, 4))), axis=1)  # include homogeneous coordinates
    input_matrix = np.concatenate((L1, L2), axis=0)

    # definition of new nodes matrix in dimensions accordingly to old nodes matrix to be used in the system
    output_matrix = np.concatenate((new_nodes, np.zeros((4, 3))), axis=0)

    # solve system of equations to obtain transformation matrix
    transformation_matrix = np.linalg.solve(input_matrix, output_matrix)

    return transformation_matrix


def calculate_new_nodes(transformation_matrix, complete_mesh, new_nodes, method):

    len_complete_mesh = len(complete_mesh)
    len_new_nodes = len(new_nodes)
    K = np.zeros((len_complete_mesh, len_new_nodes))

    for i in range(len_new_nodes):
        distance = complete_mesh - np.ones((len_complete_mesh, 1))*new_nodes[i, :]
        K[:, i] = np.sum(distance ** 2, axis=1)

    if method == 'gau':
        r = 1
        K = rbf(K, r)
    elif method == 'thin':
        K = ThinPlate(K)

    P = np.insert(complete_mesh, 0, 1, axis=1)
    input_matrix = np.concatenate((K, P), axis=1)

    output_matrix = np.matmul(input_matrix, transformation_matrix)

    return output_matrix


def rbfwarp3d(complete_mesh, fixed_moving_nodes, new_nodes, method):

    transformation_matrix = calculate_transformation_matrix(fixed_moving_nodes, new_nodes, method)
    new_nodes_complete_mesh = calculate_new_nodes(transformation_matrix, complete_mesh, new_nodes, method)

    return new_nodes_complete_mesh


