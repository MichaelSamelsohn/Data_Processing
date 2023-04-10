"""
Script Name - Intensity_Transformations.py

Purpose - Perform intensity transformations on an image. Intensity transformations refer to changes per pixel (as
opposed to pixel neighbourhood operations).

Best practice for working with intensity transformations (*):
    1) Construct a formula for the transformation dependent on the pixel value - T(pixel).
    2) Prepare a lookup table for all the possible pixel values (see use_lookup_table method docstring for time
       analysis).
    3) Use the lookup table to transform the image.

(*) - Assuming the image intensity values are integers.

Created by Michael Samelsohn, 13/05/22
"""

# Imports #
import os

import numpy as np
from numpy import ndarray

from Common import use_lookup_table, scale_pixel_values
from Utilities import Settings
from Utilities.Decorators import book_implementation
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


def thresholding(image: ndarray, threshold_value=Settings.DEFAULT_THRESHOLD_VALUE) -> ndarray:
    """
    Transforming the image to its binary version using the provided threshold.
    Comparing pixel values against provided threshold. If pixel value is larger, convert it to 1 (white).
    Otherwise, convert it to 0 (black).

    :param image: The image for thresholding.
    :param threshold_value: The threshold value. Acceptable values are - [0, 1].
    :return: The binary image (based on the threshold).
    """

    log.debug(f"The provided threshold is - {threshold_value}")
    try:
        assert 0 < threshold_value < 1
    except AssertionError:
        log.warning("Provided threshold is not in acceptable range, [0, 1], "
                    "it will be assigned to closest acceptable value")
        threshold_value = 0 if threshold_value < 0 else 1

    log.debug("Performing image thresholding")
    return (image > threshold_value).astype(float)


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 3 - Some Basic Intensity Transformation Functions, p.122-123")
def negative(image: ndarray) -> ndarray:
    """
    Perform image negative. Simply subtract every value of the matrix from the maximal value (1).

    :param image: The image for negative.
    :return: The image negative.
    """

    log.debug("Performing image negative")
    return 1 - image


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="??")  # TODO: Add reference.
def gamma_correction(image: ndarray, gamma=Settings.DEFAULT_GAMMA_VALUE) -> ndarray:
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
    elif gamma == 1:
        log.warning("Gamma of 1 does nothing to the image")
        return image

    log.debug("Performing Gamma correction to the image")
    return np.power(image, gamma)


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 3 - Some Basic Intensity Transformation Functions, p.131-133")
@scale_pixel_values(scale_factor=255)
def bit_plane_reconstruction(image: ndarray, degree_of_reduction=Settings.DEFAULT_DEGREE_OF_REDUCTION) -> ndarray:
    """
    Bit plane reconstruction. The degree of reduction indicates how many bit planes we dismiss from the LSB.
    If degree of reduction is 0 (minimal value), all bit planes are included (original image).
    If degree of reduction is 1, all bit planes are included excluding the LSB.
    If degree of reduction is 7 (maximal value), only the MSB is included.

    When looking at reconstructed images, it is noticeable that when dropping a few bits (2-3), the image quality
    remains intact (identical to human eyes). This means that the human eye, can't detect differences up to a change of
    4-8 pixel value colors. In terms of engineering, this could help with compression, as lower bits can be dropped
    entirely (and later padded with zeros), thus saving memory.

    :param image: The image for bit plane reconstruction.
    :param degree_of_reduction: Degree of reduction = How many LSB bits are dropped.
    :return: Bit plane reconstructed image.
    """

    log.debug(f"The provided degree of reduction is - {degree_of_reduction}")
    if type(degree_of_reduction) is not int:
        log.error("The selected bit plane is not of type integer. Will reset to default")
        degree_of_reduction = Settings.DEFAULT_DEGREE_OF_REDUCTION
    # If provided degree of reduction is not in acceptable range, [0, 7], it will be assigned to closest acceptable value.
    degree_of_reduction = 0 if degree_of_reduction < 0 else 7 if degree_of_reduction > 7 else degree_of_reduction
    reduction_factor = np.power(2, degree_of_reduction)
    log.debug(f"The reduction factor is - {reduction_factor}")

    log.debug("Preparing the lookup table for the transformation")
    lookup_table = np.zeros(256)  # Initializing zeros array.
    for value in range(256):
        lookup_table.put(value, value // reduction_factor * reduction_factor)

    log.debug("Performing image color reduction")
    return use_lookup_table(image=image, lookup_table=lookup_table)


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 3 - Some Basic Intensity Transformation Functions, p.131-133")
@scale_pixel_values(scale_factor=255)
def bit_plane_slicing(image: ndarray, bit_plane=Settings.DEFAULT_BIT_PLANE) -> ndarray:
    """
    Bit plane slicing. It comes to show the contribution of each bit plane.
    The planes where the bit is equal to 1 will contribute pixel value of 255 (white).
    The planes where the bit is equal to 0 will contribute pixel value of 0 (black).
    Since an image is normally continuous (other than edges), the difference between MSB values of neighbouring pixels
    is small. Therefore, when slicing significant bits, the pixel values should give a relatively 'good' image, where
    the object is recognizable (*).
    This is not the case for the less significant bits as even small changes in pixel values, drastically changes those
    bits. Therefore, lower bit plane slicing will lead to random-like images.

    (*) - This is true for non-random images (usually, where there is an object and background).

    :param image: The image to be bit plane sliced.
    :param bit_plane:  The bit plane.
    :return: Bit plane sliced image (see explanation above on what image to expect depending on the selected bit plane).
    """

    log.debug(f"The chosen bit plane is - {bit_plane}")
    # If provided bit plane is not in acceptable range, [0, 7], it will be assigned to the closest acceptable value.
    bit_plane = 0 if bit_plane < 0 else 7 if bit_plane > 7 else bit_plane
    mask = 1 << bit_plane  # Mask to filter the bits not belonging to selected bit plane.
    log.debug(f"Using the following mask - {mask}")

    log.debug("Preparing the lookup table for the transformation")
    lookup_table = np.zeros(256)  # Initializing zeros array.
    for value in range(256):
        lookup_table.put(value, ((value & mask) >> bit_plane) * 255)

    log.debug("Performing bit plane slicing")
    return use_lookup_table(image=image, lookup_table=lookup_table)
