"""
Script Name - intensity_transformations.py

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
import numpy as np
from numpy import ndarray
from Image_Processing.Source.Basic.common import use_lookup_table, scale_pixel_values
from Image_Processing.Settings.image_settings import *
from Utilities.decorators import book_reference


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 3.2 - Some Basic Intensity Transformation Functions, p.122-123")
def negative(image: ndarray) -> ndarray:
    """
    Perform image negative. Simply subtract every value of the matrix from the maximal value, 1.

    :param image: The image for negative.

    :return: Negative image.
    """

    log.info("Performing image negative")
    return 1 - image


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 3.2 - Some Basic Intensity Transformation Functions, p.125-128")
def gamma_correction(image: ndarray, gamma: float) -> ndarray:
    """
    Perform Gamma correction on an image.
        * Higher (>1) Gamma value darkens the image.
        * Smaller (<1) Gamma value brightens the image.
        * Gamma value = 1 does nothing.

    Assumptions:
    • Gamma value is a positive float different from 1 (if gamma=1, the function has no effect).

    :param image: The image to be corrected.
    :param gamma: Gamma value for the image correction.

    :return: Gamma-corrected image.
    """

    log.info(f"Performing Gamma (={gamma}) correction to the image")
    return np.power(image, gamma)


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 3.2 - Some Basic Intensity Transformation Functions, p.131-133")
@scale_pixel_values(scale_factor=255)
def bit_plane_reconstruction(image: ndarray, degree_of_reduction: int) -> ndarray:
    """
    Bit-plane reconstruction. The degree of reduction indicates how many bit planes we dismiss from the LSB.
    If degree of reduction is 0 (minimal value), all bit planes are included (original image).
    If degree of reduction is 1, all bit planes are included excluding the LSB.
    If degree of reduction is 7 (maximal value), only the MSB is included.

    When looking at reconstructed images, it is noticeable that when dropping a few bits (2-3), the image quality
    remains intact (identical to human eyes). This means that the human eye, can't detect differences up to a change of
    4-8 pixel value colors. In terms of engineering, this could help with compression, as lower bits can be dropped
    entirely (and later padded with zeros), thus saving memory.

    :param image: The image for bit-plane reconstruction.
    :param degree_of_reduction: Degree of reduction = How many LSB bits are dropped.

    :return: Bit-plane reconstructed image.
    """

    log.info(f"Performing image color reduction (degree of reduction = {degree_of_reduction})")

    # If provided degree of reduction is not in acceptable range, [0, 7], it will be assigned to the closest acceptable
    # value.
    degree_of_reduction = 0 if degree_of_reduction < 0 else 7 if degree_of_reduction > 7 else degree_of_reduction
    reduction_factor = np.power(2, degree_of_reduction)
    log.debug(f"The reduction factor is - {reduction_factor}")

    log.debug("Preparing the lookup table for the transformation")
    lookup_table = np.zeros(256)  # Initializing zeros array.
    for value in range(256):
        lookup_table.put(value, value // reduction_factor * reduction_factor)

    # Applying the lookup table.
    return use_lookup_table(image=image, lookup_table=lookup_table)


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 3.2 - Some Basic Intensity Transformation Functions, p.131-133")
@scale_pixel_values(scale_factor=255)
def bit_plane_slicing(image: ndarray, bit_plane: int) -> ndarray:
    """
    Bit-plane slicing. It comes to show the contribution of each bit plane.
    The planes where the bit is equal to 1 will contribute pixel value of 255 (white).
    The planes where the bit is equal to 0 will contribute pixel value of 0 (black).
    Since an image is normally continuous (other than edges), the difference between MSB values of neighbouring pixels
    is small. Therefore, when slicing significant bits, the pixel values should give a relatively 'good' image, where
    the object is recognizable (*).
    This is not the case for the less significant bits as even small changes in pixel values, drastically changes those
    bits. Therefore, lower bit plane slicing will lead to random-like images.

    (*) - This is true for non-random images (usually, where there is an object and background).

    :param image: The image to be bit-plane sliced.
    :param bit_plane:  The bit plane.

    :return: Bit-plane sliced image (see explanation above on what image to expect depending on the selected bit plane).
    """

    log.info(f"Performing bit-plane ({bit_plane}) slicing")

    # If provided bit-plane is not in acceptable range, [0, 7], it will be assigned to the closest acceptable value.
    bit_plane = 0 if bit_plane < 0 else 7 if bit_plane > 7 else bit_plane
    mask = 1 << bit_plane  # Mask to filter the bits not belonging to selected bit plane.
    log.debug(f"Using the following mask - {mask}")

    log.debug("Preparing the lookup table for the transformation")
    lookup_table = np.zeros(256)  # Initializing zeros array.
    for value in range(256):
        lookup_table.put(value, ((value & mask) >> bit_plane) * 255)

    # Applying the lookup table.
    return use_lookup_table(image=image, lookup_table=lookup_table)
