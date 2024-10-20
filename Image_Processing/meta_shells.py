# Imports #
import cmath

from Utilities.decorators import article_reference
from common import *
from spatial_filtering import *
from segmentation import *
from morphological_operations import *
from intensity_transformations import *
from Settings.settings import log


@measure_runtime
def noiseless_doublet(image: ndarray) -> ndarray:
    """
    TODO: Complete the docstring.
    """

    log.debug("Stretching the contrast of the image")
    stretched_image = contrast_stretching(image=image)

    log.debug("Thresholding the image to extract the high intensity contour")
    high_intensity_contour = thresholding(image=stretched_image, threshold_value=0.75)

    log.debug("Thresholding the negative image to extract the low intensity contour")
    negative_image = negative(image=stretched_image)
    low_intensity_contour = thresholding(image=negative_image, threshold_value=0.75)

    log.debug("Blurring the image to join the two intensity contours")
    blurred = blur_image(image=low_intensity_contour + high_intensity_contour, filter_size=11)
    log.debug("Thresholding the blurred image to obtain a blob centered on the required line")
    blob = global_thresholding(image=blurred, initial_threshold=0.1)

    return blob


@article_reference(article="[T. Y. Zhang and C. Y. Suen. A Fast Parallel Algorithm for Thinning Digital Patterns. "
                           "Communications of the ACM, 27(3):236–239, 1984")
@measure_runtime
def thinning(binary_image: ndarray) -> ndarray:
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

    :param binary_image: Binary image for thinning.

    :return: Skeleton of the original binary image.
    """

    log.debug("Performing image thinning")

    log.debug("Asserting image is binary")
    if not np.array_equal(binary_image, binary_image.astype(bool)):
        log.error("Provided image is not binary")
        return binary_image

    # Copying the image as to not disturb the original.
    skeleton_image = copy.deepcopy(binary_image)

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


@measure_runtime
def extract_skeleton_parameters(skeleton_image: ndarray) -> (list[(int, int)], list[float]):
    """
    Extract important parameters (link indexes and distances) of the skeleton image.

    Assumptions:
    1) Only a single connected skeleton exists in the provided image.
    2) The skeleton is within the image borders.
    3) The skeleton is of unitary thickness.

    :param skeleton_image: Skeleton image.

    :return: Array of link indexes and array of link distances.
    """

    # Copying the image as to not disturb the original.
    snake_image = copy.deepcopy(skeleton_image)  # Helper image.
    skeleton_links = []  # Return array containing the indexes (rows and columns) of the skeleton.
    skeleton_link_distances = []  # Return array containing the distances between adjacent links of the skeleton.

    log.debug("Finding first skeleton link")
    link = find_first_link_pixel(skeleton_image=skeleton_image)
    skeleton_links.append(link)
    snake_image[link[0], link[1]] = 0  # Removing the first link from the skeleton.

    log.debug("Connecting skeleton links")
    while True:
        # Extract the local 3x3 neighborhood.
        link_neighborhood = extract_sub_image(image=snake_image, position=link, sub_image_size=3)
        """
        Since we are assuming unitary thickness, the closest pixel with value 1 is next link, therefore, the order of 
        the neighbor pixels is arranged as to have the vertical/horizontal ones checked first as they are the closest, 
        followed by the diagonal ones. 
        """
        link_neighborhood_array = {
            # Horizontal/Vertical neighbors.
            (-1, 0): link_neighborhood[0, 1], (0, 1): link_neighborhood[1, 2],
            (1, 0): link_neighborhood[2, 1], (0, -1): link_neighborhood[1, 0],
            # Diagonal neighbors.
            (-1, -1): link_neighborhood[0, 0], (-1, 1): link_neighborhood[0, 2],
            (1, 1): link_neighborhood[2, 2], (1, -1): link_neighborhood[2, 0]
        }
        is_new_link = False  # Used as a check for the stop condition.
        for position in link_neighborhood_array:
            if link_neighborhood_array[position] == 1:
                # Found the closest link.
                link = (link[0] + position[0], link[1] + position[1])
                skeleton_links.append(link)
                skeleton_link_distances.append(np.sqrt(position[0] ** 2 + position[1] ** 2))
                snake_image[link[0]][link[1]] = 0  # Removing the link from the skeleton.
                is_new_link = True  # Found new link.
                break

        # Stop condition check - No new link found (the image is black).
        if not is_new_link:
            log.debug("No new link found (skeleton recovered)")
            log.debug(f"Total links in skeleton - {len(skeleton_links)}")
            # Calculate the distance from last link to first one.
            skeleton_link_distances.append((np.sqrt((skeleton_links[0][0] - skeleton_links[-1][0]) ** 2 +
                                                    (skeleton_links[0][1] - skeleton_links[-1][1]) ** 2)))
            break

    return skeleton_links, skeleton_link_distances


def find_first_link_pixel(skeleton_image: ndarray) -> (int, int):
    """
    Find the first link in a skeleton image by scanning the image for the first pixel with 1 value.

    :param skeleton_image: Binary image (with a unitary thickness skeleton object).

    :return: Tuple containing the row and column values of the first link.
    """

    for row in range(1, skeleton_image.shape[0] - 1):
        for col in range(1, skeleton_image.shape[1] - 1):
            if skeleton_image[row][col] == 1:
                first_link = (row, col)
                log.debug(f"Found first skeleton link - {first_link}")
                return first_link  # Found the first link, no need to continue.


@measure_runtime
def find_equal_distance_pixels(number_of_pixels: int, skeleton_links: list[(int, int)],
                               skeleton_link_distances: list[float]) -> list[(float, float)]:
    """
    Find all equal distance indexes of a skeleton image.
    Note - The returned indexes aren't necessarily integer values, as interpolation is used to equalize the distance.

    Assumptions:
    1) number_of_points is smaller than len(skeleton_indexes).

    :param number_of_pixels: Number of pixels for extraction.
    :param skeleton_links: Indexes of the links in the skeleton image.
    :param skeleton_link_distances: distances between each link in the skeleton image.

    :return: array of indexes of the skeleton spaced with equal distance.
    """

    # TODO: Assert that len(skeleton_indexes) == len(skeleton_distances).

    pixel_coordinates = [skeleton_links[0]]  # The first link is the first index.

    # Calculating the total distance.
    total_distance = sum(skeleton_link_distances)
    log.debug(f"Total distance of skeleton - {total_distance}")

    # Calculating the interval between each equal distance index.
    interval_distance = total_distance / number_of_pixels
    log.debug(f"Interval distance is - {interval_distance}")

    distance = 0  # Used for measuring covered distance.
    for i in range(len(skeleton_links)):
        distance += skeleton_link_distances[i]
        if distance >= interval_distance:
            # Crossed the interval distance.

            # Calculate the distance needed versus remainder.
            remainder = distance - interval_distance
            complementary_distance = skeleton_link_distances[i] - remainder

            # Calculate and append the exact interpolated points.
            pixel_coordinates.append(interpolate_line_point(p1=skeleton_links[i], p2=skeleton_links[i + 1],
                                                            d=complementary_distance))

            distance = remainder  # Reset the distance counter to the remainder.

    return pixel_coordinates


def interpolate_line_point(p1: (int, int), p2: (int, int), d: float) -> (float, float):
    """
    Purpose - Find a point, p3, located on the line connecting p1 and p2, and is at a distance d from p1 located between
    p1 and p2.

    Assumption - The distance d is smaller than the distance between p1 and p2.

    Solution:
    Let's denote the two points as: p1 = (x1,y1), p2 = (x2,y2).
    Equation for the line connecting p1 and p2: y-y1 = m(x-x1) =>
                                      (1)  y = y1+m(x-x1), m=(y1-y2)/(x1-x2)

    Let's write the conditions that satisfy point p3:
    Distance equation (2): (x3-x1)^2 + (y3-y1)^2 = d^2
    Line equation     (3): y3 = y1+m(x3-x1)

    We insert (3) to (2) and receive: (x3-x1)^2 + [y1+m(x3-x1)-y1]^2 = d^2 => (x3-x1)^2 + m^2(x3-x1)^2 = d^2 =>
    => (x3-x1)^2(1+m^2)=d^2 => (x3-x1)^2=d^2/(1+m^2)
    Note - 1+m^2 > 0, therefore, we can safely divide by it.
    To simplify, let's denote C=d^2/(1+m^2) => (x3-x1)^2=C => x3^2 - 2x1x3 + x1^2 = C =>
                                      (4)   x3^2 - 2x1x3 + (x1^2-C) = 0

    (4) is a quadratic equation with the solutions: x3+=[-b+sqrt(b^2-4ac)]/2a, x3-=[-b-sqrt(b^2-4ac)]/2a,
    Where a=1, b=-2x1, c=x1^2-C:
    x3+ = [2x1 + sqrt(4x1^2-4*1*(x1^2-C))]/(2*1) = [2x1 + 2*sqrt(x1^2-x1^2+C)]/2 = x1+sqrt(C) =>
                                      (5)  x3+=x1+sqrt(C)
    The same applies for x3-:
                                      (6)  x3-=x1-sqrt(C)
    Note - C=d^2/(1+m^2)>0, therefore, sqrt(C) will have two real solutions. This is logical because p3 can be one
    either side of p1 on the line and at the distance d.

    We use the third condition that p3 is between p1 and p2, meaning that either x1>x3>x2 or x1<x3<x2. This way, we can
    choose the corresponding solution.

    When there is a vertical line (x1=x2), the calculation of p3 is simplified to x3=x2=x1, y3=y1+d*(y2-y1), where the
    factor (y2-y1) dictates the direction.

    :param p1: Point p1 (x1,y1).
    :param p2: Point p2 (x2,y2).
    :param d: Distance between p1 and p3.

    :return: p3 (x3,y3).
    """

    # Extracting the x,y coordinates.
    x1, y1 = p1
    x2, y2 = p2

    try:
        # Calculating the constants m and C.
        m = (p1[1] - p2[1]) / (p1[0] - p2[0])
        const = d ** 2 / (1 + m ** 2)

        # Calculating solution of the quadratic equation (4).
        x3 = x1 + np.sqrt(const)  # Assuming solution (5).
        if (x3 > x1 and x3 > x2) or (x3 < x1 and x3 < x2):
            # Solution (5) doesn't satisfy the third condition.
            x3 = x1 - np.sqrt(const)  # Applying solution (6).
        y3 = y1 + m * (x3 - x1)  # Applying equation (3) to find the y coordinate.
        return x3, y3
    except ZeroDivisionError:
        # (p1[0]-p2[0])=0 -> Vertical line (only y changes).
        return x1, y1 + d * (y2 - y1)


@measure_runtime
def transform_to_spatial_space(image_size: int, scaling_factor: float, pixel_coordinates: (float, float)) \
        -> list[(float, float)]:
    """
    Transform image coordinates to spatial space.

    Assumptions:
    1) The image size is an odd integer (symmetric around the origin).
    2) scaling_factor is the same for x and y axes.

    Image space versus spatial space:

                                      (0,0) -------(image_size/2)------→ col
                                        |
                                        |                y
                                        |                ↑
                                        |                |
                                        |                |
                                  (image_size/2)       (0,0) -----→ x
                                        |
                                        |
                                        |
                                        ↓
                                       row

    The origin point of the spatial space is at the middle of the image space, hence the image space should be a
    symmetrical size of an odd number.
    The column-axis in the image space is in the same direction as the x-axis, therefore, x=col-image_size/2.
    The row-axis in the image space is in opposite direction of the y-axis, therefore, y=image_size/2-row.

    :param image_size: The size of the image axes (odd integer).
    :param scaling_factor: The scaling factor for the image.
    :param pixel_coordinates: The pixel coordinates for the transform.

    :return: Array of transformed (translated and scaled) spatial coordinates.
    """

    # Calculating the translation factor.
    translation_factor = image_size / 2  # Simplified, because it's used many times throughout the following operations.
    log.debug(f"Translation factor - {translation_factor}")

    # Calculating the delta factor (pixel distance unit in spatial space).
    delta_factor = scaling_factor / translation_factor
    log.debug(f"One pixel unit in spatial space - {delta_factor}")

    # Translate and scale pixel coordinates to spatial ones.
    spatial_coordinates = [(delta_factor * (col - translation_factor), delta_factor * (translation_factor - row))
                           for row, col in pixel_coordinates]

    return spatial_coordinates


def generate_multifoil(a: float, b: float, lobes: int, number_of_points: int):
    """
    Generate a multifoil function.

    :param a: Amplitude of the multifoil.
    :param b: ??
    :param lobes: Number of lobes the multifoil includes.
    :param number_of_points: Number of points included in the function.

    :return: Cartesian coordinates of the multifoil function.
    """

    log.debug("Calculating the polar coordinates")
    phi = np.linspace(0, 2 * np.pi, number_of_points)
    r = a * (1 + b * np.cos(lobes * phi))

    log.debug("Converting to Cartesian coordinates")
    x = [r[i] * np.cos(phi[i]) for i in range(number_of_points)]
    y = [r[i] * np.sin(phi[i]) for i in range(number_of_points)]

    return x, y


@measure_runtime
def dft_2d(spatial_coordinates: list[(float, float)]):
    """
    TODO: Complete the docstring.
    """

    fourier_coefficients = []

    log.debug("Turning spatial coordinates into complex numbers")
    complex_coordinates = [x + 1j * y for x, y in spatial_coordinates]

    log.debug("Calculating the Fourier coefficients")
    normalization_factor = 1 / len(spatial_coordinates)  # Simplified, because it's used many times.
    for k in range(len(spatial_coordinates)):
        a = 0  # Resetting the coefficient calculation.
        for n in range(len(spatial_coordinates)):
            a += normalization_factor * complex_coordinates[n] * cmath.exp(
                -1j * 2 * math.pi * n * k * normalization_factor)
        fourier_coefficients.append(a)

    return fourier_coefficients
