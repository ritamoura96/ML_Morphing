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


def calculate_w(ps, pd, method):
    """

    :param ps:
    :param pd:
    :param method:
    :return:
    """

    # Training 'w' with 'L'

    num_center = len(pd)
    nump = len(ps)
    K = np.zeros((num_center, nump))

    for i in range(num_center):
        # Forward warping, different from image warping
        dx = np.tile(pd[i, :], np.ones(nump)) - ps
        dx = np.reshape(dx, (len(pd), 3))
        # Use |dist|^2 as input
        K[:, i] = np.sum(dx ** 2, axis=1)

    if method == 'gau':
        r = 1
        K = rbf(K, r)
    elif method == 'thin':
        K = ThinPlate(K)

    P = np.insert(ps, 0, 1, axis=1)

    L1 = np.concatenate((K, P), axis=1)
    P_transpose = np.transpose(P)
    L2 = np.concatenate((P_transpose, np.zeros((4, 4))), axis=1)

    L = np.concatenate((L1, L2), axis=0)
    Y = np.concatenate((pd, np.zeros((4, 3))), axis=0)

    w = np.linalg.solve(L, Y)

    return w


def calculate_new_nodes(w, p3d, pd, method):
    """

    :param w:
    :param p3d:
    :param pd:
    :param method:
    :return:
    """

    nump = len(p3d)
    num_center = len(pd)
    kp = np.zeros((nump, num_center))

    for i in range(num_center):
        dx = p3d - np.ones((nump, 1))*pd[i, :]
        kp[:, i] = np.sum(dx ** 2, axis=1)

    if method == 'gau':
        r = 1
        kp = rbf(kp, r)
    elif method == 'thin':
        kp = ThinPlate(kp)

    P = np.insert(p3d, 0, 1, axis=1)
    L = np.concatenate((kp, P), axis=1)
    p3do = np.matmul(L, w)

    return p3do


def rbfwarp3d(p3d, ps, pd, method):

    w = calculate_w(ps, pd, method)
    new_nodes = calculate_new_nodes(w, p3d, pd, method)

    return new_nodes


