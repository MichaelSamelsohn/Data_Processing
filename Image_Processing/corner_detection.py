# Imports #
import numpy as np
from numpy import ndarray
from common import generate_filter, convolution_2d, extract_sub_image
from intensity_transformations import gamma_correction
from Settings import image_settings
from Settings.settings import log
from spatial_filtering import SOBEL_OPERATORS


def corner_detection(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE, detector_type="Harris",
                     filter_type=image_settings.DEFAULT_FILTER_TYPE,
                     filter_size=image_settings.DEFAULT_FILTER_SIZE, k=0.04, gamma=0.05) -> ndarray:
    """
    Detect corners in an image.
    TODO: Add the full theoretical explanation to how this works.

    :param image: The image for sharpening.
    :param detector_type: TODO: Complete.
    :param padding_type: The padding type used for the convolution.
    :param filter_type: Filter used as the window function.
    :param filter_size: Size of the filter used as the window function.
    :param k: TODO: Complete.
    :param gamma: Gamma value for the darkening of the image.

    :return: Darkened image with highlighted corners.
    """

    log.info("Performing Harris corner detector")

    log.debug("Calculating the directional derivatives")
    ix = convolution_2d(image=image, kernel=SOBEL_OPERATORS["HORIZONTAL"], padding_type=padding_type,
                        contrast_stretch=False)
    iy = convolution_2d(image=image, kernel=SOBEL_OPERATORS["VERTICAL"], padding_type=padding_type,
                        contrast_stretch=False)

    log.debug("Generating the selected filter")
    kernel = generate_filter(filter_type=filter_type, filter_size=filter_size)

    log.debug("Calculating spatial derivative")
    ix_2 = np.power(ix, 2)
    ix_2_filtered = convolution_2d(image=ix_2, kernel=kernel)
    iy_2 = np.power(iy, 2)
    iy_2_filtered = convolution_2d(image=iy_2, kernel=kernel)
    ix_iy = ix * iy
    ix_iy_filtered = convolution_2d(image=ix_iy, kernel=kernel)

    log.debug("Setting up structure tensor and Harris performing response calculation")
    r = np.zeros(shape=image.shape)
    half_filter_size = filter_size // 2  # To avoid repetitive calculations.
    for row in range(1, image.shape[0]-1):
        for col in range(1, image.shape[1]-1):
            # Extracting the appropriate neighborhood.
            ix_2_neighborhood = ix_2_filtered[row - half_filter_size: row + half_filter_size + 1,
                                              col - half_filter_size: col + half_filter_size + 1]
            iy_2_neighborhood = iy_2_filtered[row - half_filter_size: row + half_filter_size + 1,
                                              col - half_filter_size: col + half_filter_size + 1]
            ix_iy_neighborhood = ix_iy_filtered[row - half_filter_size: row + half_filter_size + 1,
                                                col - half_filter_size: col + half_filter_size + 1]

            # Calculating the sum of the neighborhood.
            ix_2_sum = np.sum(ix_2_neighborhood)
            iy_2_sum = np.sum(iy_2_neighborhood)
            ix_iy_sum = np.sum(ix_iy_neighborhood)

            # Calculating the R scores of the image.
            if detector_type == "Harris":
                det_m = ix_2_sum * iy_2_sum - np.power(ix_iy_sum, 2)
                trace_m = ix_2_sum + iy_2_sum
                r[row, col] = det_m - k * np.power(trace_m, 2)
            elif detector_type == "Shi-Tomasi":
                lambda1, lambda2 = np.linalg.eigvals([[ix_2_sum, ix_iy_sum], [ix_iy_sum, iy_2_sum]])
                r[row, col] = min(lambda1, lambda2)

    log.debug("Non-maximum suppression - Finding the local maxima as corners within the window (3x3 filter)")
    corners = np.zeros(shape=image.shape)
    for row in range(1, image.shape[0]-1):
        for col in range(1, image.shape[1]-1):
            if r[row, col] == extract_sub_image(image=r, position=(row, col), sub_image_size=3).max():
                corners[row, col] = r[row, col]

    log.debug("Highlighting best corners (those with the best scores)")
    max_corner = np.max(corners)  # Maximum value of a corner in the corners (R) matrix.
    for row in range(1, image.shape[0]-1):
        for col in range(1, image.shape[1]-1):
            # Lowest rated corners are filtered.
            corners[row, col] = 1 if corners[row, col] > (0.05 if detector_type == "Harris" else 0.2) * max_corner else 0
    log.info(f"Number of corners identified is - {np.sum(corners != 0)}")

    log.debug("Adding Gamma correction (to better see the highlighted corners)")
    result = gamma_correction(image, gamma=gamma)

    return result + corners
