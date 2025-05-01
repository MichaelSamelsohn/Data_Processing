# Imports #
from typing import Any
from Image_Processing.Advanced.segmentation import *
from Settings.settings import *


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

    log.info("Extracting skeleton coordinates and distances")

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

    log.info("Finding equal distance coordinates")

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


def transform_to_spatial_space(image_size: int, scaling_factor: float, pixel_coordinates: (float, float)) \
        -> tuple[list[float | Any], list[float | Any]]:
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

    log.info("Transforming coordinates from image space to spatial space")

    # Calculating the translation factor.
    translation_factor = image_size // 2  # Simplified because it's used many times throughout the following operations.
    log.debug(f"Translation factor - {translation_factor}")

    # Calculating the delta factor (pixel distance unit in spatial space).
    delta_factor = scaling_factor / translation_factor
    log.debug(f"One pixel unit in spatial space - {delta_factor}")

    # Translate and scale pixel coordinates to spatial ones.
    # spatial_coordinates = [(delta_factor * (col - translation_factor), delta_factor * (translation_factor - row))
    #                        for row, col in pixel_coordinates]
    x = [(delta_factor * (col - translation_factor)) for row, col in pixel_coordinates]
    y = [(delta_factor * (translation_factor - row)) for row, col in pixel_coordinates]

    return x, y
