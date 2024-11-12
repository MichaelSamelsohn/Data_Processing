"""
Script Name - thinning.py

Assumption - All methods are implemented on a binary image.

Created by Michael Samelsohn, 06/11/24
"""

# Imports #
import copy
import numpy as np
from numpy import ndarray

from common import extract_sub_image, contrast_stretching
from Utilities.decorators import article_reference
from Settings.settings import log
from intensity_transformations import negative
from segmentation import thresholding, global_thresholding
from spatial_filtering import blur_image


def sub_iteration_thinning(image: ndarray, method="ZS") -> ndarray:
    """
    A fast parallel thinning algorithm. It consists of two sub-iterations:
    • one aimed at deleting the south-east boundary points and the north-west corner points
    • one is aimed at deleting the north-west boundary points and the south-east corner points.
    End points and pixel connectivity are preserved. Each pattern is thinned down to a "skeleton" of unitary thickness.

    A binary digitized picture is defined by a matrix IT where each pixel IT(i,j) is either 1 or 0. The pattern
    consists of those pixels that have value 1 (therefore, the algorithm should only apply to pixels with value 1).
    Each stroke in the pattern is more than one element thick. Iterative transformations are applied to matrix IT point
    by point according to the values of a small set of neighboring points.

    It is assumed that a 3x3 window is used, and that each element is connected with its eight neighboring elements (no
    need to apply the algorithm to image edges).
    The algorithm presented in this paper requires only simple computations.

    The process continues until no pixels are identified as contour points (only the skeleton remains, nothing else to
    thin out). Therefore, between each sub-iteration, a check is performed to see how many contour points were
    identified.

    :param image: The image for thinning.
    :param method: Thinning method.

    :return: Skeleton image.
    """

    log.info(f"Performing image thinning using method - {method}")

    # Copying the image as to not disturb the original.
    skeleton_image = copy.deepcopy(image)

    iteration_counter = 0  # For debug purposes.
    is_contour_removed = True  # Flag used to determine if contour removal process is exhausted.
    while is_contour_removed:
        iteration_counter += 1
        log.debug(f"Iteration #{iteration_counter}")

        for i in [1, 2]:
            skeleton_image, contour_pixels = sub_iteration(image=skeleton_image, sub_iteration_index=i, method=method)
            log.debug(f"Contour pixels found in sub-iteration {i} - {contour_pixels}")

            # Stop condition check.
            if contour_pixels == 0:
                log.debug("No new contour pixels found, process finished")
                is_contour_removed = False
                break

    return skeleton_image


def sub_iteration(image: ndarray, method: str, sub_iteration_index: int) -> (ndarray, int):
    """
    Sub-iteration method used in parallel thinning algorithms with two sub-iterations.

    General logic:
    1) Locate a non-zero pixel.
    2) Perform all possible computations (even those not related to the selected method).
    3) Evaluate conditions to determine if the examined pixel is to be removed or not.
    The above process is repeated until all non-zero pixels are evaluated.

    Note - Since more computations are done than necessary, this implementation is not optimal, rather for simplicity
    of use.

    :param image: Binary image for thinning.
    :param method: Thinning method.
    :param sub_iteration_index: Index indicating which sub-iteration is currently running.

    :return: Thinned binary image and number of contour pixels removed.
    """

    contour_image = np.zeros(image.shape)
    contour_points = 0
    for row in range(1, image.shape[0] - 1):
        for col in range(1, image.shape[1] - 1):
            # Checking pixel value.
            if image[row][col] == 0:
                continue  # If the pixel is black it can't be part of a contour.

            """
            Designations of the nine pixels in a 3 x 3 window, where P1 is the pixel under check:

                                                P9  P2  P3

                                                P8  P1  P4

                                                P7  P6  P5
            """
            # Extract the sub-image.
            sub_image = extract_sub_image(image=image, position=(row, col), sub_image_size=3)
            # Arrange pixels values in an array, clockwise order (for simplicity of use).
            neighborhood_array = [sub_image[0, 1], sub_image[0, 2],
                                  sub_image[1, 2], sub_image[2, 2], sub_image[2, 1],
                                  sub_image[2, 0], sub_image[1, 0], sub_image[0, 0]]

            """
            Sub-field evaluation:
            (i + j)mod2 == 0 (for sub iteration 1).
            (i + j)mod2 != 0 (for sub iteration 2).
            """
            sub_field = (row + col) % 2
            sub_field = True if ((sub_field == 0 and sub_iteration_index == 1) or
                                 (sub_field == 1 and sub_iteration_index == 2)) else False

            """
            8-Connected components calculation.
            not(P2) and (P3 or P4) + not(P4) and (P5 or P6) + not(P6) and (P7 or P8) + not(P8) and (P9 or P2).
            """
            connected_components = (int(not neighborhood_array[0] and (neighborhood_array[1] or neighborhood_array[2])) +
                                    int(not neighborhood_array[2] and (neighborhood_array[3] or neighborhood_array[4])) +
                                    int(not neighborhood_array[4] and (neighborhood_array[5] or neighborhood_array[6])) +
                                    int(not neighborhood_array[6] and (neighborhood_array[7] or neighborhood_array[0])))

            """ Neighbors calculation - the number of nonzero neighbors of P1 = P2 + P3 + P4 + • • • + P8 + P9. """
            neighbors = np.sum(neighborhood_array[1:])

            """
            0->1 Transitions calculation. 
            The number of 01 patterns in the ordered set P2, P3, P4, • • • P8, P9, P2.
            """
            n = neighborhood_array + neighborhood_array[0:1]
            transitions = sum((p1, p2) == (0, 1) for p1, p2 in zip(n, n[1:]))

            """
            Basic conditions (sub-iteration 1):
            P2*P4*P6 = 0.
            P4*P6*P8 = 0.
            The solution to the set of basic conditions is - P4 = 0 or P6 = 0 or (P2 = 0 and P8 = 0). So the point P1, 
            which has been removed, might be an east or south boundary point or a north-west corner point.
            
            Basic conditions (sub-iteration 2):
            Sub-iteration 2 - P2*P4*P8.
            Sub-iteration 2 - P2*P6*P8.
            The solution to the set of basic conditions is - P2 = 0 or P8 = 0 or (P4 = 0 and P6 = 0). So the point P1, 
            which has been removed, might be a west or north boundary point or a south-east corner point. 
            """
            basic_1 = (neighborhood_array[0] * neighborhood_array[2] *
                       neighborhood_array[4 if sub_iteration_index == 1 else 6])
            basic_2 = (neighborhood_array[2 if sub_iteration_index == 1 else 0] *
                       neighborhood_array[4] * neighborhood_array[6])

            # Check if all conditions are met -> contour point.
            match method:
                case "ZS":
                    """
                    Article reference - T. Y. Zhang and C. Y. Suen. 'A Fast Parallel Algorithm for Thinning Digital 
                    Patterns', Communications of the ACM, 27(3):236–239, 1984.
                    
                    A fast parallel thinning algorithm. It consists of two sub-iterations:
                        • one aimed at deleting the south-east boundary points and the north-west corner points.
                        • one is aimed at deleting the north-west boundary points and the south-east corner points.
                    End points and pixel connectivity are preserved. Each pattern is thinned down to a "skeleton" of 
                    unitary thickness.
                    """
                    if (2 <= neighbors <= 6) and (transitions == 1) and (basic_1 == 0) and (basic_2 == 0):
                        """
                        By condition 2 <= neighbors <= 6, the endpoints of a skeleton line are preserved. 
                        Condition transitions == 1 prevents the deletion of those points that lie between the endpoints 
                        of a skeleton line.
                        """
                        # Found a contour point (to be removed).
                        contour_points += 1
                        contour_image[row, col] = 1
                case "BST":
                    """
                    Article reference - L. Ben Boudaoud, A. Sider and A. Tari, 'A new thinning algorithm for binary 
                    images', 2015 3rd International Conference on Control, Engineering & Information Technology (CEIT), 
                    Tlemcen, Algeria, 2015, pp. 1-6.
                    
                    This thinning algorithm is based on the directional approach used by Zhang-Suen algorithm and is combined with the
                    sub-field approach, which consists of dividing an image into two sub-fields. We define two sub-fields according to
                    the parity of pixels. The first sub-field is the set of odd pixels that is those for which the sum of their
                    coordinates i + j is odd and the second sub-field is similarity composed of the set of even pixels.
                    """
                    if (sub_field and (connected_components == 1) and (2 <= neighbors <= 7) and
                            (basic_1 == 0) and (basic_2 == 0)):
                        """
                        Condition connected_components == 1 implies that p is simple when p is a boundary pixel and the 
                        deletion will not disconnect the 3×3 neighborhood. 
                        Condition 2≤B(p1)≤7 means that we examine a larger set of border points than that considered by 
                        ZS, it implies deletion of more boundary pixels.
                        """
                        # Found a contour point (to be removed).
                        contour_points += 1
                        contour_image[row, col] = 1

    return image - contour_image, contour_points


@article_reference(article="Tarábek, Peter. (2008). \"Performance measurements of thinning algorithms\", Journal of "
                           "Information, Control and Management Systems. 6.")
def measure_thinning_rate(image: ndarray) -> float:
    """
    Measuring the thinning rate (TR) - The degree of thinness of the image,
                                                TR = 1 - TM1/TM2
    Where TM1 stands for total triangle count of the thinned image and TM2 stands for maximum triangle count possible in
    the image.

    If image[row][col] is a white pixel, then the value of TM1(image[row][col]) is equal to the number of triangles
    whose three vertices are all white pixels. It is easy to prove that, if anywhere in the image that is not one-pixel
    wide (not thinned), then there exists a triangle composed of three white pixels. Such triangles are referred to as
    white triangles.
    TM1 is normalized with respect to parameter TM2. TM2 represents the largest number of white triangles that an image
    can have. Hence, the normalized value of the thinness measurement TM lies between 0 and 1.
    When TR = 1 image is perfectly thinned, when TR = 0 image is not thinned at all.

    :param image: The image for thinning rate measurement.

    :return: Thinning rate calculation.
    """

    tm1 = 0
    for row in range(1, image.shape[0] - 1):
        for col in range(1, image.shape[1] - 1):
            if image[row][col] == 0:
                continue  # If the pixel is black it can't be part of a contour.

            """
            Designations of the nine pixels in a 3 x 3 window, where P1 is the pixel under check:

                                                P9  P2  P3

                                                P8  P1  P4

                                                P7  P6  P5
            """
            # Extract the sub-image.
            sub_image = extract_sub_image(image=image, position=(row, col), sub_image_size=3)
            # Arrange pixels values in an array (clockwise order).
            neighborhood_array = [sub_image[0, 1], sub_image[0, 2],
                                  sub_image[1, 2], sub_image[2, 2], sub_image[2, 1],
                                  sub_image[2, 0], sub_image[1, 0], sub_image[0, 0]]

            # Calculating TM1(image[row][col]).
            tm1 += ((neighborhood_array[6] * neighborhood_array[7]) + (neighborhood_array[7] * neighborhood_array[0]) +
                    (neighborhood_array[0] * neighborhood_array[1]) + (neighborhood_array[1] * neighborhood_array[2]))

    # Calculating TM2.
    tm2 = 4 * np.power([max(image.shape[0], image.shape[0]) - 1], 2)

    # Thinning rate calculation.
    thinning_rate = 1 - (tm1 / tm2)
    log.info(f"The Thinning rate (TR) is - {thinning_rate}")

    return thinning_rate


            # Check if all conditions are met -> contour point.
            if (2 <= b <= 6) and (a == 1) and (c == 0) and (d == 0):
                # Found a contour point (to be removed).
                contour_points += 1
                contour_image[row, col] = 1

    return binary_image - contour_image, contour_points
