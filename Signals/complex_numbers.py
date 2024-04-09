"""
TODO: Complete the docstring.
"""

# Imports #
import os
import numpy as np
from matplotlib import pyplot as plt
from Utilities.logger import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


class Complex:
    def __init__(self, re, im):
        self.re = re
        self.im = im

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

    def polar_notation(self):
        mag = np.sqrt(self.re**2 + self.im**2)
        log.info(f"The magnitude is - {mag}")
        theta = np.arctan(self.im/self.re)
        log.info(f"The Theta is - {theta}")
        return mag, theta


if __name__ == '__main__':
    complex = Complex(re=1, im=1)
    # complex.plot()
    complex.polar_notation()
