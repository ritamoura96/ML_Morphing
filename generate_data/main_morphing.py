import meshio
import trimesh
import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist
from scipy.interpolate import splprep, splev

from rbfwarp import rbfwarp3d

# define new coordinates for the moving nodes according to the diameter

def select_diameter(points, diameter_name, new_distance, node_1, node_2, pd, pos1, pos2):
    """

    :param points:
    :param diameter_name:
    :param new_distance:
    :param node_1:
    :param node_2:
    :param pd:
    :param pos1:
    :param pos2:
    :return:
    """
    if diameter_name == 'T' or diameter_name == 'IS':
        axis = 2
    elif diameter_name == 'AP':
        axis = 0

    a1 = points[node_1]
    a2 = points[node_2]
    # old_d = pdist([a1, a2])
    new_d = new_distance
    halfD = new_d / 2

    c = (a1[axis] + a2[axis]) / 2

    if a2[axis] > a1[axis]:
        na1 = c - halfD
        na2 = c + halfD
    else:
        na1 = c + halfD
        na2 = c - halfD

    if axis == 0:
        na1 = [na1, a1[1], a1[2]]
        na2 = [na2, a2[1], a2[2]]
    elif axis == 2:
        na1 = [a1[0], a1[1], na1]
        na2 = [a2[0], a2[1], na2]

    pd[pos1] = na1
    pd[pos2] = na2

    return pd


def plot(mesh, mesh1, moving_nodes, new_points, mesh2, ID_moving_nodes):
    """

    :param mesh:
    :param mesh1:
    :param moving_nodes:
    :param new_points:
    :param mesh2:
    :param ID_moving_nodes:
    :return:
    """

    fig = plt.figure(figsize=(14, 9))

    # parameters configuration
    color_points = 'red'
    point_size = 30
    muscle_transparency = 0.2
    point_transparency = 1

    # original mesh
    ax = fig.add_subplot(1, 2, 1, projection='3d')
    ax.scatter(moving_nodes[:, 0], moving_nodes[:, 1], moving_nodes[:, 2], c=color_points, s=point_size, alpha=point_transparency)
    ax.plot_trisurf(mesh.points[:, 0], mesh.points[:, 1], triangles=mesh1.faces, Z=mesh1.vertices[:, 2], alpha=muscle_transparency)
    ax.view_init(0, 70, 90)
    ax.set_xlim(-160, -40)
    ax.set_zlim(-80, 80)

    # morphed mesh
    ax = fig.add_subplot(1, 2, 2, projection='3d')

    ID_sorted = [ID_moving_nodes[0],ID_moving_nodes[2], ID_moving_nodes[3], ID_moving_nodes[1]]
    moving_nodes_sorted = complete_mesh[ID_sorted, :]

    # Generate a spline representation of the curve
    tck, u = splprep([moving_nodes_sorted[:, 0], moving_nodes_sorted[:, 1], moving_nodes_sorted[:, 2]], s=1, per=False)  # todo: check it out
    u_new = np.linspace(u.min(), u.max(), 100)
    x_new, y_new, z_new = splev(u_new, tck)
    ax.plot(x_new, y_new, z_new, color='red')

    # Points of the interspinous distance
    is_nodes = [ID_moving_nodes[4], ID_moving_nodes[5]]
    is_nodes = complete_mesh[is_nodes, :]
    ax.scatter(is_nodes[:, 0], is_nodes[:, 1], is_nodes[:, 2], c=color_points, s=point_size, alpha=point_transparency)

    # Morphed mesh plot
    ax.plot_trisurf(new_points[:, 0], new_points[:, 1], triangles=mesh2.faces, Z=mesh2.vertices[:, 2], alpha=muscle_transparency)
    ax.view_init(0, 70, 90)
    ax.set_xlim(-160, -40)
    ax.set_zlim(-80, 80)
    plt.show()

    return


if __name__ == '__main__':

    # Load the 3D mesh using meshio library
    mesh = meshio.read('muscles_info.inp')

    # Convert the mesh data to a trimesh object (for representation purposes)
    complete_mesh = mesh.points
    cells = mesh.get_cells_type('hexahedron')
    mesh1 = trimesh.Trimesh(vertices=complete_mesh, faces=cells)

    # --------------------------------------------------------------------------------------------------- #
    # Input definitions

    # Note: node number = (node number - 1) because python starts at 0

    # Define fixed nodes
    ID_fixed_nodes = [0, 1, 4, 5, 8, 11]

    # Define moving nodes (nodes of the diameters to be changed)
    # transverse diameter
    node_1 = 14
    node_2 = 18
    # transverse diameter
    node_3 = 317
    node_4 = 528
    # interspinous  diameter
    node_5 = 7
    node_6 = 12
    # anteroposterior diameter
    #node_7 = 520
    #node_8 = 541

    # Define new diameters (distance between two defined points)
    diameter_AP_variation = 50
    diameter_T_variation = 45
    diameter_IS_variation = 120

    # --------------------------------------------------------------------------------------------------- #

    ID_moving_nodes = [node_1, node_2, node_3, node_4, node_5, node_6]
    pos = list(range(-len(ID_moving_nodes), 0))

    fixed_nodes = complete_mesh[ID_fixed_nodes, :]
    moving_nodes = complete_mesh[ID_moving_nodes, :]
    fixed_moving_nodes = np.concatenate((fixed_nodes, moving_nodes), axis=0)
    new_nodes = fixed_moving_nodes.copy()

    new_nodes = select_diameter(complete_mesh, 'T', diameter_T_variation, node_1, node_2, new_nodes, pos[0], pos[1])
    new_nodes = select_diameter(complete_mesh, 'T', diameter_T_variation, node_3, node_4, new_nodes, pos[2], pos[3])
    new_nodes = select_diameter(complete_mesh, 'IS', diameter_IS_variation, node_5, node_6, new_nodes, pos[4], pos[5])
    #pd = select_diameter(points, 'AP', diameter_AP_variation, node_7, node_8, pd, pos[6], pos[7])
    #pd = select_diameter(points, 'T', diameter_T_variation, node_9, node_10, pd, pos[8], pos[9])

    new_points = rbfwarp3d(complete_mesh, fixed_moving_nodes, new_nodes, 'thin')

    mesh2 = trimesh.Trimesh(vertices=new_points, faces=cells)

    plot(mesh, mesh1, moving_nodes, new_points, mesh2, ID_moving_nodes)

    # Open INP file for writing
    index_list = list(range(1, len(new_points)+1))
    with open("muscles_nodes.inp", "w") as f:
        f.write("*Node, nset=pelvic_floor_nodes\n")
        for i, row in enumerate(new_points):
            row_with_index = [index_list[i]] + list(row)
            row_str = ", ".join(str(val) for val in row_with_index)
            f.write(row_str + "\n")
