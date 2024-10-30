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
import copy

# Imports #
import numpy as np
from numpy import ndarray

from common import convolution_2d, extract_sub_image
from Settings import image_settings
from Utilities.decorators import book_reference, article_reference
from Settings.settings import log
from spatial_filtering import laplacian_gradient, blur_image, sobel_filter


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

    log.info("Performing isolated points detection using the Laplacian kernel")

    # Applying Laplacian kernel on the image.
    post_laplacian_image = laplacian_gradient(image=image, padding_type=padding_type,
                                              include_diagonal_terms=include_diagonal_terms)

    # Thresholding the remaining values to remove "weak" points.
    return thresholding(image=np.abs(post_laplacian_image), threshold_value=threshold_value)


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 10.2 - Point, Line, and Edge Detection, p.707-710")
def line_detection(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                   threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE) -> dict:
    """
    Line detection in an image.

    If we are interested in detecting all the lines in an image in the direction defined by a given kernel, we simply
    run the kernel through the image and threshold the absolute value of the result. The nonzero points remaining after
    thresholding are the strongest responses which, for lines one pixel thick, correspond closest to the direction
    defined by the kernel.

    :param image: The image used for line detection.
    :param padding_type: The padding type used for the convolution.
    :param threshold_value: The threshold value for post filter image normalization.
    Note - The threshold value is important, because it determines the 'strength' of the gradient. This means that
    higher threshold, will display higher contrast lines.

    :return: Filtered image in all directions.
    """

    log.info("Performing line detection")

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

    log.debug("Filtering the images in all directions")
    filtered_images_dictionary = {}
    for direction_kernel in line_detection_kernels:
        log.debug(f"Current kernel direction is - {direction_kernel}")
        filtered_image = convolution_2d(image=image, kernel=line_detection_kernels[direction_kernel],
                                        padding_type=padding_type)

        # Thresholding the absolute value of the pixels.
        filtered_images_dictionary[direction_kernel] = thresholding(image=np.abs(filtered_image),
                                                                    threshold_value=threshold_value)

    return filtered_images_dictionary


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 10.2 - Point, Line, and Edge Detection, p.720-722")
# TODO: Find the article reference.
def kirsch_edge_detection(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE) -> dict:
    """
    Perform Kirsch edge detection on an image.

    Kirsch's method employs 8 directional 3x3 kernels, where the image is convolved with each one. Once finished, a max
    value image is generated and compared with each direction. A pixel is marked for a specific direction when the
    direction image value equals the max value (indicating that the change in that direction is the strongest).

    :param image: The image for Kirsch edge detection.
    :param padding_type: The padding type used for the convolution.

    :return: Filtered image in all directions.
    """

    log.info("Performing line detection using Kirsch compass kernels")

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
    filtered_images_dictionary = {}
    for direction in kirsch_edge_detection_kernels:
        log.debug(f"Current direction is - {direction}")
        filtered_images_dictionary[direction] = (post_convolution_images[direction] <= max_value_image) \
                                                 * post_convolution_images[direction]

    return filtered_images_dictionary


"""
The edge-detection methods implemented in the previous subsections are based on filtering an image with one or more 
kernels, with no provisions made for edge characteristics and noise content. In this section, we discuss more advanced 
techniques that attempt to improve on simple edge-detection methods by taking into account factors such as image noise 
and the nature of edges themselves.
"""


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 10.2 - Point, Line, and Edge Detection, p.724-729")
@article_reference(article="Marr, D.; Hildreth, E. (29 Feb 1980). \"Theory of Edge Detection\". Proceedings of the "
                           "Royal Society of London. Series B, Biological Sciences. 207 (1167): 187–217")
def marr_hildreth_edge_detection(image: ndarray, filter_size=image_settings.DEFAULT_FILTER_SIZE,
                                 padding_type=image_settings.DEFAULT_PADDING_TYPE, sigma=1,
                                 include_diagonal_terms=image_settings.DEFAULT_INCLUDE_DIAGONAL_TERMS,
                                 threshold=0) -> ndarray:
    """
    Marr and Hildreth [1980] argued that:
    1. Intensity changes are not independent of image scale, implying that their detection requires using operators of
       different sizes
    2. A sudden intensity change will give rise to a peak or trough in the first derivative or, equivalently, to a zero
    crossing in the second derivative.

    These ideas suggest that an operator used for edge detection should have two salient features. First and foremost,
    it should be a differential operator capable of computing a digital approximation of the first or second derivative
    at every point in the image. Second, it should be capable of being “tuned” to act at any desired scale, so that
    large operators can be used to detect blurry edges and small operators to detect sharply focused fine detail.

    Marr and Hildreth suggested that the most satisfactory operator fulfilling these conditions is the filter ∇^2G
    Where ∇^2 is the Laplacian operator and the G stands for the Gaussian 2D function:
                                            G(x,y) = e[-(x^2+y^2)/2sigma^2]
    with standard deviation s (sometimes s is called the space constant in this context). We find an expression for ∇^2G
    by applying the Laplacian:
        ∇^2G(x,y) = ∂^2G(x,y)/∂x^2 + ∂^2G(x,y)/∂y^2 = • • • = [(x^2+y^2-2sigma^2)/sigma^4] * e[-(x^2+y^2)/2sigma^2]
    This expression is called the Laplacian of a Gaussian (LoG). The zero crossings of the LoG occur at x^2+y^2=2sigma^2
    which defines a circle of radius sqrt(2)sigma centered on the peak of the Gaussian function.

    There are two fundamental ideas behind the selection of the operator ∇^2G. First, the Gaussian part of the operator
    blurs the image, thus reducing the intensity of structures (including noise) at scales much smaller than sigma. The
    other idea concerns the second derivative properties of the Laplacian operator, ∇^2. Although first derivatives can
    be used for detecting abrupt changes in intensity, they are directional operators. The Laplacian, on the other hand,
    has the important advantage of being isotropic (invariant to rotation), which not only corresponds to
    characteristics of the human visual system but also responds equally to changes in intensity in any kernel
    direction, thus avoiding having to use multiple kernels to calculate the strongest response at any point in the
    image.

    The Marr-Hildreth algorithm consists of convolving the LoG kernel with an input image. Because the Laplacian and
    convolution are linear processes we can smooth the image first with a Gaussian filter and then compute the Laplacian
    of the result.

    :param image: The image for Kirsch edge detection.
    :param sigma: Value of the sigma used in the Gaussian kernel.
    :param filter_size: Size of the filter used for the convolution with the Gaussian kernel.
    :param padding_type: The padding type used for the convolution with the Gaussian kernel.
    :param include_diagonal_terms: Boolean value determining which Laplacian kernel is used.
    :param threshold: Threshold value used to filter "weaker" edge pixels.

    :return: Filtered image with LoG.
    """

    log.info("Applying the Marr-Hildreth edge detection method on the image")

    # Blurring the image with a Gaussian kernel.
    gaussian_image = blur_image(image=image, filter_type=image_settings.GAUSSIAN_FILTER, filter_size=filter_size,
                                padding_type=padding_type, k=1, sigma=sigma)

    # Applying the Laplacian on the Gaussian image.
    log_image = laplacian_gradient(image=gaussian_image, padding_type=padding_type,
                                   include_diagonal_terms=include_diagonal_terms, normalization_method='unchanged')

    log.debug("Finding the zero crossings of the LoG image")
    marr_hildreth_image = np.zeros(image.shape)
    for row in range(1, image.shape[0] - 1):
        for col in range(1, image.shape[1] - 1):
            # Extract the sub-image for the zero crossing inspection.
            sub_image = extract_sub_image(image=log_image, position=(row, col), sub_image_size=3)
            # Mark the inspected pixel as either 1 (zero crossing above threshold -> edge) or 0.
            marr_hildreth_image[row][col] = zero_crossing(sub_image=sub_image, threshold=threshold)

    return marr_hildreth_image


def zero_crossing(sub_image: ndarray, threshold: float) -> int:
    """
    Helper method for Marr Hildreth edge detection.

    One approach for finding the zero crossings at any pixel, p, of the filtered image, g(x,y), is to use a 3×3
    neighborhood centered at p. A zero crossing at p implies that the signs of at least two of its opposing neighboring
    pixels must differ. There are four cases to test: left/right, up/down, and the two diagonals. If the values of
    g(x,y) are being compared against a threshold (a common approach), then not only must the signs of opposing
    neighbors be different, but the absolute value of their numerical difference must also exceed the threshold before
    we can call p a zero-crossing pixel.

    :param sub_image: 3×3 sub image (extracted from the LoG one).
    :param threshold: Threshold value used to filter "weaker" edge pixels.

    :return: 1 if pixel is designated as a zero crossing, 0 otherwise.
    """

    # Check horizontal line.
    if (((sub_image[1][0] > 0 > sub_image[1][2]) or (sub_image[1][2] > 0 > sub_image[1][0]))
            and (np.abs(sub_image[1][2] - sub_image[1][0]) > threshold)):
        return 1
    # Check vertical line.
    elif (((sub_image[0][1] > 0 > sub_image[2][1]) or (sub_image[2][1] > 0 > sub_image[0][1]))
            and (np.abs(sub_image[2][1] - sub_image[0][1]) > threshold)):
        return 1
    # Check forward slash \.
    elif (((sub_image[0][0] > 0 > sub_image[2][2]) or (sub_image[2][2] > 0 > sub_image[0][0]))
            and (np.abs(sub_image[2][2] - sub_image[0][0]) > threshold)):
        return 1
    # Check backward slash /.
    elif (((sub_image[0][2] > 0 > sub_image[2][0]) or (sub_image[2][0] > 0 > sub_image[0][2]))
            and (np.abs(sub_image[2][0] - sub_image[0][2]) > threshold)):
        return 1
    else:
        return 0

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

    log.info(f"Performing image thresholding with threshold value of {threshold_value}")
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

    # TODO: Add an assumption that the image is grayscale.

    log.info(f"Performing global thresholding, with initial value {initial_threshold}")

    log.debug("Starting the search for the global threshold")
    threshold_image = copy.deepcopy(image)
    thresholds = []  # Dictionary that appends all threshold values (useful for debug purposes).
    global_threshold = np.round(initial_threshold, 3)
    while True:
        # Thresholding the image using the current global threshold.
        boolean_image = threshold_image > global_threshold

        # Calculating the pixel count for both groups (pixel values below/above the threshold).
        above_threshold_pixel_count = np.count_nonzero(boolean_image)
        below_threshold_pixel_count = threshold_image.shape[0] * threshold_image.shape[1] - above_threshold_pixel_count

        # Generating the threshold images.
        above_threshold_image = boolean_image * threshold_image
        below_threshold_image = threshold_image - above_threshold_image

        # Calculating the mean for each pixel group.
        above_threshold_mean = np.sum(above_threshold_image) / above_threshold_pixel_count
        below_threshold_mean = np.sum(below_threshold_image) / below_threshold_pixel_count

        # Calculating the new global threshold.
        new_global_threshold = np.round(0.5 * (above_threshold_mean + below_threshold_mean), 3)
        thresholds.append(new_global_threshold)

        # Checking stopping condition (the difference between the two latest thresholds is lower than defined delta).
        if np.abs(new_global_threshold - global_threshold) < delta_t:
            log.info(f"Global threshold reached - {np.round(global_threshold, 3)} "
                     f"(initial threshold value - {initial_threshold})")
            log.info(f"List of the calculated global thresholds - {thresholds}")
            log.info(f"Iterations to reach global threshold - {len(thresholds)}")
            break
        else:
            global_threshold = np.round(new_global_threshold, 3)

    return thresholding(image=threshold_image, threshold_value=np.round(global_threshold, 3))


# TODO: Implement the optimum global thresholding using Otsu's method - p.747-752.
