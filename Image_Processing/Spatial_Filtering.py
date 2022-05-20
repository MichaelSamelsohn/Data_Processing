"""
Script Name - Spatial_Filtering.py

Purpose - Perform spatial filtering on an image. Intensity transformations refer to changes based on a neighbourhood (as
opposed to intensity transformations, pixel based operations).

Best practice for working with intensity transformations (*):
    1) Generate a filter. A filter defines the relation between the target pixel and its surrounding neighbors. The
    bigger the filter, the more neighbouring pixels influence the target one. There are several important rules when
    constructing a filter:
        * It must have a center -> Filter size is symmetrical and an odd integer.
        * It must be normalized, otherwise, you may get pixel values that exceed the possible range.
    2) Convolve the target image with the generated filter (kernel). Convolution requires the following:
        * Pad the image. This is because the filter doesn't have enough neighbors for the boundary pixels, therefore,
        the image needs to be artificially extended.

Created by Michael Samelsohn, 20/05/22
"""

# Imports #
import os

from numpy import ndarray

from Common import generate_filter, convolution_2d
from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


def box_filter(image: ndarray, filter_size=Settings.DEFAULT_FILTER_SIZE, padding_type=Settings.DEFAULT_PADDING_TYPE) \
        -> ndarray:
    """
    Use box filter on an image.

    :param image: The image to be filtered.
    :param filter_size: The filter size.
    :param padding_type: The padding type used for the convolution.
    :return: Filtered image.
    """
    kernel = generate_filter(filter_type=Settings.BOX_FILTER, filter_size=filter_size)
    return convolution_2d(image=image, kernel=kernel, padding_type=padding_type)
