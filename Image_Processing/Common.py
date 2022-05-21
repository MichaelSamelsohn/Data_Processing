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
from Utilities.Decorators import measure_runtime
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


def convert_to_grayscale(image: ndarray) -> ndarray:
    """
    Convert a color image to grayscale.

    :param image: Color image for conversion. If image is grayscale, it is returned as is.
    :return: Grayscale image.
    """

    # TODO: Add a check that image is not grayscale already.
    log.debug("Converting image to grayscale")
    red, green, blue = image[:, :, 0], image[:, :, 1], image[:, :, 2]
    grayscale_image = 0.2989 * red + 0.5870 * green + 0.1140 * blue
    return grayscale_image


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

    new_image = copy.deepcopy(image)
    log.debug("Applying lookup table to the image")
    new_image[:, :] = lookup_table[image[:, :]]
    return new_image


def scale_pixel_values(scale_factor=Settings.DEFAULT_SCALING_FACTOR):
    def wrapper(func):
        def inner(*args, **kwargs):
            log.debug(f"Scaling image by a factor of {scale_factor}")
            kwargs["image"] = scale_image(image=kwargs["image"], scale_factor=scale_factor)
            return_image = func(*args, **kwargs)
            log.debug("Scaling image back")
            return scale_image(image=return_image, scale_factor=1 / scale_factor)

        return inner

    return wrapper


def scale_image(image: ndarray, scale_factor=Settings.DEFAULT_SCALING_FACTOR) -> ndarray:
    """
    Scale the pixel values of an image by the provided scaling factor.
    This function is useful when the pixel range is [0, 1] and it needs to be converted to integer values (scaling
    upwards by 255) and vice-versa.

    :param image: The image to be scaled.
    :param scale_factor: The scaling factor.
    Note - For scaling factor 255, the image is also set as int type (rather than float).
    :return: Scaled image.
    """

    log.debug(f"Scale factor is - {scale_factor}")
    log.debug("Scaling the image")
    scaled_image = copy.deepcopy(image * scale_factor)

    if scale_factor == 255:
        log.debug("Scale factor is 255 -> Setting the image as int type")
        scaled_image = scaled_image.astype(int)

    return scaled_image


def calculate_histogram(image: ndarray, normalize=Settings.DEFAULT_HISTOGRAM_NORMALIZATION) \
        -> tuple[ndarray, ndarray, ndarray] | ndarray:
    """
    Calculate the histogram of an image. A histogram shows the amount of pixels per pixel intensity value.
    If the histogram is normalized, it shows the probabilities per pixel intensity value.
    Note - if the image is a color one, the return value will contain three histograms (one for each color channel).

    :param image: The image.
    :param normalize: Boolean value indicating if the histogram is to be normalized or not.
    :return: Histogram of the provided image.
    """

    if len(image.shape) == 3:
        log.debug("Color image -> Splitting the image to its three channels")
        red, green, blue = image[:, :, 0], image[:, :, 1], image[:, :, 2]
        return calculate_histogram(image=red, normalize=normalize), \
               calculate_histogram(image=green, normalize=normalize), \
               calculate_histogram(image=blue, normalize=normalize)

    log.debug("Scaling the image to have a histogram with integer values")
    image = scale_image(image=image, scale_factor=255)

    log.debug("Initializing the histogram")
    histogram = np.zeros(256)

    log.debug("Calculating the histogram")
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            histogram[image[row][col]] += 1

    if normalize:
        log.debug("Normalizing the histogram")
        histogram /= (image.shape[0] * image.shape[1])

    return histogram


def generate_filter(filter_type=Settings.DEFAULT_FILTER_TYPE, filter_size=Settings.DEFAULT_FILTER_SIZE) -> ndarray:
    """

    :param filter_type: The type of filter to be generated.
    :param filter_size: The size of the filter to be generated. Can be either an integer or a tuple of integers.
    Types of filters:
        * Box filter - An all ones filter (with normalization).
    :return: Matrix array with the specified dimensions and based on the selected filter type
    """

    # Asserting that filter size is an odd number and filter is symmetrical.
    if type(filter_size) == int:
        if filter_size % 2 == 0:
            log.warning("Filter size is an even number. Filters should be odd number size")
        else:
            filter_size = (filter_size, filter_size)
    elif type(filter_size) == tuple:
        if len(filter_size) != 2:
            log.raise_exception(message="Filter size is not defined well", exception=IndexError)
        elif filter_size[0] != filter_size[1]:
            log.warning("Filter size is not symmetrical")

    image_filter = np.zeros(shape=filter_size)
    log.debug("Identifying the filter type and generating it")
    match filter_type:
        case Settings.BOX_FILTER:
            log.debug("Box type filter selected")
            image_filter = np.ones(shape=filter_size)
            image_filter /= np.sum(image_filter)  # Normalize.

    return image_filter


def pad_image(image: ndarray, padding_type=Settings.DEFAULT_PADDING_TYPE,
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

    log.debug("Generating image with extended boundaries")
    padded_image = np.zeros(shape=(image.shape[0] + 2 * padding_size,
                                   image.shape[1] + 2 * padding_size,
                                   image.shape[2]))

    log.debug("Identifying the padding type and applying it")
    match padding_type:
        case Settings.ZERO_PADDING:
            log.debug("Zero padding selected")
            padded_image[padding_size:-padding_size, padding_size:-padding_size] = image[:, :]

    return padded_image


@measure_runtime
def convolution_2d(image: ndarray, kernel: ndarray, padding_type=Settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    Perform convolution on an image with a kernel matrix. Mainly used for spatial filtering.
    TODO: Optimize function runtime.

    :param image: The image to be convolved.
    :param kernel: Kernel matrix.
    :param padding_type: The padding type used for extending the image boundaries.
    :return: Convolution of the image with the convolution object.
    """

    log.debug("Asserting that convolution matrix is symmetrical")
    convolution_matrix_size = kernel.shape[0]
    if kernel.shape[0] != kernel.shape[1]:
        log.raise_exception(message="Convolution matrix is not symmetrical", exception=ValueError)

    log.debug(f"Convolution matrix size is - {convolution_matrix_size}")
    log.debug("Padding the image")
    padded_image = pad_image(image=image, padding_type=padding_type, padding_size=convolution_matrix_size // 2)

    log.debug("Performing the convolution between the image and the convolution matrix")
    convolution_image = np.zeros(shape=image.shape)
    for row in range(convolution_matrix_size // 2, image.shape[0] + convolution_matrix_size // 2):
        for col in range(convolution_matrix_size // 2, image.shape[1] + convolution_matrix_size // 2):
            sub_image = extract_sub_image(image=padded_image, position=(row, col),
                                          sub_image_size=convolution_matrix_size)
            for color_index in range(image.shape[2]):
                if len(image.shape) == 3:
                    # Color image.
                    convolution_image[row - convolution_matrix_size // 2, col - convolution_matrix_size // 2, color_index] =\
                        np.sum(sub_image[:, :, color_index] * kernel)
                else:
                    # Grayscale image.
                    convolution_image[row - convolution_matrix_size // 2, col - convolution_matrix_size // 2] = \
                        np.sum(sub_image[:, :] * kernel)

    return convolution_image


def extract_sub_image(image: ndarray, position: tuple[int, int], sub_image_size: int) -> ndarray:
    """
    Extract sub image from an image. Mainly used for performing neighbourhood operations.

    :param image: The image.
    :param position: The x,y position of the center pixel (of the sub image).
    :param sub_image_size: The size of the sub image.
    :return: Sub image, where the center pixel is based on the selected position.
    """

    # Asserting that sub image size is an odd number (so it can have a center pixel).
    if sub_image_size % 2 == 0:
        log.raise_exception(message="The selected sub image is an even integer (sub image must have a center pixel, "
                                    "therefore, its size must be an odd integer)", exception=ValueError)

    # Setting the positions for the rows.
    row_start = position[0] - (sub_image_size // 2)
    row_end = position[0] + (sub_image_size // 2) + 1

    # Setting the positions for the cols.
    col_start = position[1] - (sub_image_size // 2)
    col_end = position[1] + (sub_image_size // 2) + 1

    # Extracting the sub image.
    sub_image = image[row_start:row_end, col_start:col_end]

    return sub_image
