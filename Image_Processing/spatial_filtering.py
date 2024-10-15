"""
Script Name - spatial_filtering.py

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
import numpy as np
from numpy import ndarray
from common import generate_filter, convolution_2d, contrast_stretching
from segmentation import laplacian_gradient
from Settings import image_settings
from Utilities.decorators import book_reference
from Settings.settings import log

# Constants #
SOBEL_OPERATORS = {
    "VERTICAL": np.array([[-1, -2, -1],
                            [0, 0, 0],
                            [1, 2, 1]]),
    "HORIZONTAL": np.array([[-1, 0, 1],
                          [-2, 0, 2],
                          [-1, 0, 1]])
}


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 3 - Smoothing (Lowpass) Spatial Filters, p.164-175")
def blur_image(image: ndarray, filter_type=image_settings.DEFAULT_FILTER_TYPE,
               filter_size=image_settings.DEFAULT_FILTER_SIZE, padding_type=image_settings.DEFAULT_PADDING_TYPE,
               **kwargs) -> ndarray:
    """
    Apply a low pass filter (blur) on an image.

    :param image: The image to be filtered.
    :param filter_type: The filter type.
    :param filter_size: The filter size.
    :param padding_type: The padding type used for the convolution.
    :return: Filtered image.
    """
    kernel = generate_filter(filter_type=filter_type, filter_size=filter_size, **kwargs)
    return convolution_2d(image=image, kernel=kernel, padding_type=padding_type)


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 3 - Sharpening (Highpass) Spatial Filters, p.178-182")
def laplacian_image_sharpening(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                               include_diagonal_terms=image_settings.DEFAULT_INCLUDE_DIAGONAL_TERMS,
                               c=image_settings.DEFAULT_CONSTANT) -> ndarray:
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


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 3 - Sharpening (Highpass) Spatial Filters, p.182-184")
def high_boost_filter(image: ndarray, filter_type=image_settings.DEFAULT_FILTER_TYPE, filter_size=image_settings.DEFAULT_FILTER_SIZE,
                      padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    Use a high boost filter (un-sharp masking) to sharpen the image.

    :param image: The image for sharpening.
    :param filter_type: The filter used for the image blurring.
    :param filter_size: The filter size used for the image blurring.
    :param padding_type: The padding type used for the convolution.
    :return: Sharpened image.
    """

    log.debug("Blurring the image")
    blurred_image = blur_image(image=image, filter_type=filter_type, filter_size=filter_size, padding_type=padding_type)

    log.debug("Subtracting the blurred image from the original one -> Mask")
    mask = image - blurred_image

    log.debug("Adding the mask to the original image")
    return image + mask


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 3 - Using first-order derivatives for image sharpening — the gradient, "
                               "p.184-188")
def sobel_filter(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                 contrast_stretch=image_settings.DEFAULT_CONTRAST_STRETCHING) -> ndarray:
    """
    Use a sobel operator filter (first-order derivative) to sharpen the image.

    :param image: The image for sharpening.
    :param padding_type: The padding type used for the convolution.
    :param contrast_stretch: TODO: Complete the docstring.
    :return: Sharpened image.
    """

    log.debug("Calculating the horizontal-directional derivative")
    gx = convolution_2d(image=image, kernel=SOBEL_OPERATORS["HORIZONTAL"], padding_type=padding_type,
                        contrast_stretch=False)
    log.debug("Calculating the vertical-directional derivative")
    gy = convolution_2d(image=image, kernel=SOBEL_OPERATORS["VERTICAL"], padding_type=padding_type,
                        contrast_stretch=False)

    log.debug("Calculating the magnitude (length) of the image gradient")
    magnitude = np.sqrt(np.power(gx, 2) + np.power(gy, 2))
    return magnitude if not contrast_stretch else contrast_stretching(image=magnitude)
