"""
Script Name - segmentation.py

A simplified profile, with just enough points to make it possible for us to analyze manually how the first- and
second-order derivatives behave as they encounter a point, a line, and the edges of objects. In this diagram the
transition in the ramp spans four pixels, the noise point is a single pixel, the line is three pixels thick, and the
transition of the step edge takes place between adjacent pixels. The number of intensity levels was limited to eight for
simplicity.
                        7                                                                 •  •  •  •
                        6                             • Isolated point
                        5  •  •
                        4        •  Ramp                               Line             Step
                        3           •                                   •
                        2              •
                        1                 •                 Flat     •     •
                        0                    •  •  •     •  •  •  •           •  •  •  •
    Intensity values       5  5  4  3  2  1  0  0  0  6  0  0  0  0  1  3  1  0  0  0  0  7  7  7  7
    First derivative         -1 -1 -1 -1 -1  0  0  6 -6  0  0  0  1  2 -2 -1  0  0  0  0  7  0  0  0
    Second derivative        -1  0  0  0  0  1  0  6 -12 6  0  0  1  1 -4  1  1  0  0  7 -7  0  0  0

Consider the properties of the first and second derivatives as we traverse the profile from left to right. Initially,
the first-order derivative is nonzero at the onset and along the entire intensity ramp, while the second-order
derivative is nonzero only at the onset and end of the ramp. Because the edges of digital images resemble this type of
transition, we conclude that first-order derivatives produce “thick” edges, and second-order derivatives much thinner
ones. Next we encounter the isolated noise point. Here, the magnitude of the response at the point is much stronger for
the second- than for the first-order derivative. This is not unexpected, because a second-order derivative is much more
aggressive than a first-order derivative in enhancing sharp changes. Thus, we can expect second-order derivatives to
enhance fine detail (including noise) much more than first-order derivatives. The line in this example is rather thin,
so it too is fine detail, and we see again that the second derivative has a larger magnitude. Finally, note in both the
ramp and step edges that the second derivative has opposite signs (negative to positive or positive to negative) as it
transitions into and out of an edge. This “double-edge” effect is an important characteristic that can be used to locate
edges, as we will show later in this section. As we move into the edge, the sign of the second derivative is used also
to determine whether an edge is a transition from light to dark (negative second derivative), or from dark to light
(positive second derivative).

In summary, we arrive at the following conclusions:
    (1) First-order derivatives generally produce thicker edges.
    (2) Second-order derivatives have a stronger response to fine detail, such as thin lines, isolated points, and
        noise.
    (3) Second-order derivatives produce a double-edge response at ramp and step transitions in intensity.
    (4) The sign of the second derivative can be used to determine whether a transition into an edge is from light to
        dark or dark to light.

Created by Michael Samelsohn, 20/05/22
"""

# Imports #
import numpy as np
from numpy import ndarray

from common import convolution_2d, convert_to_grayscale
from Settings import image_settings
from Utilities.decorators import book_reference
from Settings.settings import log
from spatial_filtering import laplacian_gradient


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 10.2 - Point, Line, and Edge Detection, p.706-707")
def isolated_point_detection(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                             include_diagonal_terms=image_settings.DEFAULT_INCLUDE_DIAGONAL_TERMS,
                             threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE) -> ndarray:
    """
    Isolated point detection using the Laplacian kernel (second-derivative).
    As seen above, second-order derivatives have a stronger response to fine detail, such as thin lines, isolated
    points, and noise.

    :param image: The image for isolated point detection.
    :param padding_type: Padding type used for applying the kernel.
    :param include_diagonal_terms: Type of Laplacian kernel used for the isolated point detection.
    :param threshold_value: Threshold value used for the thresholding of the post Laplacian image (to remove "weak"
    isolated points).

    :return: Binary image containing the strongest isolated points.
    """

    log.debug("Detecting isolated points")

    # Step I - Applying Laplacian kernel on the image.
    post_laplacian_image = laplacian_gradient(image=image, padding_type=padding_type,
                                              include_diagonal_terms=include_diagonal_terms)

    # Step II - Thresholding the remaining values to remove "weak" points.
    return thresholding(image=np.abs(post_laplacian_image), threshold_value=threshold_value)


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 10.2 - Point, Line, and Edge Detection, p.707-710")
def line_detection(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                   threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE) -> dict:
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

    line_detection_kernels = {
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

    log.debug("Filtering the images")
    for direction_kernel in line_detection_kernels:
        log.debug(f"Current kernel direction is - {direction_kernel}")
        filtered_image = convolution_2d(image=image, kernel=line_detection_kernels[direction_kernel],
                                        padding_type=padding_type)

        log.debug("Thresholding the absolute value of the pixels")
        filtered_images_dictionary[direction_kernel] = thresholding(image=np.abs(filtered_image),
                                                                    threshold_value=threshold_value)

    return filtered_images_dictionary


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 10.2 - Point, Line, and Edge Detection, p.720-722")
def kirsch_edge_detection(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE) -> dict:
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

    kirsch_edge_detection_kernels = {
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

    log.debug("Filtering the image in all directions")
    post_convolution_images = {}
    for direction_kernel in kirsch_edge_detection_kernels:
        log.debug(f"Current direction is - {direction_kernel}")
        post_convolution_images[direction_kernel] = convolution_2d(image=image,
                                                                   kernel=kirsch_edge_detection_kernels[
                                                                       direction_kernel],
                                                                   padding_type=padding_type)

    log.debug("Amassing a maximum values image (for later comparison with every direction)")
    max_value_image = np.zeros(shape=image.shape)
    for post_convolution_image in post_convolution_images:
        boolean_image = (post_convolution_images[post_convolution_image] > max_value_image) \
                        * post_convolution_images[post_convolution_image]
        max_value_image = np.maximum(boolean_image, max_value_image)

    log.debug("Comparing direction images with max values image")
    for direction in kirsch_edge_detection_kernels:
        log.debug(f"Current direction is - {direction}")
        filtered_images_dictionary[direction] = (post_convolution_images[direction] <= max_value_image) \
                                                * post_convolution_images[direction]

    return filtered_images_dictionary


# TODO: Implement the Marr-Hildreth edge detector (LoG) - p.724-729.
# TODO: Implement the Canny edge detector - p.729-735.
# TODO: Implement the Hough transform - p.737-742.


@book_reference(book=image_settings.GONZALES_WOODS_BOOK, reference="Chapter 10.3 - Thresholding, p.742-746")
def thresholding(image: ndarray, threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE) -> ndarray:
    """
    Transforming the image to its binary version using the provided threshold.
    Comparing pixel values against provided threshold. If pixel value is larger, convert it to 1 (white).
    Otherwise, convert it to 0 (black).

    :param image: The image for thresholding.
    :param threshold_value: The threshold value. Acceptable values are - (0, 1).

    :return: The binary image (based on the threshold).
    """

    log.debug("Performing image thresholding")

    log.debug(f"The provided threshold is - {threshold_value}")

    # .astype(float) is used to convert the boolean matrix (generated by the condition check) to a float based one.
    return (image > threshold_value).astype(float)


# TODO: Implement multi-thresholding (Chapter 10.3 - Thresholding, p.743)

@book_reference(book=image_settings.GONZALES_WOODS_BOOK, reference="Chapter 10.3 - Thresholding, p.746-747")
def global_thresholding(image: ndarray, initial_threshold=image_settings.DEFAULT_THRESHOLD_VALUE,
                        delta_t=image_settings.DEFAULT_DELTA_T) -> ndarray:
    """
    When the intensity distributions of objects and background pixels are sufficiently distinct, it is possible to use a
    single (global) threshold applicable over the entire image. In most applications, there is usually enough
    variability between images that, even if global thresholding is a suitable approach, an algorithm capable of
    estimating the threshold value for each image is required.

    :param image: The image for global thresholding.
    :param initial_threshold: Threshold seed.
    :param delta_t: The minimal interval between following threshold values (when the next iteration is less than the
    interval value, the algorithm stops).

    :return: Threshold image.
    """

    grayscale_image = convert_to_grayscale(image=image)

    log.debug(f"Setting the global threshold to initial (default) value - {initial_threshold}")
    global_threshold = np.round(initial_threshold, 3)
    thresholds = []  # Dictionary that appends all threshold values (useful for debug purposes).

    log.debug("Starting the search for the global threshold")
    while True:

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
        new_global_threshold = np.round(0.5 * (above_threshold_mean + below_threshold_mean), 3)
        thresholds.append(new_global_threshold)

        # Checking stopping condition (the difference between the two latest thresholds is lower than defined delta).
        if np.abs(new_global_threshold - global_threshold) < delta_t:
            log.info(f"Global threshold reached - {np.round(global_threshold, 3)} (initial threshold value - {initial_threshold})")
            log.info(f"List of the calculated global thresholds - {thresholds}")
            log.info(f"Iterations to reach global threshold - {len(thresholds)}")
            break
        else:
            global_threshold = np.round(new_global_threshold, 3)

    return thresholding(image=grayscale_image, threshold_value=np.round(global_threshold, 3))


# TODO: Implement the optimum global thresholding using Otsu's method - p.747-752.
