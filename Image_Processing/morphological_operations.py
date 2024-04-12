"""
Script Name - morphological_operations.py

TODO: Add page reference for all the functions.

Purpose - Listed below are rules when working with morphological operations:
    1) Images are binary.
    2) Structuring elements are square-shaped, odd-sized matrices.
    3) The origin of the structuring element is always the center.
    4) Structuring elements can contain three different values,
        * 0 - Background
        * 1 - Foreground
        * -1 - Don't care

Created by Michael Samelsohn, 27/05/22
"""

# Imports #
import os

import numpy as np
from numpy import ndarray

from common import pad_image, extract_sub_image, convert_to_grayscale
from intensity_transformations import thresholding
from Settings import image_settings
from Utilities.decorators import measure_runtime
from Settings.settings import log


def morphological_erosion(image: ndarray, structuring_element: ndarray,
                          threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE,
                          padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    Perform a morphological erosion operation on an image using the structuring element.

    :param image: The image to be eroded.
    :param structuring_element: Structuring element.
    :param threshold_value: Threshold value used for image binarization.
    :param padding_type: The padding type used for extending the image boundaries.
    :return:
    """

    return morphological_convolution(image=image, structuring_element=structuring_element,
                                     operation_type=image_settings.EROSION, threshold_value=threshold_value,
                                     padding_type=padding_type)


def morphological_dilation(image: ndarray, structuring_element: ndarray,
                           threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE,
                           padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    Perform a morphological dilation operation on an image using the structuring element.

    :param image: The image to be dilated.
    :param structuring_element: Structuring element.
    :param threshold_value: Threshold value used for image binarization.
    :param padding_type: The padding type used for extending the image boundaries.
    :return:
    """

    return morphological_convolution(image=image, structuring_element=structuring_element,
                                     operation_type=image_settings.DILATION, threshold_value=threshold_value,
                                     padding_type=padding_type)


def morphological_opening(image: ndarray, structuring_element: ndarray,
                          threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE,
                          padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """

    :param image: The image to be opened.
    :param structuring_element: Structuring element.
    :param threshold_value: Threshold value used for image binarization.
    :param padding_type: The padding type used for extending the image boundaries.
    :return:
    """

    eroded_image = morphological_convolution(image=image, structuring_element=structuring_element,
                                             operation_type=image_settings.EROSION, threshold_value=threshold_value,
                                             padding_type=padding_type)

    return morphological_convolution(image=eroded_image, structuring_element=structuring_element,
                                     operation_type=image_settings.DILATION, threshold_value=threshold_value,
                                     padding_type=padding_type)


def morphological_closing(image: ndarray, structuring_element: ndarray,
                          threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE,
                          padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """

    :param image: The image to be closed.
    :param structuring_element: Structuring element.
    :param threshold_value: Threshold value used for image binarization.
    :param padding_type: The padding type used for extending the image boundaries.
    :return:
    """

    dilated_image = morphological_convolution(image=image, structuring_element=structuring_element,
                                              operation_type=image_settings.DILATION, threshold_value=threshold_value,
                                              padding_type=padding_type)

    return morphological_convolution(image=dilated_image, structuring_element=structuring_element,
                                     operation_type=image_settings.EROSION, threshold_value=threshold_value,
                                     padding_type=padding_type)


def boundary_extraction(image: ndarray, structuring_element: ndarray, threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE,
                        padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """

    :param image: The image for boundary extraction.
    :param structuring_element: Structuring element.
    :param threshold_value: Threshold value used for image binarization.
    :param padding_type: The padding type used for extending the image boundaries.
    :return: The boundary of the image.
    """

    eroded_image = morphological_convolution(image=image, structuring_element=structuring_element,
                                             operation_type=image_settings.EROSION, threshold_value=threshold_value,
                                             padding_type=padding_type)

    return thresholding(image=convert_to_grayscale(image=image), threshold_value=threshold_value) - eroded_image


@measure_runtime
def morphological_convolution(image: ndarray, structuring_element: ndarray, operation_type,
                              threshold_value=image_settings.DEFAULT_THRESHOLD_VALUE,
                              padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    Perform a morphological convolution on an image with a structuring element.

    :param image: The image to be convolved.
    :param structuring_element: Structuring element.
    :param operation_type: There are two types of basic operations that can be performed:
        * Settings.EROSION (erosion).
        * Settings.DILATION (dilation).
    :param threshold_value: Threshold value used for image binarization.
    :param padding_type: The padding type used for extending the image boundaries.
    :return: Convolution of the image with the convolution object.
    """

    log.debug("Performing image binarization")
    binary_image = thresholding(image=convert_to_grayscale(image=image), threshold_value=threshold_value)

    log.debug("Asserting that structuring element is symmetrical")
    structuring_element_size = structuring_element.shape[0]
    if structuring_element.shape[0] != structuring_element.shape[1]:
        log.raise_exception(message="Structuring element is not symmetrical", exception=ValueError)

    log.debug(f"Structuring element size is - {structuring_element_size}")
    log.debug("Padding the image")
    padded_image = pad_image(image=binary_image, padding_type=padding_type, padding_size=structuring_element_size // 2)

    log.debug("Performing the morphological operation between the image and the structuring element")
    post_morphology_image = np.zeros(shape=binary_image.shape)
    for row in range(structuring_element_size // 2, image.shape[0] + structuring_element_size // 2):
        for col in range(structuring_element_size // 2, image.shape[1] + structuring_element_size // 2):
            sub_image = extract_sub_image(image=padded_image, position=(row, col),
                                          sub_image_size=structuring_element_size)
            post_morphology_image[row - structuring_element_size // 2, col - structuring_element_size // 2] \
                = morphological_convolution_dilation(sub_image=sub_image,
                                                     structuring_element=structuring_element) if operation_type == image_settings.DILATION \
                else morphological_convolution_erosion(sub_image=sub_image, structuring_element=structuring_element)

    return post_morphology_image


def morphological_convolution_dilation(sub_image: ndarray, structuring_element: ndarray) -> int:
    """
    Helper method for performing morphological dilation on a sub image.
    Notes:
        * The image and structuring element size must be identical.
        * Don't care values (denoted as -1) are ignored.

    :param sub_image: The sub-image (that matches in size the structuring element).
    :param structuring_element: Structuring element.
    :return: 1 if at least one value matches between the image and the structuring element, 0 otherwise.
    """

    # Check that image and structuring element are of the same shape.
    if sub_image.shape != structuring_element.shape:
        log.raise_exception(message="The image and structuring element have different sizes", exception=TypeError)

    for row in range(sub_image.shape[0]):
        for col in range(sub_image.shape[1]):
            if sub_image[row][col] == structuring_element[row][col] and structuring_element[row][col] != -1:
                return 1

    # If this point was reached without return value, then no match was found between image and structuring
    # element.
    return 0


def morphological_convolution_erosion(sub_image: ndarray, structuring_element: ndarray) -> int:
    """
    Helper method for performing morphological erosion on a sub image.
    Notes:
        * The image and structuring element size must be identical.
        * Don't care values (denoted as -1) are ignored.

    :param sub_image: The sub-image (that matches in size the structuring element).
    :param structuring_element: Structuring element.
    :return: 1 if all values match between the image and the structuring element, 0 otherwise.
    """

    # Check that image and structuring element are of the same shape.
    if sub_image.shape != structuring_element.shape:
        log.raise_exception(message="The image and structuring element have different sizes", exception=TypeError)

    for row in range(sub_image.shape[0]):
        for col in range(sub_image.shape[1]):
            if sub_image[row][col] != structuring_element[row][col] and structuring_element[row][col] != -1:
                return 0

    # If this point was reached without return value, then no mismatch was found between image and structuring
    # element.
    return 1
