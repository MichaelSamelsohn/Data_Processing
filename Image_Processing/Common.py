# Imports #
import copy
import os

from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


def use_lookup_table(image, lookup_table):
    """
    Convert image using lookup table values.
    The lookup table provides a transformation value for each possible intensity value (normally, 0-255).
    Lookup tables are extremely time-efficient when it comes to pixel-wise (as opposed to neighbourhood) transformations
    where there is a formula for each intensity value -> O(1), otherwise, the calculation is done for every pixel -> O(N*M)
    (N, M are the image dimensions).

    :param image: The image to be used for the lookup table.
    :param lookup_table: The lookup table.
    :return: Result image where every pixel was transformed according to its corresponding index value in the lookup
    table.
    """

    log.debug("Applying lookup table to the image")
    new_image = copy.deepcopy(image)
    new_image[:, :] = lookup_table[image[:, :]]
    return new_image


def scale_image(image, scale_factor=Settings.DEFAULT_SCALING_FACTOR):
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
