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

import numpy as np
from numpy import ndarray

from Common import generate_filter, convolution_2d
from Segmentation import laplacian_gradient
from Utilities import Settings
from Utilities.Decorators import book_implementation
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


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 3 - Sharpening (Highpass) Spatial Filters, p.178-182")
def laplacian_image_sharpening(image: ndarray, padding_type=Settings.DEFAULT_PADDING_TYPE,
                               include_diagonal_terms=Settings.DEFAULT_INCLUDE_DIAGONAL_TERMS,
                               c=Settings.DEFAULT_CONSTANT) -> ndarray:
    """
    Perform image sharpening using the laplacian operator.

    :param image: The image for sharpening.
    :param padding_type: The padding type used for the convolution.
    :param include_diagonal_terms: TODO: Add parameter description.
    :param c: The multiplication factor.
    :return: Sharpened image.
    """

    log.debug("Segment the image using the Laplacian operator")
    post_laplacian_image = laplacian_gradient(image=image, padding_type=padding_type,
                                              include_diagonal_terms=include_diagonal_terms)

    return image + (c * post_laplacian_image)


def high_boost_filter(image: ndarray, filter_type=Settings.DEFAULT_FILTER_TYPE, filter_size=Settings.DEFAULT_FILTER_SIZE,
                      padding_type=Settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    Use a high boost filter (un-sharp masking) to sharpen the image.

    :param image: The image for sharpening.
    :param filter_type: The filter used for the image blurring.
    :param filter_size: The filter size used for the image blurring.
    :param padding_type: The padding type used for the convolution.
    :return: Sharpened image.
    """

    blurred_image = np.zeros(image.shape)

    log.debug("Blurring the image")
    match filter_type:
        case Settings.BOX_FILTER:
            blurred_image = box_filter(image=image, filter_size=filter_size, padding_type=padding_type)

    log.debug("Subtracting the blurred image from the original one -> Mask")
    mask = image - blurred_image

    log.debug("Adding the mask to the original image")
    return image + mask
