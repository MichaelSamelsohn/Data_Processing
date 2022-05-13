# Imports #
import os

import numpy as np

from Common import use_lookup_table
from Utilities import Settings
from Utilities.Decorators import book_implementation, scale_pixel_values
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


def thresholding(image, threshold_value=Settings.DEFAULT_BINARY_THRESHOLD):
    """
    Transforming the image to its binary version using the provided threshold.
    Comparing pixel values against provided threshold. If pixel value is larger, convert it to 1 (white).
    Otherwise, convert it to 0 (black).

    :param image: The image for thresholding.
    :param threshold_value: The threshold value. Acceptable values are - [0, 1].
    :return: The binary image (based on the threshold).
    """

    log.debug(f"The provided threshold is - {threshold_value}")
    log.warning("If provided threshold is not in acceptable range, [0, 1], "
                "it will be assigned to closest acceptable value")
    threshold_value = 0 if threshold_value < 0 else 1 if threshold_value > 1 else threshold_value

    log.debug("Performing image thresholding")
    return image > threshold_value


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 3 - Some Basic Intensity Transformation Functions, p.122-123")
def negative(image):
    """
    Perform image negative. Simply subtract every value of the matrix from the maximal value (1).

    :param image: The image for negative.
    :return: The image negative.
    """

    log.debug("Performing image negative")
    return 1 - image


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="??")  # TODO: Add reference.
def gamma_correction(image, gamma=Settings.DEFAULT_GAMMA_VALUE):
    """
    Perform Gamma correction on an image.
        * Higher (>1) Gamma value darkens the image.
        * Smaller (<1) Gamma value brightens the image.
        * Gamma value = 1 does nothing.

    :param image: The image to be corrected.
    :param gamma: Gamma value for the image correction.
    :return: Gamma-corrected image.
    """

    log.debug(f"Selected Gamma value is - {gamma}")
    if gamma <= 0:
        log.warning("Gamma of zero or less will generate a white image")

    log.debug("Performing Gamma correction to an image")
    return np.power(image, gamma)


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 3 - Some Basic Intensity Transformation Functions, p.131-133")
def bit_plane_reconstruction(image, degree_of_reduction=Settings.DEFAULT_DEGREE_OF_REDUCTION):
    """
    Bit plane reconstruction. The degree of reduction indicates how many bit planes we dismiss from the LSB.
    If degree of reduction is 0 (minimal value), all bit planes are included (original image).
    If degree of reduction is 1, all bit planes are included excluding the LSB.
    If degree of reduction is 7 (maximal value), only the MSB is included.

    :param image: The image for bit plane reconstruction.
    :param degree_of_reduction: Degree of reduction = How many LSB bits are dropped.
    :return: Bit plane reconstructed image.
    """

    log.debug(f"The provided degree of reduction is - {degree_of_reduction}")
    if type(degree_of_reduction) is not int:
        log.error("The selected bit plane is not of type integer. Will reset to default")
        degree_of_reduction = Settings.DEFAULT_DEGREE_OF_REDUCTION
    log.warning("If provided degree of reduction is not in acceptable range, [0, 7], "
                "it will be assigned to closest acceptable value")
    degree_of_reduction = 0 if degree_of_reduction < 0 else 7 if degree_of_reduction > 7 else degree_of_reduction

    log.debug("Performing image color reduction")
    reduction_factor = np.power(2, degree_of_reduction) / 256
    log.debug(f"The reduction factor is - {reduction_factor}")
    return image // reduction_factor * reduction_factor


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 3 - Some Basic Intensity Transformation Functions, p.131-133")
@scale_pixel_values(scale_factor=255)
def bit_plane_slicing(image, bit_plane=Settings.DEFAULT_BIT_PLANE):
    """

    :param image:
    :param bit_plane:
    :return:
    """

    log.debug(f"The chosen bit plane is - {bit_plane}")
    log.warning("If provided bit plane is not in acceptable range, [0, 7], "
                "it will be assigned to closest acceptable value")
    bit_plane = 0 if bit_plane < 0 else 7 if bit_plane > 7 else bit_plane

    mask = 1 << bit_plane  # Mask to filter the bits not belonging to selected bit plane.
    log.debug(f"Using the following mask - {mask}")

    log.debug("Preparing the lookup table for the transformation")
    lookup_table = np.zeros(256)  # Initializing zeros array.
    for value in range(256):
        lookup_table.put(value, 255 * ((value & mask) >> bit_plane))

    log.debug("Performing bit plane slicing")
    return use_lookup_table(image=image, lookup_table=lookup_table)
