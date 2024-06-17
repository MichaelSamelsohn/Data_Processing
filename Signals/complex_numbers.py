"""
TODO: Complete the docstring.
"""

# Imports #
import os
import numpy as np
from matplotlib import pyplot as plt
from Settings.settings import log


class Complex:
    def __init__(self, re, im):
        self.re = re
        self.im = im

        # Polar notation.
        self.magnitude = np.sqrt(self.re ** 2 + self.im ** 2)
        self.theta = np.arctan(self.im / self.re)

    def plot(self):
        """
        Plot the complex number.
        TODO: Possibly add (0,0) as reference.
        """

        log.debug("Plotting the complex number")

        # TODO: Explain what the plot arguments stand for.
        plt.plot(self.re, self.im, 'o--', markersize=6)
        plt.grid()  # Adds the plot grid.

        plt.title("Complex number")
        plt.xlabel("Real")
        plt.ylabel("Imaginary")

        plt.show()

    def __add__(self, other):
        return Complex(re=self.re + other.re, im=self.im + other.im)

    def __sub__(self, other):
        return Complex(re=self.re - other.re, im=self.im - other.im)

    def __mul__(self, other):
        # TODO: Finish the implementation.
        pass

