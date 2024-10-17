import copy

from Utilities.decorators import article_reference
from common import *
from spatial_filtering import *
from corner_detection import *
from segmentation import *
from morphological_operations import *
from intensity_transformations import *
from Settings import image_settings

from Settings.settings import log


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

    The process continues until no pixels are identified as contour points (only the skeleton remians, nothing else to
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
        skeleton_image, contour_points = thinning_sub_iteration(binary_image=skeleton_image, sub_iteration=1)
        log.debug(f"Contour points found in sub-iteration 1 - {contour_points}")

        # Stop condition check.
        if contour_points == 0:
            log.debug("No new contour points found, process finished")
            break

        # Sub-iteration 2.
        skeleton_image, contour_points = thinning_sub_iteration(binary_image=skeleton_image, sub_iteration=2)
        log.debug(f"Contour points found in sub-iteration 2 - {contour_points}")

        # Stop condition check.
        if contour_points == 0:
            log.debug("No new contour points found, process finished")
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
    TODO: Complete the docstring.

    Assumptions:
    1) Only a single connected skeleton exists in the provided image.
    2) The skeleton is within the image borders.
    3) The skeleton is of unitary thickness.
    """

    # Copying the image as to not disturb the original.
    snake_image = copy.deepcopy(skeleton_image)
    skeleton_indexes = []  # Return array containing the indexes (rows and columns) of the skeleton.
    skeleton_distances = []  # Return array containing the distances between adjacent links of the skeleton.

    log.debug("Finding first skeleton link")
    link = find_first_link(skeleton_image=skeleton_image)
    skeleton_indexes.append(link)
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
                skeleton_indexes.append(link)
                skeleton_distances.append(np.sqrt(position[0] ** 2 + position[1] ** 2))
                snake_image[link[0]][link[1]] = 0  # Removing the link from the skeleton.
                is_new_link = True  # Found new link.
                break

        # Stop condition check - No new link found (the image is black).
        if not is_new_link:
            log.debug("No new link found (skeleton recovered)")
            log.debug(f"Total links in skeleton - {len(skeleton_indexes)}")
            # Calculate the distance from last link to first one.
            skeleton_distances.append((np.sqrt((skeleton_indexes[0][0] - skeleton_indexes[-1][0])**2 +
                                               (skeleton_indexes[0][1] - skeleton_indexes[-1][1])**2)))
            break

    return skeleton_indexes, skeleton_distances


def find_first_link(skeleton_image: ndarray) -> (int, int):
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
        const = d**2 / (1 + m**2)

        # Calculating solution of the quadratic equation (4).
        x3 = x1 + np.sqrt(const)  # Assuming solution (5).
        if (x3 > x1 and x3 > x2) or (x3 < x1 and x3 < x2):
            # Solution (5) doesn't satisfy the third condition.
            x3 = x1 - np.sqrt(const)  # Applying solution (6).
        y3 = y1 + m*(x3 - x1)  # Applying equation (3) to find the y coordinate.
        return x3, y3
    except ZeroDivisionError:
        # (p1[0]-p2[0])=0 -> Vertical line (only y changes).
        return x1, y1 + d*(y2 - y1)
