# Imports #
import cmath
import math

from Utilities.decorators import measure_runtime
from Settings.settings import log


@measure_runtime
def dft_2d(spatial_coordinates: list[(float, float)]):
    """
    TODO: Complete the docstring.
    """

    fourier_coefficients = []

    log.debug("Turning spatial coordinates into complex numbers")
    complex_coordinates = [x + 1j * y for x, y in spatial_coordinates]

    log.debug("Calculating the Fourier coefficients")
    normalization_factor = 1 / len(spatial_coordinates)  # Simplified, because it's used many times.
    for k in range(len(spatial_coordinates)):
        a = 0  # Resetting the coefficient calculation.
        for n in range(len(spatial_coordinates)):
            a += normalization_factor * complex_coordinates[n] * cmath.exp(
                -1j * 2 * math.pi * n * k * normalization_factor)
        fourier_coefficients.append(a)

    return fourier_coefficients
