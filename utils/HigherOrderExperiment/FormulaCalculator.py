import math
from mpl_toolkits.mplot3d import axes3d
from itertools import izip
import matplotlib.pyplot as plt
import numpy as np


def calculate_formula(m, n, t):
    poweroftwo = (1 - m + ((n + 1) // 2))

    try:
        # print m,n,t

        top = math.factorial(t)
        top *= math.factorial(m)
        top *= math.factorial(n - t)
        if poweroftwo < 0:
            top *= 2 ** (-1 * poweroftwo)
        bottom = math.factorial(t - m)
        bottom *= math.factorial(((n + 1) // 2) - m)
        bottom *= math.factorial((2 * m) - t)
        if poweroftwo > 0:
            bottom *= 2 ** poweroftwo

    except ValueError:
        return 0

    return top / bottom


def calculate_probablistic(n, t):
    result = int(n * (1 - (1 - (float(t) / n)) ** 2) / 2)

    return result


def plot_formula():
    n = 100
    percentage_list = list()

    for t in range(1, 100):

        mv = list()

        for m in range(1, 100):
            mv.append(calculate_formula(m, n, t))

        mv_sum = sum(mv)

        percentage_list.append([int(c * 100 / mv_sum) for c in mv])

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    # X, Y, Z = axes3d.get_test_data(0.05)
    x = y = np.arange(1, 100, 1)
    X, Y = np.meshgrid(x, y)
    # Y = np.array([[range(1, 100)] for _ in range(1, 100)])
    Z = np.array(percentage_list)

    # print percentage_list[11][20]
    ax.plot_wireframe(X, Y, Z, rstride=1, cstride=1)

    plt.show()


def check_for_n(m, t, nl, nu):
    for n in range(nl, nu):
        print(calculate_formula(int(n * m / 200), n, int(n * t / 100)))


def get_most_likely_m(n, t):
    mv = dict()
    percentage_list = dict()

    for m in range(1, n):
        mv[m] = calculate_formula(m, n, t)

    mv_sum = sum(mv.values())
    print (mv_sum)
    likely = 0
    likely_key = None
    for key in mv.keys():
        percentage_list[key] = int(mv[key] * 100 / mv_sum)
        if percentage_list[key] > likely:
            likely = percentage_list[key]
            likely_key = key

    # print(percentage_list)
    return likely_key, likely


def read_from_csv(rawline):
    # assert isinstance(handle, file)
    line = rawline.split(",")
    return line[0], int(line[2]), int(line[3])


def write_to_csv(handle, name, killedfom, totalfom, killedhom, predictedkilledhom, confidence, probablistickilledhom):
    assert isinstance(handle, file)
    handle.write(
            ",".join([name, str(killedfom), str(totalfom), str(killedhom), str(predictedkilledhom),
                      str(confidence) + "%", str(probablistickilledhom)]))
    handle.write("\n")

"""
focsv = open("./firstorder.csv", "r")
hocsv = open("./secondorder.csv", "r")

resultcsv = open("./result.csv", "w")

for fline, hline in izip(focsv, hocsv):
    name, killedfom, totalfom = read_from_csv(fline.strip())
    dummy, dummy2, killedhom = read_from_csv(hline.strip())
    m, c = get_most_likely_m(totalfom, killedfom)
    p = calculate_probablistic(totalfom, killedfom)

    write_to_csv(resultcsv, name, killedfom, totalfom, killedhom, m, c, p)

# mlist = list()
# tlist = range(1, 100)

# for t in range(1, 100):
#     m, c = get_most_likely_m(100, t)
#     mlist.append(2 * m)

# plt.plot(tlist, mlist)
# plt.show()

focsv.close()
hocsv.close()
resultcsv.close()
"""


get_most_likely_m(100,50)

all = math.factorial(100)
all /= math.factorial(50)
all /= 2**50


print(all) 
