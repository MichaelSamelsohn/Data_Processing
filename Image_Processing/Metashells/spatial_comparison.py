# Imports #
import numpy as np
from matplotlib import pyplot as plt

from Settings.settings import *


def spatial_comparison(x1, y1):
    """
    TODO: Complete the docstring.
    """

    x2, y2 = generate_multifoil(a=6, b=0.25, lobes=3, number_of_points=100)  # TODO: Generalize.
    plot(x1=x1, y1=y1, x2=x2, y2=y2)
    # TODO: Add a call for the metric function.


def generate_multifoil(a: float, b: float, lobes: int, number_of_points: int):
    """
    Generate a multifoil function.

    :param a: Amplitude of the multifoil.
    :param b: TODO: complete the docstring.
    :param lobes: Number of lobes the multifoil includes.
    :param number_of_points: Number of points included in the function.

    :return: Cartesian coordinates of the multifoil function.
    """

    log.debug("Calculating the polar coordinates")
    phi = np.linspace(0, 2 * np.pi, number_of_points)
    r = a * (1 + b * np.cos(lobes * phi))

    log.debug("Converting to Cartesian coordinates")
    x = [r[i] * np.cos(phi[i]) for i in range(number_of_points)]
    y = [r[i] * np.sin(phi[i]) for i in range(number_of_points)]

    return x, y


def plot(x1, y1, x2, y2):
    """
    TODO: Complete the docstring.
    """

    # Plot both scatter plots
    plt.plot(x1, y1, color='blue', label='Scatter 1')
    plt.plot(x2, y2, color='red', label='Scatter 2')

    # Add labels and title
    plt.xlabel('X Axis')
    plt.ylabel('Y Axis')
    plt.title('Two Scatter Plots on One Figure')
    plt.legend()
    plt.grid(True)

    # Show the plot
    plt.show()


# TODO: Add a function for measuring a metric.
