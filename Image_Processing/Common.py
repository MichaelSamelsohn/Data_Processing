"""
Script Name - Common.py

Purpose - Commonly used functions.

Created by Michael Samelsohn, 12/05/22
"""

# Imports #
import copy
import os
import numpy as np
from numpy import ndarray

from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


def use_lookup_table(image, lookup_table: ndarray | list) -> ndarray:
    """
    Convert image using lookup table values.
    The lookup table provides a transformation value for each possible intensity value (normally, 0-255).
    Lookup tables are extremely time-efficient when it comes to pixel-wise (as opposed to neighbourhood) transformations
    where there is a formula for each intensity value -> O(1).
    Otherwise, the calculation is done for every pixel -> O(N*M) (N, M are the image dimensions).

    :param image: The image to be used for the lookup table.
    :param lookup_table: The lookup table.
    :return: Result image where every pixel was transformed according to its corresponding index value in the lookup
    table.
    """

    log.debug("Applying lookup table to the image")
    new_image = copy.deepcopy(image)
    new_image[:, :] = lookup_table[image[:, :]]
    return new_image


def scale_image(image, scale_factor=Settings.DEFAULT_SCALING_FACTOR) -> ndarray:
    """
    Scale the pixel values of an image by the provided scaling factor.
    This function is useful when the pixel range is [0, 1] and it needs to be converted to integer values (scaling
    upwards by 255) and vice-versa.

    :param image: The image to be scaled.
    :param scale_factor: The scaling factor.
    Note - For scaling factor 255, the image is also set as int type (rather than float).
    :return: Scaled image.
    """

    scaled_image = copy.deepcopy(image * scale_factor)
    if scale_factor == 255:
        log.debug("Scale factor is 255 -> Setting the image as int type")
        scaled_image = scaled_image.astype(int)
    return scaled_image


def generate_filter(filter_type=Settings.DEFAULT_FILTER_TYPE, filter_size=Settings.DEFAULT_FILTER_SIZE) -> ndarray:
    """

    :param filter_type: The type of filter to be generated.
    :param filter_size: The size of the filter to be generated. Can be either an integer or a tuple of integers.
    Types of filters:
        * Box filter - An all ones filter (with normalization).
    TODO: Add a warning for even filter sizes or non-symmetrical sizes.
    :return: Matrix array with the specified dimensions and based on the selected filter type
    """

    image_filter = np.zeros(shape=filter_size)

    if type(filter_size) == int and filter_size % 2 != 0:
        log.warning("Filter size is a even number. Filters should be odd number size")
    elif type(filter_size) == tuple and filter_size[0] != filter_size[1]:
        log.warning("Filter size is not symmetrical")

    match filter_type:
        case "box":
            image_filter = np.ones(shape=filter_size)
            image_filter /= np.sum(image_filter)  # Normalize.

    return image_filter


def pad_image(image: ndarray, padding_type=Settings.ZERO_PADDING,
              padding_size=Settings.DEFAULT_PADDING_SIZE) -> ndarray:
    """
    Padding the image boundaries.

    :param image: The image for padding.
    :param padding_type: The padding type.
    Types of padding methods:
        * Zero padding ("zero_padding") - Add zeros to the boundaries.
    :param padding_size: The padding size.
    :return: Padded image.
    """

    image_filter = np.zeros(shape=(image.shape[0] + 2 * padding_size,
                                   image.shape[1] + 2 * padding_size,
                                   image.shape[2]))

    match padding_type:
        case Settings.ZERO_PADDING:
            image_filter[padding_size:-padding_size, padding_size:-padding_size] = image[:, :]

    return image_filter
