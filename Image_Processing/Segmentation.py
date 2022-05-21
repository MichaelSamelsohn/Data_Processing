"""
Script Name - Segmentation.py

Purpose - ??

Created by Michael Samelsohn, 20/05/22
"""

# Imports #
import os
import numpy as np
from numpy import ndarray

from Common import convolution_2d, convert_to_grayscale
from Intensity_Transformations import thresholding
from Utilities import Settings
from Utilities.Decorators import book_implementation
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)

# Constants #
LINE_DETECTION_KERNELS = {
    "HORIZONTAL": np.array([[-1, -1, -1],
                            [2, 2, 2],
                            [-1, -1, -1]]),
    "PLUS_45": np.array([[2, -1, -1],
                         [-1, 2, -1],
                         [-1, -1, 2]]),
    "VERTICAL": np.array([[-1, 2, -1],
                          [-1, 2, -1],
                          [-1, 2, -1]]),
    "MINUS_45": np.array([[-1, -1, 2],
                          [-1, 2, -1],
                          [2, -1, -1]]),
}

KIRSCH_EDGE_DETECTION_KERNELS = {
    "NORTH": np.array([[-3, -3, 5],
                       [-3, 0, 5],
                       [-3, -3, 5]]),
    "NORTH_WEST": np.array([[-3, 5, 5],
                            [-3, 0, 5],
                            [-3, -3, -3]]),
    "WEST": np.array([[5, 5, 5],
                      [-3, 0, -3],
                      [-3, -3, -3]]),
    "SOUTH_WEST": np.array([[5, 5, -3],
                            [5, 0, -3],
                            [-3, -3, -3]]),
    "SOUTH": np.array([[5, -3, -3],
                       [5, 0, -3],
                       [5, -3, -3]]),
    "SOUTH_EAST": np.array([[-3, -3, -3],
                            [5, 0, -3],
                            [5, 5, -3]]),
    "EAST": np.array([[-3, -3, -3],
                      [-3, 0, -3],
                      [5, 5, 5]]),
    "NORTH_EAST": np.array([[-3, -3, -3],
                            [-3, 0, 5],
                            [-3, 5, 5]])
}

LAPLACIAN_KERNELS = {
    "WITHOUT_DIAGONAL_TERMS": np.array([[0, 1, 0],
                                        [1, -4, 1],
                                        [0, 1, 0]]),
    "WITH_DIAGONAL_TERMS": np.array([[1, 1, 1],
                                     [1, -8, 1],
                                     [1, 1, 1]])
}


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 10.3 - Thresholding, p.746-747")
def global_thresholding(image: ndarray, initial_threshold=Settings.DEFAULT_THRESHOLD_VALUE,
                        delta_t=Settings.DEFAULT_DELTA_T) -> ndarray:
    """
    TODO: Add more documentation.

    :param image: The image for thresholding.
    :param initial_threshold: TODO: Add parameter description.
    :param delta_t: TODO: Add parameter description.
    :return: Threshold image.
    """

    grayscale_image = convert_to_grayscale(image=image)

    log.debug(f"Setting the global threshold to initial (default) value - {initial_threshold}")
    global_threshold = np.round(initial_threshold, 3)

    log.debug("Starting the search for global threshold")
    iteration_counter = 0
    while True:
        iteration_counter += 1  # Update iteration counter.

        # Thresholding the image using the current global threshold.
        boolean_image = grayscale_image > global_threshold

        # Calculating the pixel count for both groups (pixel values below/above the threshold).
        above_threshold_pixel_count = np.count_nonzero(boolean_image)
        below_threshold_pixel_count = grayscale_image.shape[0] * grayscale_image.shape[1] - above_threshold_pixel_count

        # Generating the threshold images.
        above_threshold_image = boolean_image * grayscale_image
        below_threshold_image = grayscale_image - above_threshold_image

        # Calculating the mean for each pixel group.
        above_threshold_mean = np.sum(above_threshold_image) / above_threshold_pixel_count
        below_threshold_mean = np.sum(below_threshold_image) / below_threshold_pixel_count

        # Calculating the new global threshold.
        new_global_threshold = 0.5 * (above_threshold_mean + below_threshold_mean)

        # Checking stopping condition (the difference between the two latest thresholds is lower than defined delta).
        if np.abs(new_global_threshold - global_threshold) < delta_t:
            log.info(f"Global threshold reached - {np.round(global_threshold, 3)} (initial threshold value - {initial_threshold})")
            log.info(f"Iterations to reach global threshold - {iteration_counter}")
            break
        else:
            global_threshold = np.round(new_global_threshold, 3)

    return thresholding(image=grayscale_image, threshold_value=np.round(global_threshold, 3))


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 3 - Some Basic Intensity Transformation Functions, p.175-182")
def laplacian_gradient(image: ndarray, padding_type=Settings.DEFAULT_PADDING_TYPE,
                       include_diagonal_terms=Settings.DEFAULT_INCLUDE_DIAGONAL_TERMS) -> ndarray:
    """
    TODO: Add more documentation.

    :param image: TODO: Add parameter description.
    :param padding_type: TODO: Add parameter description.
    :param include_diagonal_terms: TODO: Add parameter description.
    :return: TODO: Add parameter description.
    """

    laplacian_kernel = LAPLACIAN_KERNELS["WITHOUT_DIAGONAL_TERMS"] if not include_diagonal_terms \
        else LAPLACIAN_KERNELS["WITH_DIAGONAL_TERMS"]

    log.debug("Filtering the image")
    return convolution_2d(image=image, kernel=laplacian_kernel, padding_type=padding_type)


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 10.2 - Point, Line, and Edge Detection, p.706-707")
def isolated_point_detection(image: ndarray, padding_type=Settings.DEFAULT_PADDING_TYPE,
                             include_diagonal_terms=Settings.DEFAULT_INCLUDE_DIAGONAL_TERMS,
                             threshold_value=Settings.DEFAULT_THRESHOLD_VALUE) -> ndarray:
    """
    TODO: Add more documentation.

    :param image: TODO: Add parameter description.
    :param padding_type: TODO: Add parameter description.
    :param include_diagonal_terms: TODO: Add parameter description.
    :param threshold_value: TODO: Add parameter description.
    :return: TODO: Add parameter description.
    """

    # TODO: Add logs.
    post_laplacian_image = laplacian_gradient(image=image, padding_type=padding_type,
                                              include_diagonal_terms=include_diagonal_terms)

    return thresholding(image=np.abs(post_laplacian_image), threshold_value=threshold_value)


@book_implementation(book=Settings.GONZALES_WOODS_BOOK,
                     reference="Chapter 10.2 - Point, Line, and Edge Detection, p.707-710")
def line_detection(image: ndarray, padding_type=Settings.DEFAULT_PADDING_TYPE,
                   threshold_value=Settings.DEFAULT_THRESHOLD_VALUE) -> dict:
    """
    Line detection in an image.
    TODO: Add more documentation.

    :param image: The image used for line detection.
    :param padding_type: The padding type used for the convolution.
    :param threshold_value: The threshold value for post filter image normalization.
    Note - The threshold value is important, because it determines the 'strength' of the gradient. This means that
    higher threshold, will display higher contrast lines.
    :return: Filtered image in all directions.
    """

    filtered_images_dictionary = {}

    log.debug("Filtering the images")
    for direction_kernel in LINE_DETECTION_KERNELS:
        log.debug(f"Current kernel direction is - {direction_kernel}")
        filtered_image = convolution_2d(image=image, kernel=LINE_DETECTION_KERNELS[direction_kernel],
                                        padding_type=padding_type)

        log.debug("Thresholding the absolute value of the pixels")
        filtered_images_dictionary[direction_kernel] = thresholding(image=np.abs(filtered_image),
                                                                    threshold_value=threshold_value)

    return filtered_images_dictionary


@book_implementation(book="Digital Image Processing (4th edition) - Gonzales & Woods",
                     reference="Chapter 10.2 - Point, Line, and Edge Detection, p.720-722")
def kirsch_edge_detection(image: ndarray, padding_type=Settings.DEFAULT_PADDING_TYPE) -> dict:
    """
    Perform Kirsch edge detection on an image. Kirsch's method employs 8 directional 3x3 kernels, where the image is
    convolved with each one. Once finished, a max value image is generated and compared with each direction. A pixel is
    marked for a specific direction when the direction image value equals the max value (indicating that the change in
    that direction is the strongest).

    :param image: The image for Kirsch edge detection.
    :param padding_type: The padding type used for the convolution.
    :return: Filtered image in all directions.
    """

    filtered_images_dictionary = {}

    log.debug("Filtering the image in all directions")
    post_convolution_images = {}
    for direction_kernel in KIRSCH_EDGE_DETECTION_KERNELS:
        log.debug(f"Current direction is - {direction_kernel}")
        post_convolution_images[direction_kernel] = convolution_2d(image=image,
                                                                   kernel=KIRSCH_EDGE_DETECTION_KERNELS[
                                                                       direction_kernel],
                                                                   padding_type=padding_type)

    log.debug("Amassing a maximum values image (for later comparison with every direction)")
    max_value_image = np.zeros(shape=image.shape)
    for post_convolution_image in post_convolution_images:
        boolean_image = (post_convolution_images[post_convolution_image] > max_value_image) \
                        * post_convolution_images[post_convolution_image]
        max_value_image = np.maximum(boolean_image, max_value_image)

    log.debug("Comparing direction images with max values image")
    for direction in KIRSCH_EDGE_DETECTION_KERNELS:
        log.debug(f"Current direction is - {direction}")
        filtered_images_dictionary[direction] = (post_convolution_images[direction] <= max_value_image) \
                                                * post_convolution_images[direction]

    return filtered_images_dictionary
