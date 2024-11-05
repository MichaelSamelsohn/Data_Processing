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

from common import convolution_2d, extract_sub_image, calculate_histogram
from Settings import image_settings
from Utilities.decorators import book_reference, article_reference
from Settings.settings import log
from spatial_filtering import laplacian_gradient, blur_image, sobel_filter


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 10.2 - Point, Line, and Edge Detection, p.706-707")
def isolated_point_detection(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                             normalization_method=image_settings.DEFAULT_NORMALIZATION_METHOD,
                             include_diagonal_terms=image_settings.DEFAULT_INCLUDE_DIAGONAL_TERMS,
                             threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE) -> ndarray:
    """
    Isolated point detection using the Laplacian kernel (second-derivative).
    As seen above, second-order derivatives have a stronger response to fine detail, such as thin lines, isolated
    points, and noise.

    :param image: The image for isolated point detection.
    :param padding_type: Padding type used for applying the kernel.
    :param normalization_method: Method used for image normalization. Options are - unchanged, stretch, cutoff.
    :param include_diagonal_terms: Type of Laplacian kernel used for the isolated point detection.
    :param threshold_value: Threshold value used for the thresholding of the post Laplacian image (to remove "weak"
    isolated points).

    :return: Binary image containing the strongest isolated points.
    """

    log.info("Performing isolated points detection using the Laplacian kernel")

    # Applying Laplacian kernel on the image.
    post_laplacian_image = laplacian_gradient(image=image, padding_type=padding_type,
                                              include_diagonal_terms=include_diagonal_terms,
                                              normalization_method=normalization_method)

    # Thresholding the remaining values to remove "weak" points.
    return thresholding(image=np.abs(post_laplacian_image), threshold_value=threshold_value)


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 10.2 - Point, Line, and Edge Detection, p.707-710")
def line_detection(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                   normalization_method=image_settings.DEFAULT_NORMALIZATION_METHOD,
                   threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE) -> dict:
    """
    Line detection in an image.

    If we are interested in detecting all the lines in an image in the direction defined by a given kernel, we simply
    run the kernel through the image and threshold the absolute value of the result. The nonzero points remaining after
    thresholding are the strongest responses which, for lines one pixel thick, correspond closest to the direction
    defined by the kernel.

    :param image: The image used for line detection.
    :param padding_type: The padding type used for the convolution.
    :param normalization_method: Method used for image normalization. Options are - unchanged, stretch, cutoff.
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
                                        padding_type=padding_type, normalization_method=normalization_method)

        # Thresholding the absolute value of the pixels.
        filtered_images_dictionary[direction_kernel] = thresholding(image=np.abs(filtered_image),
                                                                    threshold_value=threshold_value)

    return filtered_images_dictionary


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 10.2 - Point, Line, and Edge Detection, p.720-722")
@article_reference(article="Kirsch, R. [1971]. “Computer Determination of the Constituent Structure of Biological "
                           "Images,” Comput. Biomed. Res., vol. 4, pp. 315–328")
def kirsch_edge_detection(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                          normalization_method=image_settings.DEFAULT_NORMALIZATION_METHOD,
                          compare_max_value=True) -> dict:
    """
    Perform Kirsch edge detection on an image.

    Kirsch's method employs 8 directional 3x3 kernels, where the image is convolved with each one. Once finished, a max
    value image is generated and compared with each direction. A pixel is marked for a specific direction when the
    direction image value equals the max value (indicating that the change in that direction is the strongest).

    :param image: The image for Kirsch edge detection.
    :param padding_type: The padding type used for the convolution.
    :param normalization_method: Method used for image normalization. Options are - unchanged, stretch, cutoff.
    :param compare_max_value: Boolean value specifying whether to perform part 2 (comparing directions with max values) of the
    Kirsch edge detection algorithm.

    :return: Filtered image in all directions.
    """

    log.info(f"Performing line detection using Kirsch compass kernels "
             f"{'(compass kernel convolution only)' if not compare_max_value else ''}")

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
        post_convolution_images[direction_kernel] = convolution_2d(
            image=image, kernel=kirsch_edge_detection_kernels[direction_kernel],
            padding_type=padding_type, normalization_method='unchanged' if compare_max_value else normalization_method)

    if not compare_max_value:
        log.warning("Returning images without comparison of max values")
        return post_convolution_images

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
        filtered_images_dictionary[direction] = ((post_convolution_images[direction] == max_value_image) *
                                                 post_convolution_images[direction])

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
                                 padding_type=image_settings.DEFAULT_PADDING_TYPE,
                                 sigma=image_settings.DEFAULT_SIGMA_VALUE,
                                 include_diagonal_terms=image_settings.DEFAULT_INCLUDE_DIAGONAL_TERMS,
                                 threshold=image_settings.DEFAULT_THRESHOLD_VALUE) -> ndarray:
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
                                padding_type=padding_type, sigma=sigma)

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


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 10.2 - Point, Line, and Edge Detection, p.729-735")
@article_reference(article="Canny, J. [1986]. “A Computational Approach for Edge Detection,” IEEE Trans. Pattern Anal. "
                           "Machine Intell., vol. 8, no. 6, pp. 679–698")
def canny_edge_detection(image: ndarray, filter_size=image_settings.DEFAULT_FILTER_SIZE,
                         padding_type=image_settings.DEFAULT_PADDING_TYPE, sigma=image_settings.DEFAULT_SIGMA_VALUE,
                         high_threshold=image_settings.DEFAULT_HIGH_THRESHOLD_CANNY,
                         low_threshold=image_settings.DEFAULT_LOW_THRESHOLD_CANNY) -> ndarray:
    """
    Canny’s approach is based on three basic objectives:
    1. Low error rate. All edges should be found, and there should be no spurious responses.
    2. Edge points should be well localized. The edges located must be as close as possible to the true edges. That is,
       the distance between a point marked as an edge by the detector and the center of the true edge should be minimum.
    3. Single edge point response. The detector should return only one point for each true edge point. That is, the
       number of local maxima around the true edge should be minimum. This means that the detector should not identify
       multiple edge pixels where only a single edge point exists.
    The essence of Canny’s work was in expressing the preceding three criteria mathematically, and then attempting to
    find optimal solutions to these formulations.

    The essence of Canny’s work was in expressing the preceding three criteria mathematically, and then attempting to
    find optimal solutions to these formulations. In general, it is difficult (or impossible) to find a closed-form
    solution that satisfies all the preceding objectives. However, using numerical optimization with 1-D step edges
    corrupted by additive white Gaussian noise led to the conclusion that a good approximation to the optimal step edge
    detector is the first derivative of a Gaussian, where the approximation was only about 20% worse that using the
    optimized numerical solution (a difference of this magnitude generally is visually imperceptible in most
    applications).

    Generalizing the preceding result to 2-D involves recognizing that the 1-D approach still applies in the direction
    of the edge normal (see Fig. 10.12). Because the direction of the normal is unknown beforehand, this would require
    applying the 1-D edge detector in all possible directions. This task can be approximated by first smoothing the
    image with a circular 2-D Gaussian function, computing the gradient of the result, and then using the gradient
    magnitude and direction to estimate edge strength and direction at every point.

    The Canny edge detection algorithm consists of the following steps:
    1. Smooth the input image with a Gaussian filter.
    2. Compute the gradient magnitude and angle images.
    3. Apply nonmaxima suppression to the gradient magnitude image.
    4. Use double thresholding and connectivity analysis to detect and link edges.

    :param image: The image for edge detection.
    :param filter_size: Size of the filter used for the convolution with the Gaussian kernel.
    :param padding_type: The padding type used for the convolution with the Gaussian kernel.
    :param sigma: Value of the sigma used in the Gaussian kernel.
    :param high_threshold: The high threshold value used for the hysteresis.
    :param low_threshold: The low threshold value used for the hysteresis.
    Note - Experimental evidence (Canny [1986]) suggests that the ratio of the high to low threshold should be in the
    range of 2:1 to 3:1.

    :return: Binary image showing edges using the Canny edge detection method.
    """

    log.info("Applying the Canny edge detection method on the image")

    # Smoothing (blurring) the image with a Gaussian kernel.
    gaussian_image = blur_image(image=image, filter_type=image_settings.GAUSSIAN_FILTER, filter_size=filter_size,
                                padding_type=padding_type, sigma=sigma)

    # Computing the gradient magnitude and direction (using the Sobel filter).
    gradient_images = sobel_filter(image=gaussian_image, padding_type=padding_type, normalization_method='unchanged')
    magnitude_image, direction_image = gradient_images["Magnitude"], gradient_images["Direction"]

    # Applying non-maxima suppression to the gradient images.
    suppression_image = non_maxima_suppression(magnitude_image=magnitude_image, direction_image=direction_image)

    # Double (hysteresis) thresholding.
    canny_image = hysteresis_thresholding(suppression_image=suppression_image,
                                          high_threshold=high_threshold, low_threshold=low_threshold)

    return canny_image


def non_maxima_suppression(magnitude_image: ndarray, direction_image: ndarray):
    """
    Gradient images typically contain wide ridges around local maxima. To thin those ridges, one approach is to use
    nonmaxima suppression. The essence of this approach is to specify a number of discrete orientations of the edge
    normal (gradient vector). For example, in a 3×3 region we can define four orientations for an edge passing through
    the center point of the region: horizontal, vertical, +45° and −45°. Because we have to quantize all possible edge
    directions into four ranges, we have to define a range of directions over which we consider an edge to be
    horizontal. We determine edge direction from the direction of the edge normal, which we obtain directly from the
    direction image data. For example, if the edge normal is in the range of directions from −22.5° to 22.5° or from
    −157.5° to 157.5°, we call the edge a horizontal edge.

    Let d1, d2, d3, and d4 denote the four basic edge directions just discussed for a 3×3  region: horizontal, −45°,
    vertical, and +45°, respectively. We can formulate the following nonmaxima suppression scheme for a 3×3 region
    centered at an arbitrary point (x,y) in the direction image:
    1. Find the direction dk that is closest to a(x,y).
    2. Let K denote the value of the magnitude at (x,y). If K is less than the value of the magnitude at one or both of
       the neighbors of point (x,y) along dk - suppression.

    :param magnitude_image: Magnitude image.
    :param direction_image: Direction image.

    :return: Suppressed image.
    """

    log.debug("Converting the direction image to angles (for simplicity)")
    angle_image = direction_image * 180.0 / np.pi  # max -> 180°, min -> -180°.
    """
    Since the directions have opposite symmetry, it is easier to normalize the angle values to fit in the interval of 
    [0, 180°]. This simplifies the if-conditions for finding the direction dk. Therefore, all negative angles are 
    incremented by a value of pi.
    """
    angle_image[angle_image < 0] += 180  # max -> 180°, min -> 0°.

    suppression_image = copy.deepcopy(magnitude_image)
    for row in range(1, magnitude_image.shape[0] - 1):
        for col in range(1, magnitude_image.shape[1] - 1):
            # Find the direction dk that is closest to angle(x,y).
            alpha = angle_image[row][col]  # The angle value.
            adjacent_magnitude_values = [0, 0]
            if (0 <= alpha < 22.5) or (157.5 <= alpha <= 180):
                # Horizontal edge direction.
                adjacent_magnitude_values = [magnitude_image[row][col - 1], magnitude_image[row][col + 1]]
            elif 22.5 <= alpha < 67.5:
                # -45° edge direction.
                adjacent_magnitude_values = [magnitude_image[row - 1][col + 1], magnitude_image[row + 1][col - 1]]
            elif 67.5 <= alpha < 112.5:
                # Vertical edge direction.
                adjacent_magnitude_values = [magnitude_image[row - 1][col], magnitude_image[row + 1][col]]
            elif 112.5 <= alpha < 157.5:
                # +45° edge direction.
                adjacent_magnitude_values = [magnitude_image[row + 1][col + 1], magnitude_image[row - 1][col - 1]]

            # Suppression.
            if magnitude_image[row][col] < max(adjacent_magnitude_values):
                suppression_image[row][col] = 0

    return suppression_image


def hysteresis_thresholding(suppression_image: ndarray, high_threshold: float, low_threshold: float) -> ndarray:
    """
    Reduce false edge points using hysteresis thresholding, which uses two thresholds: a low threshold, TL and a high
    threshold, TH. Experimental evidence (Canny [1986]) suggests that the ratio of the high to low threshold should be
    in the range of 2:1 to 3:1.

    When both threshold images are generated, we eliminate the high threshold image from the low threshold one, to
    create a distinction between the two - "strong" edge pixels in the high threshold image, and "weak" ones in the low
    threshold image. The "strong" edge pixels are marked immediately. Depending on the value of TH, the edges in the
    high threshold image typically have gaps.

    Longer edges are formed using the following procedure:
    (a) Locate the next unvisited edge pixel, p, in high_threshold_image(x,y).
    (b) Mark as valid edge pixels all the weak pixels in low_threshold_image(x,y) that are connected to
        p using, 8-connectivity.
    (c) If all nonzero pixels in high_threshold_image(x,y) have been visited go to Step (d). Else, return
        to Step (a).
    (d) Set to zero all pixels in low_threshold_image(x,y) that were not marked as valid edge pixels.

    :param suppression_image: Suppressed image.
    :param high_threshold: High threshold used for the hysteresis thresholding.
    :param low_threshold: Low threshold used for the hysteresis thresholding.

    :return: Hysteresis image.
    """

    log.info("Performing hysteresis thresholding")

    log.debug("High threshold - \"Strong\" edge pixels")
    high_suppression_image = thresholding(image=suppression_image, threshold_value=high_threshold)
    log.debug("High threshold - \"Weak\" edge pixels")
    low_suppression_image = thresholding(image=suppression_image, threshold_value=low_threshold)
    low_suppression_image -= high_suppression_image

    log.debug("Connectivity analysis (to detect and link edges)")
    hysteresis_image = copy.deepcopy(high_suppression_image)
    for row in range(1, low_suppression_image.shape[0] - 1):
        for col in range(1, low_suppression_image.shape[1] - 1):
            if low_suppression_image[row][col] == 1:
                # Extract the 3x3 neighborhood (to find "strong" pixels nearby).
                sub_image = extract_sub_image(image=high_suppression_image, position=(row, col), sub_image_size=3)
                if np.sum(sub_image) > 0:
                    # At least one "strong" pixel is an 8-neighbor.
                    hysteresis_image[row][col] = 1

    return hysteresis_image


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

    The following iterative algorithm can be used for this purpose:
    1. Select an initial estimate for the global threshold, T.
    2. Segment the image using T. This will produce two groups of pixels: G1, consisting of pixels with intensity
       values > T; and G2 , consisting of pixels with values ≤ T.
    3. Compute the average (mean) intensity values m1 and m2 for the pixels in G1 and G2 , respectively.
    4. Compute a new threshold value T, midway between m1 and m2.
    5. Repeat Steps 2 through 4 until the difference between values of T in successive iterations is smaller than a
       predefined value, delta_T.

    The algorithm is stated here in terms of successively thresholding the input image and calculating the means at each
    step, because it is more intuitive to introduce it in this manner. However, it is possible to develop an equivalent
    (and more efficient) procedure by expressing all computations in the terms of the image histogram, which has to be
    computed only once.

    The preceding algorithm works well in situations where there is a reasonably clear valley between the modes of the
    histogram related to objects and background. Parameter delta_T is used to stop iterating when the changes in
    threshold values is small. The initial threshold must be chosen greater than the minimum and less than the maximum
    intensity level in the image (the average intensity of the image is a good initial choice for T). If this condition
    is met, the algorithm converges in a finite number of steps, whether or not the modes are separable.

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


@book_reference(book=image_settings.GONZALES_WOODS_BOOK, reference="Chapter 10.3 - Thresholding, p.747-752")
@article_reference(article="Otsu, N. [1979]. “A Threshold Selection Method from Gray-Level Histograms,” IEEE Trans. "
                           "Systems, Man, and Cybernetics, vol. 9, no. 1, pp. 62–66.")
def otsu_global_thresholding(image: ndarray) -> ndarray:
    """
    A nonparametric and unsupervised method of automatic threshold selection for picture segmentation is presented. An
    optimal threshold is selected by the discriminant criterion, namely, to maximize the separability of the resultant
    classes in gray levels. The procedure is very simple, utilizing only the zeroth- and the first-order cumulative
    moments of the gray-level histogram.

    :param image: The image to be thresholded by Otsu's method.

    :return: thresholded image.
    """

    log.info("Performing Otsu's global thresholding")

    # Calculating the normalized histogram of the image.
    histogram = calculate_histogram(image=image, normalize=True)
    intensity_levels = len(histogram)
    log.debug(f"Intensity levels in the provided image (deducted from the histogram) - {intensity_levels}")

    log.debug("Computing the cumulative sums")
    cumulative_sum = np.zeros(intensity_levels)
    for k in range(intensity_levels):
        cumulative_sum[k] = np.sum([histogram[i] for i in range(k)])

    log.debug("Computing the cumulative means (average intensity)")
    cumulative_mean = np.zeros(intensity_levels)
    for k in range(intensity_levels):
        cumulative_mean[k] = np.sum([histogram[i] * i for i in range(k)])

    log.debug("Computing the global mean (average intensity of the entire image)")
    global_mean = cumulative_mean[-1]  # Private case when k=L-1.

    log.debug("Computing the between-class variance term")
    between_class_variance = np.zeros(intensity_levels)
    for k in range(intensity_levels):
        between_class_variance[k] = ((np.power(global_mean * cumulative_sum[k] - cumulative_mean[k], 2))
                                     / (cumulative_sum[k] * (1 - cumulative_sum[k])))
    """
    Since cumulative_sum[k] could equal to 0, this means that the denominator can equal 0, which eventually leads to 
    'nan' values. Therefore, we eliminate all those options by turning them to zero.
    """
    between_class_variance[np.isnan(between_class_variance)] = 0

    log.debug("Obtaining the Otsu threshold, as the value of k for which maximizes the between-class variance")
    max_indexes = np.argwhere(between_class_variance == np.amax(between_class_variance)).flatten().tolist()
    # If the maximum is not unique, obtain the threshold by averaging the values of k corresponding to the various
    # maxima detected.
    otsu_threshold = np.mean(max_indexes)
    log.debug(f"Otsu's threshold value (un-normalized) is - {otsu_threshold}")

    log.debug("Computing the global variance (intensity variance of all the pixels in the image)")
    global_variance = np.sum([np.power(i - global_mean, 2) * histogram[i] for i in range(intensity_levels)])
    log.debug("Computing the separability measure for otsu's threshold")
    separability_measure = between_class_variance[int(otsu_threshold)] / global_variance
    log.info(f"Separability measure - {separability_measure}")

    # Thresholding the image with Otsu's threshold value.
    """
    Since we are working with the histogram data (presented as an array with integer indexes starting with 0), it is 
    easier to continue working that way. However, since the image pixel values are in range of [0, 1], we need to 
    normalize the threshold we got.
    """
    otsu_threshold /= intensity_levels
    return thresholding(image=image, threshold_value=otsu_threshold)


@article_reference(article="[T. Y. Zhang and C. Y. Suen. A Fast Parallel Algorithm for Thinning Digital Patterns. "
                           "Communications of the ACM, 27(3):236–239, 1984")
def thinning(image: ndarray) -> ndarray:
    """
    A fast parallel thinning algorithm. It consists of two sub-iterations:
    • one aimed at deleting the south-east boundary points and the north-west corner points
    • one is aimed at deleting the north-west boundary points and the south-east corner points.
    End points and pixel connectivity are preserved. Each pattern is thinned down to a "skeleton" of unitary thickness.

    A binary digitized picture is defined by a matrix IT where each pixel IT(i, j) is either 1 or 0. The pattern
    consists of those pixels that have value 1 (therefore, the algorithm should only apply to pixels with value 1).
    Each stroke in the pattern is more than one element thick. Iterative transformations are applied to matrix IT point
    by point according to the values of a small set of neighboring points.

    It is assumed that a 3x3 window is used, and that each element is connected with its eight neighboring elements (no
    need to apply the algorithm to image edges).
    The algorithm presented in this paper requires only simple computations.

    The process continues until no pixels are identified as contour points (only the skeleton remains, nothing else to
    thin out). Therefore, between each sub-iteration, a check is performed to see how many contour points were
    identified.

    :param image: Binary image for thinning.

    :return: Skeleton of the original binary image.
    """

    log.info("Performing image thinning")

    # Copying the image as to not disturb the original.
    skeleton_image = copy.deepcopy(image)

    iteration_counter = 0  # For debug purposes.
    while True:
        iteration_counter += 1
        log.debug(f"Iteration #{iteration_counter}")

        # Sub-iteration 1.
        skeleton_image, contour_pixels = thinning_sub_iteration(binary_image=skeleton_image, sub_iteration=1)
        log.debug(f"Contour pixels found in sub-iteration 1 - {contour_pixels}")

        # Stop condition check.
        if contour_pixels == 0:
            log.debug("No new contour pixels found, process finished")
            break

        # Sub-iteration 2.
        skeleton_image, contour_pixels = thinning_sub_iteration(binary_image=skeleton_image, sub_iteration=2)
        log.debug(f"Contour pixels found in sub-iteration 2 - {contour_pixels}")

        # Stop condition check.
        if contour_pixels == 0:
            log.debug("No new contour pixels found, process finished")
            break

    return skeleton_image


def thinning_sub_iteration(binary_image: ndarray, sub_iteration: int) -> (ndarray, int):
    """
    Designations of the nine pixels in a 3 x 3 window, where P1 is the pixel under check:

                                                P9  P2  P3

                                                P8  P1  P4

                                                P7  P6  P5

    the contour point P1 is deleted from the digital pattern if it satisfies the following conditions:
    (a) 2 <= B(P1) <= 6  # B(P1) is the number of nonzero neighbors of P1 = B(P1) = P2 + P3 + P4 + • • • + P8 + P9.
    (b) A(P1)= 1         # A(P1) is the number of 01 patterns in the ordered set P2, P3, P4, • • • P8, P9, P2.
    (c) P2*P4*P6 = 0     # (c') P2*P4*P8 = 0 (for sub-iteration 2).
    (d) P4*P6*P8 = 0     # (d') P2*P6*P8 = 0 (for sub-iteration 2)

    Condition (a) preserves the endpoints of a skeleton line.
    Condition (b) prevents the deletion of those points that lie between the endpoints of a skeleton line.

    The solution to the set of (c) and (d) is - P4 = 0 or P6 = 0 or (P2 = 0 and P8 = 0). So the point P1, which has been
    removed, might be an east or south boundary point or a north-west corner point.

    The solution to the set of (c') and (d') is - P2 = 0 or P8 = 0 or (P4 = 0 and P6 = 0). So the point P1, which has
    been removed, might be a west or north boundary point or a south-east corner point.

    Firstly, the pixels are identified as contour points. Secondly, they are removed from the image.

    :param binary_image: Binary image for thinning.
    :param sub_iteration: Index indicating which sub-iteration is currently running.

    :return: Thinned binary image.
    """

    contour_image = np.zeros(binary_image.shape)

    contour_points = 0
    for row in range(1, binary_image.shape[0] - 1):
        for col in range(1, binary_image.shape[1] - 1):
            # Checking pixel value.
            if binary_image[row][col] == 0:
                continue  # If the pixel is black it can't be part of a contour.

            # Extract the sub-image.
            sub_image = extract_sub_image(image=binary_image, position=(row, col), sub_image_size=3)
            # Arrange pixels values in an array (clockwise order).
            neighborhood_array = [sub_image[0, 1], sub_image[0, 2],
                                  sub_image[1, 2], sub_image[2, 2], sub_image[2, 1],
                                  sub_image[2, 0], sub_image[1, 0], sub_image[0, 0]]

            # Condition (a) calculation - B(P1).
            b = np.sum(neighborhood_array[1:])

            # Condition (b) calculation - A(P1).
            n = neighborhood_array + neighborhood_array[0:1]
            a = sum((p1, p2) == (0, 1) for p1, p2 in zip(n, n[1:]))

            # Sub-iteration 1 - Condition (c) calculation - P2*P4*P6 = 0.
            # Sub-iteration 2 - Condition (c') calculation - P2*P4*P8 = 0.
            c = neighborhood_array[0] * neighborhood_array[2] * neighborhood_array[4 if sub_iteration == 1 else 6]

            # Sub-iteration 1 - Condition (d) calculation - P4*P6*P8 = 0.
            # Sub-iteration 2 - Condition (d') calculation - P2*P6*P8 = 0.
            d = neighborhood_array[2 if sub_iteration == 1 else 0] * neighborhood_array[4] * neighborhood_array[6]

            # Check if all conditions are met -> contour point.
            if (2 <= b <= 6) and (a == 1) and (c == 0) and (d == 0):
                # Found a contour point (to be removed).
                contour_points += 1
                contour_image[row, col] = 1

    return binary_image - contour_image, contour_points
