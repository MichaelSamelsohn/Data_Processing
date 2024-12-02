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


@article_reference(article="J. Dong, W. Lin and C. Huang, “An improved parallel thinning algorithm,“ 2016 "
                           "International Conference on Wavelet Analysis and Pattern Recognition (ICWAPR), Jeju, Korea "
                           "(South), 2016, pp. 162-167")
def pre_thinning(image: ndarray) -> ndarray:
    """
    Pre-thinning is a crucial and essential step to produce a good skeleton. The binary image is scanned from the upper
    left corner to the lower right hand corner. For each pixel P in the image, let P2 to P9 be its 8 neighbors, starting
    from the north neighbor and counted in an anti-clockwise fashion. Let B_odd(P) = P2 + P4 + P6 + P8.
    If B_odd(P) < 2, the value of P is set to 0.
    Else if B_odd(P) > 2, the value of P is set to 1.
    Else, keep the value of P unchanged.

    :param image: Image for pre-thinning.

    :return: Pre-thinned image.
    """

    log.info("Performing image pre-thinning")

    pre_thinned_image = copy.deepcopy(image)
    for row in range(1, image.shape[0] - 1):
        for col in range(1, image.shape[1] - 1):
            neighbors_4 = image[row - 1][col] + image[row][col - 1] + image[row + 1][col] + image[row][col + 1]
            if neighbors_4 < 2:
                pre_thinned_image[row][col] = 0
            elif neighbors_4 > 2:
                pre_thinned_image[row][col] = 1

    return pre_thinned_image


def parallel_sub_iteration_thinning(image: ndarray, method="ZS", is_pre_thinning=False) -> ndarray:
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
    :param is_pre_thinning: Boolean value determining whether pre-thinning will take place.

    :return: Skeleton image.
    """

    log.info(f"Performing image thinning using method - {method}")

    if is_pre_thinning:
        image = pre_thinning(image=image)

    # Copying the image as to not disturb the original.
    skeleton_image = copy.deepcopy(image)

    log.debug("Activating the thinning process")
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
            # TODO: "Prettify" the syntax.
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
            adjoined_array = neighborhood_array + neighborhood_array[0:1]
            pattern_01 = sum((p1, p2) == (0, 1) for p1, p2 in zip(adjoined_array, adjoined_array[1:]))

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
                    Article reference - T. Y. Zhang and C. Y. Suen. "A Fast Parallel Algorithm for Thinning Digital 
                    Patterns", Communications of the ACM, 27(3):236–239, 1984.
                    
                    A fast parallel thinning algorithm. It consists of two sub-iterations:
                        • one aimed at deleting the south-east boundary points and the north-west corner points.
                        • one is aimed at deleting the north-west boundary points and the south-east corner points.
                    End points and pixel connectivity are preserved. Each pattern is thinned down to a "skeleton" of 
                    unitary thickness.
                    """
                    if (2 <= neighbors <= 6) and (pattern_01 == 1) and (basic_1 == 0) and (basic_2 == 0):
                        """
                        By condition 2 <= neighbors <= 6, the endpoints of a skeleton line are preserved. 
                        Condition pattern_01 == 1 prevents the deletion of those points that lie between the endpoints 
                        of a skeleton line.
                        """
                        # Found a contour point (to be removed).
                        contour_points += 1
                        contour_image[row, col] = 1
                case "BST":
                    """
                    Article reference - L. Ben Boudaoud, A. Sider and A. Tari, "A new thinning algorithm for binary 
                    images", 2015 3rd International Conference on Control, Engineering & Information Technology (CEIT), 
                    Tlemcen, Algeria, 2015, pp. 1-6.
                    
                    This thinning algorithm is based on the directional approach used by Zhang-Suen algorithm and is 
                    combined with the sub-field approach, which consists of dividing an image into two sub-fields. We 
                    define two sub-fields according to the parity of pixels. The first sub-field is the set of odd 
                    pixels that is those for which the sum of their coordinates i + j is odd and the second sub-field is 
                    similarity composed of the set of even pixels.
                    """
                    if (sub_field and (connected_components == 1) and (2 <= neighbors <= 7) and
                            (basic_1 == 0) and (basic_2 == 0)):
                        """
                        Condition connected_components == 1 implies that p is simple when p is a boundary pixel and the 
                        deletion will not disconnect the 3×3 neighborhood. 
                        Condition 2≤B(P1)≤7 means that we examine a larger set of border points than that considered by 
                        ZS, it implies deletion of more boundary pixels.
                        """
                        # Found a contour point (to be removed).
                        contour_points += 1
                        contour_image[row, col] = 1
                case "GH1":
                    """
                    Article reference - Z. Guo and R. W. Hall, "Parallel thinning with two sub-iteration algorithms", 
                    Commun. ACM, vol. 32, no. 3, pp. 359-373, Mar. 1989.

                    This method modifies the algorithms of Zhang-Suen (1984) and Lu-Wang (1986) to preserve connectivity 
                    and produce thin medial curves.
                    """

                    """
                    Endpoint check calculation.
                    n1(P) and n2(P) each break the ordered set of P’s neighboring pixels into four pairs of adjoining 
                    pixels and count the number of pairs which contain 1 or 2 ones.
                    """
                    # TODO: "Prettify" the syntax.
                    n1 = (int(neighborhood_array[7] or neighborhood_array[0]) +
                          int(neighborhood_array[1] or neighborhood_array[2]) +
                          int(neighborhood_array[3] or neighborhood_array[4]) +
                          int(neighborhood_array[5] or neighborhood_array[6]))
                    n2 = (int(neighborhood_array[0] or neighborhood_array[1]) +
                          int(neighborhood_array[2] or neighborhood_array[3]) +
                          int(neighborhood_array[4] or neighborhood_array[5]) +
                          int(neighborhood_array[6] or neighborhood_array[7]))
                    endpoint_check = min(n1, n2)

                    """
                    c1, used for odd iterations, is satisfied when P’s neighborhood takes either of the forms:
                                                x  x  x          x  0  0 

                                                x  P  0          x  P  x

                                                x  x  x          x  x  1  
                    """
                    c1 = ((neighborhood_array[0] or neighborhood_array[1] or not neighborhood_array[3])
                          and neighborhood_array[2])
                    """ c2, even iterations, is satisfied for 180° rotations of either of the two conditions above. """
                    c2 = ((neighborhood_array[4] or neighborhood_array[5] or not neighborhood_array[7])
                          and neighborhood_array[6])

                    if ((connected_components == 1) and (2 <= endpoint_check <= 3)
                            and not (c1 if sub_iteration_index == 1 else c2)):
                        """
                        Condition connected_components == 1 is a necessary condition for preserving local connectivity 
                        when P is deleted and avoids deletion of pixels in the middle of medial curves.
                        Condition 2<=endpoint_check<=3 allows endpoints to be preserved while deleting many redundant 
                        pixels in the middle of curves.
                        Condition c1 tends to identify pixels at the north and east boundary of objects and c2 
                        identifies pixels at the south and west boundary of objects.
                        """
                        # Found a contour point (to be removed).
                        contour_points += 1
                        contour_image[row, col] = 1
                case "GH2":
                    """
                    Article reference - Z. Guo and R. W. Hall, "Parallel thinning with two sub-iteration algorithms", 
                    Commun. ACM, vol. 32, no. 3, pp. 359-373, Mar. 1989. 
                    
                    This method is an adaptation of the thinning algorithm of Rosenfeld-Kak using by dividing the image 
                    into distinct subfields. These subfields are activated sequentially in distinct iterations.
                    """

                    """ 4-connected pixel evaluation - Check if all ones in the 4-neighborhood. """
                    connected_4 = False if (neighborhood_array[0] and neighborhood_array[2] and
                                            neighborhood_array[4] and neighborhood_array[6]) else True

                    if sub_field and (connected_components == 1) and connected_4 and (neighbors > 1):
                        """
                        Condition connected_components == 1 is a necessary condition for preserving local connectivity 
                        when P is deleted and avoids deletion of pixels in the middle of medial curves.
                        Condition is_candidate guarantees that only boundary pixels are candidates for deletion.
                        Condition neighbors > 1 preserves the endpoints of medial curves.
                        """
                        # Found a contour point (to be removed).
                        contour_points += 1
                        contour_image[row, col] = 1
                case "DLH":
                    """
                    Article reference - J. Dong, W. Lin and C. Huang, "An improved parallel thinning algorithm", 2016 
                    International Conference on Wavelet Analysis and Pattern Recognition (ICWAPR), Jeju, Korea (South), 
                    2016, pp. 162-167.
                    
                    The proposed algorithm yields good skeleton concerning connectivity and noise immunity. At the same 
                    time, it preserves a good symmetry, and mostly controls the large deformations at the intersections 
                    of strokes, moreover, the seeking conditions of the boundary pixels which will be deleted from the 
                    image are simple.
                    """

                    """
                    Transitions calculation. 
                    The number of 01 or 10 patterns in the ordered set P2, P3, P4, • • • P8, P9, P2.
                    """
                    transitions = sum((p1, p2) == (0, 1) or (p1, p2) == (1, 0)
                                      for p1, p2 in zip(adjoined_array, adjoined_array[1:]))

                    if (2 <= neighbors <= 6) and (transitions == 2) and (basic_1 == 0) and (basic_2 == 0):
                        """
                        By condition 2 <= neighbors <= 6, the endpoints of a skeleton line are preserved. 
                        Condition transitions == 2 prevents the deletions of skeleton points and maintains the 
                        connectedness of the original pattern.
                        """
                        # Found a contour point (to be removed).
                        contour_points += 1
                        contour_image[row, col] = 1

    return image - contour_image, contour_points


@article_reference(article="Y. Y. Zhang and P. S. P. Wang, “A parallel thinning algorithm with two-subiteration that "
                           "generates one-pixel-wide skeletons“, Proceedings of 13th International Conference on "
                           "Pattern Recognition, Vienna, Austria, 1996, pp. 457-461 vol.4")
def pta2t_thinning(image: ndarray) -> ndarray:
    """
    A fast two sub-iteration parallel thinning algorithm (PTA2T) which preserves the connectivity of patterns and
    produces one-pixel-wide skeletons.

    Definitions:
    1) A point, P, is termed "Globally Removable" if CN(P)=1 and NN(P)>1, where CN(P) is the number of connected
    components and NN is the number of non-zero neighbors. All globally removable points consist of a set termed GRS.
    2) A point, P, is termed irreducible if P is not a globally removable point. All irreducible points consist of a set
    termed IPS. IPS = WS - GRS (where WS is the set of all possible constellations for a 3x3 neighborhood).
    3) A skeleton S is of one-pixel-wide if all points in S are in IPS.
    4) A thinning algorithm is perfect if it can generate one-pixel-wide skeletons.

    Weight-Notation of thinning conditions (see calculate_decimal_weight method for weight notations):
    Weight notation set is defined to represent the thinning condition Ck of N sub-iteration algorithm A (1<=k<=N):
                                 A[k] = {WN(P) | WN(P) belongs to GRS and P belongs to Ck}
    For different window types, the WN set is different, but when summing all N WN sets, we get a set of all removable
    points for the algorithm, A_Remove = A[1] + A[2] + • • • + A[N]
    The set of all redundant points for algorithm A is - A_Redundant = GRS - A_Remove
    According to definition (4), If A_Redundant is an empty set, then the algorithm A is prefect.

    Symmetry of sub-iteration conditions:
    Various sub-iterations based algorithms have the quality of symmetry regarding the conditions that define the
    thinning process, for example, Zhang-Suen (1984), Guo-Hall (1989). This means we can use either a single window, but
    N removable points sets or N windows with a single removable set.

    Thinning conditions with array representation:
    To simplify the general form even further (and to shorten the amount of computations), we can combine all removable
    points under a single array (instead of separate sets), where the array is 0 if image[row, col] is not a removable
    point, 1 otherwise (part of a removable set).

    By combining the symmetry and condition array representation, the following pseudocode is a general form for the
    thinning process:

    procedure OH_B(image) ;
        thinning-not-end := TRUE;
        while (thinning-not-end) do
            thinning-not-end := FALSE;
            for k := 1 to 2 do
                WNQ: WNk(image)
                for row := 2 to max-row -1 do
                    for col := 2 to max-col -1 do
                        if (condition_array[WNQ[row,coll]]) then
                            thinning-not-end := TRUE;
                            image[row,col] := 0;

    See pta2t_condition_array method to see which templates are used for thinning and why the algorithm is perfect
    according to definition (4).

    :param image: The image for thinning.

    :return: Skeleton image.
    """

    log.info(f"Performing image thinning using method - Zhang-Wang")

    # Copying the image as to not disturb the original.
    skeleton_image = copy.deepcopy(image)

    # Constructing the PTA2T condition array.
    condition_array = pta2t_condition_array()

    log.debug("Activating the thinning process")
    iteration_counter = 0  # For debug purposes.
    is_contour_removed = True  # Flag used to determine if contour removal process is exhausted.
    while is_contour_removed:
        iteration_counter += 1
        log.debug(f"Iteration #{iteration_counter}")

        for i in [1, 2]:
            # Resetting the number of contour pixels removed in an iteration.
            contour_pixels = 0

            # Setting the values of the north/west (for window 1), south/east (for window 2) indexes.
            r0, c0 = (0, 1) if i == 1 else (2, 1)  # North/South.
            r6, c6 = (1, 0) if i == 1 else (1, 2)  # West/East.

            # Calculating the decimal weight of the image.
            decimal_weight_image = calculate_decimal_weight(matrix=skeleton_image, window_type=i)

            for row in range(1, image.shape[0] - 1):
                for col in range(1, image.shape[1] - 1):
                    # Checking pixel value.
                    if skeleton_image[row][col] == 0:
                        continue  # If the pixel is black it can't be part of a contour.

                    pixel_condition_value = condition_array[int(decimal_weight_image[row][col])]
                    match pixel_condition_value:
                        case 0:
                            continue  # P is not stable, not to be removed.
                        case 1:
                            # P is stable, to be removed.
                            contour_pixels += 1
                            skeleton_image[row][col] = 0
                        case 2:
                            # P is stable if north/south (window 1 and 2, respectively) is in IPS.
                            decimal_weight_window = extract_sub_image(image=decimal_weight_image, position=(row, col),
                                                                      sub_image_size=3)
                            if not condition_array[int(decimal_weight_window[r0][c0])]:
                                contour_pixels += 1
                                skeleton_image[row][col] = 0
                        case 3:
                            # P is stable if west/east (window 1 and 2, respectively) is in IPS.
                            decimal_weight_window = extract_sub_image(image=decimal_weight_image, position=(row, col),
                                                                      sub_image_size=3)
                            if not condition_array[int(decimal_weight_window[r6][c6])]:
                                contour_pixels += 1
                                skeleton_image[row][col] = 0
                        case 4:
                            # P is stable if north/south and west/east (window 1 and 2, respectively) is in IPS.
                            decimal_weight_window = extract_sub_image(image=decimal_weight_image, position=(row, col),
                                                                      sub_image_size=3)
                            if (not condition_array[int(decimal_weight_window[r0][c0])] and
                                not condition_array[int(decimal_weight_window[r6][c6])]):
                                contour_pixels += 1
                                skeleton_image[row][col] = 0

            log.debug(f"Contour pixels found in sub-iteration {i} - {contour_pixels}")

            # Stop condition check.
            if contour_pixels == 0:
                log.debug("No new contour pixels found, process finished")
                is_contour_removed = False
                break

    return skeleton_image


def pta2t_condition_array() -> ndarray:
    """
    Construction of the PTA2T condition array.
    The templates used for the construction of the array:

             0  0  x         x  0  0         x  0  x         1  1  0         0  0  1         0  0  0
             0  x  1         1  x  0         1  x  1         1  x  0         0  x  1         0  x  0
             x  1  x         x  1  x         x  1  x         x  1  x         0  0  x         1  1  x
               T1              T2              T3              T4              T5              T6

                     0  0  0         0  0  0         1  #  1         0  1  0         0  #  1
                     0  x  1         0  x  0         1  x  0         #  x  0         #  x  0
                     0  0  1         0  1  1         x  1  x         x  1  x         x  1  x
                       T7              T8              T9              T10             T11

    Where 'x' is don't care and '#' is a pixel in IPS.

    When converting all templates to weight notations we get the following:
    TO1 = {20, 22, 28, 30, 52, 54, 60, 62}                                             -- 8
    TO2 = {80, 88, 112, 120, 208, 216, 240, 248}                                       -- 8
    TO3 = {84, 86, 92, 94, 116, 118, 124, 126, 212, 214, 220, 222, 244, 246, 252, 254} -- 16
    TO4 = {209, 217, 241, 249}                                                         -- 4
    TO5 = {6, 14}                                                                      -- 2
    TO6 = {48, 56}                                                                     -- 2
    TO7 = {12}                                                                         -- 1
    TO8 = {24}                                                                         -- 1
    TO9 = {211, 219, 243, 251}                                                         -- 4
    T10 = {81, 89, 113, 121}                                                           -- 4
    T11 = {83, 91, 115, 123}                                                           -- 4

    PTA2T[1] = T1 + T2 + T3 + T4 + T5 + T6 + T7 + T8 + T9 + T10 + T11 = {
    006, 012, 014, 020, 022, 024, 028, 030, 048, 052, 054, 056, 060, 062, 080, 081, 083, 084, 086, 088, 089, 091, 092,
    094, 112, 113, 115, 116, 118, 120, 121, 123, 124, 126, 208, 209, 211, 212, 214, 216, 217, 219, 220, 222, 240, 241,
    243, 244, 246, 248, 249, 251, 252, 254
    } -- 54

    In order to distinguish the templates, we use the following values to fill the array:
    0 - P is unstable no template match                    No template
    1 - P is stable.                                       T1-T8
    2 - P is stable if north(P) is in IPS.                 T9
    3 - P is stable if west(P) is in IPS.                  T10
    4 - P is stable if north(P) and west(P) re in IPS.     T11

    Similarly, when switching to window type 2, we get:
    PTA2T[2] = {
    003, 005, 007, 013, 015, 021, 023, 029, 031, 053, 055, 061, 063, 065, 067, 069, 071, 077, 079, 096, 097, 099, 101,
    103, 109, 111, 129, 131, 133, 135, 192, 193, 195, 197, 199, 205, 207, 224, 225, 227, 141, 143, 149, 151, 157, 159,
    181, 183, 189, 191, 229, 231, 237, 239
    } -- 54

    Theorem - Algorithm PTA2T is perfect.
    Proof - The total deleted types of pixels in algorithm PTA2T thinning process is PTA2T[1] + PTA2T[2] which is equal
    to GRS. Therefore, algorithm PTA2T is perfect because all pixels in GRS are deleted.

    :return: PTA2T condition array.
    """

    log.info("Constructing the PTA2T condition array")

    log.debug("Preparing the templates T1-T11")
    t1 = np.array([[0, 0, 'x'], [0, 'x', 1], ['x', 1, 'x']])
    t2 = np.array([['x', 0, 0], [1, 'x', 0], ['x', 1, 'x']])
    t3 = np.array([['x', 0, 'x'], [1, 'x', 1], ['x', 1, 'x']])
    t4 = np.array([[1, 1, 0], [1, 'x', 0], ['x', 1, 'x']])
    t5 = np.array([[0, 0, 1], [0, 'x', 1], [0, 0, 'x']])
    t6 = np.array([[0, 0, 0], [0, 'x', 0], [1, 1, 'x']])
    t7 = np.array([[0, 0, 0], [0, 'x', 1], [0, 0, 1]])
    t8 = np.array([[0, 0, 0], [0, 'x', 0], [0, 1, 1]])
    t9 = np.array([[1, 1, 1], [1, 'x', 0], ['x', 1, 'x']])
    t10 = np.array([[0, 1, 0], [1, 'x', 0], ['x', 1, 'x']])
    t11 = np.array([[0, 1, 1], [1, 'x', 0], ['x', 1, 'x']])
    templates = {
        't1': t1, 't2': t2, 't3': t3, 't4': t4, 't5': t5, 't6': t6,
        't7': t7, 't8': t8, 't9': t9, 't10': t10, 't11': t11
    }

    log.debug("Evaluating the condition array according to template matches")
    condition_array = np.zeros(256)  # Initializing the condition array.
    for k in range(256):
        # Calculating the binary representation of the weight. Reversing it so it aligns with the window designations.
        weight = format(k, '08b')[::-1]  # '08b' - leading 0, 8 digits, binary.
        # Constructing the weight window. Since all templates are 'x' in the middle, we choose 1 as an arbitrary value.
        weight_window = np.array([[weight[7], weight[0], weight[1]],
                                  [weight[6],     1,     weight[2]],
                                  [weight[5], weight[4], weight[3]]])

        # Going over all templates to find a possible match.
        is_match = False
        for template in templates:
            # Check if current template is a match.
            is_match = is_template_match(template=templates[template], matrix=weight_window)
            if is_match:
                break  # Match found, no need to continue to the next templates.

        if not is_match:
            continue  # No match was found, value remains zero.

        # Matching the condition array value to the template match.
        match template:
            case 't1' | 't2' | 't3' | 't4' | 't5' | 't6' | 't7' | 't8':
                condition_array[k] = 1
            case 't9':
                condition_array[k] = 2
            case 't10':
                condition_array[k] = 3
            case 't11':
                condition_array[k] = 4

    return condition_array


def is_template_match(template: ndarray, matrix: ndarray) -> bool:
    """
    Method to check if the provided matrix matches the provided template.
    The template can contain don't care values designated as 'x'. For these values, no check is performed to match the
    matrix value.

    :param template: The template for matching.
    :param matrix: The matrix for template matching.

    :return: Boolean value indicating if the provided matrix matches the provided template.
    """

    # Scanning the template to find a value mismatch.
    for row in range(template.shape[0]):
        for col in range(template.shape[1]):
            # Checking for "don't care" values.
            if template[row][col] == 'x':
                continue  # Skip current value as it's a "don't care".

            # Checking for non-don't care value mismatch
            if template[row][col] != matrix[row][col]:
                return False  # Mismatch found, no need to continue.

    # If we got to this point, no mismatch was found and the matrix matches the template.
    return True


def calculate_decimal_weight(matrix: ndarray, window_type: int) -> ndarray:
    """
    Defining two possible widow types:
                                        P7  P0  P1                P3  P4  P5

                                        P6  P   P2                P2  P   P6

                                        P5  P4  P3                P1  P0  P7

                                            W1                        W2

    For a 3*3 window W1 the weight numbers (decimal weight) are among 0 and 255 and are defined as:
                    W(P) = sum(Pk*2^k) for k in 0-7 = P0*2^0 + P1*2^1 + • • • + P6*2^6 + P7*2^7

    :param matrix: Binary valued matrix.
    :param window_type: Type of window (1 or 2) for calculating the decimal weights.

    :return: Decimal weight matrix.
    """

    # Determining the indexes of the neighbor values depending on the window type selected.
    r0, c0 = (0, 1) if window_type == 1 else (2, 1)
    r1, c1 = (0, 2) if window_type == 1 else (2, 0)
    r2, c2 = (1, 2) if window_type == 1 else (1, 0)
    r3, c3 = (2, 2) if window_type == 1 else (0, 0)
    r4, c4 = (2, 1) if window_type == 1 else (0, 1)
    r5, c5 = (2, 0) if window_type == 1 else (0, 2)
    r6, c6 = (1, 0) if window_type == 1 else (1, 2)
    r7, c7 = (0, 0) if window_type == 1 else (2, 2)

    # Calculating the binary weight matrix.
    decimal_weight_matrix = np.zeros(shape=matrix.shape)  # Initializing the binary weight matrix.
    for row in range(1, matrix.shape[0] - 1):
        for col in range(1, matrix.shape[1] - 1):
            # Extract the sub-matrix.
            sub_matrix = extract_sub_image(image=matrix, position=(row, col), sub_image_size=3)

            """
            Calculating the binary weight of the current position.
            For better optimization, we convert the binary representation of the weight to the decimal value instead of 
            actually calculating it. The calculation introduces another 'for' loop (which we want to avoid),
            decimal_weight_matrix[row][col] = np.sum([neighborhood_array[i]*np.power(2, i) for i in range(8)])
            
            First, we arrange pixels values in an array, counter-clockwise order, starting from the end. This is because 
            the MSB is actually the last value P7.
            Second, we convert the array into a binary number (binary weight).
            Last, we convert the binary value to decimal (decimal weight).
            """
            neighborhood_array = [int(sub_matrix[r7, c7]), int(sub_matrix[r6, c6]),
                                  int(sub_matrix[r5, c5]), int(sub_matrix[r4, c4]), int(sub_matrix[r3, c3]),
                                  int(sub_matrix[r2, c2]), int(sub_matrix[r1, c1]), int(sub_matrix[r0, c0])]
            binary_weight = ''.join([str(s) for s in neighborhood_array])
            decimal_weight_matrix[row][col] = int(binary_weight, 2)

    return decimal_weight_matrix


@article_reference(article="Tarábek, Peter. (2008). “Performance measurements of thinning algorithms“, Journal of "
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

    log.info("Performing thinning rate calculation")

    log.debug("Calculating TM1 (the number of triangles whose three vertices are all white pixels)")
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

    log.debug("Calculating TM2 (the largest number of white triangles that an image can have)")
    tm2 = 4 * np.power([max(image.shape[0], image.shape[0]) - 1], 2)

    log.debug("Calculating the thinning rate")
    thinning_rate = 1 - (tm1 / tm2)
    log.info(f"The Thinning rate (TR) is - {thinning_rate}")

    return thinning_rate


def noiseless_doublet(image: ndarray) -> ndarray:
    """
    TODO: Complete the docstring.
    """

    stretched_image = contrast_stretching(image=image)

    high_intensity_contour = thresholding(image=stretched_image, threshold_value=0.75)

    negative_image = negative(image=stretched_image)
    low_intensity_contour = thresholding(image=negative_image, threshold_value=0.75)

    blurred = blur_image(image=high_intensity_contour, filter_size=23)
    blob = global_thresholding(image=blurred, initial_threshold=0.1)

    return blob
