# Imports #
from matplotlib import pyplot as plt
from scipy.spatial.distance import directed_hausdorff
from Image_Processing.Settings.image_settings import *
from scipy.spatial import cKDTree


def generate_multifoil(a: float, b: float, lobes: int, number_of_points: int):
    """
    Generate a multifoil function.

    :param a: Amplitude of the multifoil.
    :param b: Amplitude of each lobe.
    :param lobes: Number of lobes the multifoil includes.
    :param number_of_points: Number of points included in the function.

    :return: Cartesian coordinates of the multifoil function.
    """

    log.debug("Generating a multifoil for comparison")

    log.debug("Calculating the polar coordinates")
    phi = np.linspace(0, 2 * np.pi, number_of_points)
    r = a * (1 + b * np.cos(lobes * phi))

    log.debug("Converting to Cartesian coordinates")
    x = [r[i] * np.cos(phi[i]) for i in range(number_of_points)]
    y = [r[i] * np.sin(phi[i]) for i in range(number_of_points)]

    return x, y


def plot(x1, y1, x2, y2, display_time=None):
    """
    Plot two curves for the meta-shell and the multifoil for comparison.

    :param x1: Curve 1 values on the x-axis.
    :param y1: Curve 1 values on the y-axis.
    :param x2: Curve 2 values on the x-axis.
    :param y2: Curve 2 values on the y-axis.
    :param display_time: TODO - Complete the docstring.
    """

    # Plotting both curves.
    plt.plot(x1, y1, color='blue', label='Meta shell')
    plt.plot(x2, y2, color='red', label='Multifoil')

    # Adding labels and title.
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Processed meta-shell vs. generated multifoil')
    plt.legend()
    plt.grid(True)

    # Showing the plot.
    if display_time:
        plt.show(block=False)
        plt.pause(display_time)
        plt.close()
    else:
        plt.show()


def measure_hausdorff_distance(curve1, curve2):
    """
    Compute the Hausdorff distance between two closed curves.
    The Hausdorff distance is a way to measure how far apart two sets of points are in a space. It tells you the
    worst-case mismatch between the two shapes.
    Algorithm (Assuming we have two closed curves 𝐴 and 𝐵):
    1) For each point in 𝐴, find the closest point in 𝐵.
    2) Take the largest of those closest distances.
    3) Do the same from 𝐵 to 𝐴.
    4) The Hausdorff distance is the maximum of the values from (2) and (3).

    Qualities:
    Symmetric - Swapping curves doesn't change the result.
    Shape-aware - It captures structural differences, not just point-wise or average error.
    No point matching needed - Great for comparing shapes with different point distributions or sampling.

    Parameters:
    curve1, curve2 : array-like of shape (N, 2) and (M, 2)
        The (x, y) coordinates of the points on each curve.

    Returns:
    float : Hausdorff distance
    """

    curve1 = np.asarray(curve1)
    curve2 = np.asarray(curve2)

    # Directed Hausdorff distances in both directions
    d1 = directed_hausdorff(curve1, curve2)[0]
    d2 = directed_hausdorff(curve2, curve1)[0]

    return max(d1, d2)


def measure_average_distance(curve1, curve2):
    """
    Compute the average minimum distance (symmetric) between two closed curves.
    Algorithm (Assuming we have two closed curves 𝐴 and 𝐵):
    1) For each point in Curve 𝐴, find the closest point in Curve 𝐵, and take the average of those distances.
    2) Do the same from Curve 𝐵 to Curve 𝐴.
    3) Average those two values to get a symmetric score.

    Note - This is sometimes called the Symmetric Chamfer Distance, and it's a softer, more forgiving similarity metric
    than Hausdorff.
    """

    curve1 = np.asarray(curve1)
    curve2 = np.asarray(curve2)

    # KDTree for fast nearest-neighbor lookup
    tree1 = cKDTree(curve1)
    tree2 = cKDTree(curve2)

    # One-way distances
    dists1, _ = tree2.query(curve1)
    dists2, _ = tree1.query(curve2)

    avg_dist = (np.mean(dists1) + np.mean(dists2)) / 2
    return avg_dist
