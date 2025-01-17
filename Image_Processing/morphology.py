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

Created by Michael Samelsohn, 20/12/22
"""

# Imports #
import numpy as np
from numpy import ndarray

from Settings.image_settings import GONZALES_WOODS_BOOK
from Utilities.decorators import book_reference
from common import pad_image, extract_sub_image
from Settings import image_settings
from Settings.settings import log


@book_reference(book=GONZALES_WOODS_BOOK, reference="Chapter 9.2 - Erosion and Dilation, p.638-641")
def erosion(image: ndarray, structuring_element: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    Perform a morphological erosion operation on an image using the structuring element.

    :param image: The image to be eroded.
    :param structuring_element: Structuring element.
    :param padding_type: The padding type used for extending the image boundaries.

    :return: Morphologically eroded image.
    """

    log.info("Performing morphological erosion of the image")
    return morphological_convolution(image=image, structuring_element=structuring_element, operation_type="erosion",
                                     padding_type=padding_type)


@book_reference(book=GONZALES_WOODS_BOOK, reference="Chapter 9.2 - Erosion and Dilation, p.641-643")
def dilation(image: ndarray, structuring_element: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    Perform a morphological dilation operation on an image using the structuring element.

    :param image: The image to be dilated.
    :param structuring_element: Structuring element.
    :param padding_type: The padding type used for extending the image boundaries.

    :return: Morphologically dilated image.
    """

    log.info("Performing morphological dilation of the image")
    return morphological_convolution(image=image, structuring_element=structuring_element, operation_type="dilation",
                                     padding_type=padding_type)


@book_reference(book=GONZALES_WOODS_BOOK, reference="Chapter 9.3 - Opening and Closing, p.644-648")
def opening(image: ndarray, structuring_element: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    TODO: Complete the docstring.

    :param image: The image to be opened.
    :param structuring_element: Structuring element.
    :param padding_type: The padding type used for extending the image boundaries.

    :return: Morphologically opened image.
    """

    log.info("Performing morphological opening of the image")

    # Step I - Erode the image.
    eroded_image = erosion(image=image, structuring_element=structuring_element, padding_type=padding_type)
    # Step II - Dilate the eroded image.
    return dilation(image=eroded_image, structuring_element=structuring_element, padding_type=padding_type)


@book_reference(book=GONZALES_WOODS_BOOK, reference="Chapter 9.3 - Opening and Closing, p.644-648")
def closing(image: ndarray, structuring_element: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    TODO: Complete the docstring.

    :param image: The image to be closed.
    :param structuring_element: Structuring element.
    :param padding_type: The padding type used for extending the image boundaries.

    :return: Morphologically closed image.
    """

    log.info("Performing morphological closing of the image")

    # Step I - Dilate the image.
    dilated_image = dilation(image=image, structuring_element=structuring_element, padding_type=padding_type)
    # Step II - Erode the dilated image.
    return erosion(image=dilated_image, structuring_element=structuring_element, padding_type=padding_type)


def morphological_convolution(image: ndarray, structuring_element: ndarray, operation_type: str,
                              padding_type=image_settings.DEFAULT_PADDING_TYPE) -> ndarray:
    """
    Perform a morphological convolution on an image with a structuring element.

    :param image: The image to be convolved.
    :param structuring_element: Structuring element.
    :param operation_type: There are two types of basic operations that can be performed - erosion, dilation.
    :param padding_type: The padding type used for extending the image boundaries.

    :return: Convolution of the image with the convolution object.
    """

    log.debug("Processing the structuring element")
    processed_structuring_element = reflect_structuring_element(structuring_element=structuring_element) \
        if operation_type == "dilation" else structuring_element
    structuring_element_size = processed_structuring_element.shape[0]

    # Padding the image.
    padded_image = pad_image(image=image, padding_type=padding_type, padding_size=structuring_element_size // 2)

    log.debug("Performing the morphological operation between the image and the structuring element")
    post_morphology_image = np.zeros(shape=image.shape)
    for row in range(structuring_element_size // 2, image.shape[0] + structuring_element_size // 2):
        for col in range(structuring_element_size // 2, image.shape[1] + structuring_element_size // 2):
            # Extract the sub-image with structuring element size.
            sub_image = extract_sub_image(image=padded_image, position=(row, col),
                                          sub_image_size=structuring_element_size)

            # Perform the morphological operation.
            post_morphology_image[row - structuring_element_size // 2, col - structuring_element_size // 2] = (
                globals()[f"local_{operation_type}"](sub_image=sub_image,
                                                     structuring_element=processed_structuring_element))

    return post_morphology_image


def reflect_structuring_element(structuring_element: ndarray) -> ndarray:
    """
    Reflect the structuring element about its origin. That is, if B is a set of points in 2-D, then B_reflected is the
    set of points in B whose (x,y) coordinates have been replaced by (−x,−y).
    Note - Reflection consists simply of rotating an SE by 180° about its origin, and that all elements, including the
    background and don’t care elements, are rotated.

    :param structuring_element: Structuring element.

    :return: Reflected structuring element.
    """

    log.debug("Reflecting the structuring element")

    # Extracting the size of the structuring element.
    se_size = structuring_element.shape[0]

    reflected_structuring_element = np.zeros(shape=structuring_element.shape)
    for row in range(se_size):
        for col in range(se_size):
            reflected_structuring_element[row][col] = structuring_element[(se_size - 1) - row][(se_size - 1) - col]

    return reflected_structuring_element


def local_dilation(sub_image: ndarray, structuring_element: ndarray) -> int:
    """
    Helper method for performing morphological dilation on a sub-image. If at least a single match is found between the
    foreground of the structuring element and the foreground of the sub-image, the pixel is dilated.

    :param sub_image: The sub-image for local dilation.
    :param structuring_element: The structuring element used for the local dilation.

    :return: New pixel value, 1 if dilated, 0 otherwise.
    """

    # Scanning the image to find at least a single match between the structuring element and the sub-image.
    for row in range(sub_image.shape[0]):
        for col in range(sub_image.shape[1]):
            if structuring_element[row][col] == 1:  # Only foreground (1) pixels are examined.
                if sub_image[row][col] == 1:
                    # Match found, dilate the image.
                    return 1

    # No return value so far -> No match was found between sub-image and structuring element.
    return 0


def local_erosion(sub_image: ndarray, structuring_element: ndarray) -> int:
    """
    Helper method for performing morphological erosion on a sub-image. If at least a single mismatch is found between
    the foreground of the structuring element and the background of the sub-image, the pixel is eroded.

    :param sub_image: The sub-image for local erosion.
    :param structuring_element: The structuring element used for the local erosion.

    :return: New pixel value, 0 if eroded, 1 otherwise.
    """

    # Scanning the image to find mismatches between the structuring element and the sub-image.
    for row in range(sub_image.shape[0]):
        for col in range(sub_image.shape[1]):
            if structuring_element[row][col] == 1:  # Only foreground (1) pixels are examined.
                if sub_image[row][col] == 0:
                    # Mismatch found, erode the image.
                    return 0

    # No return value so far -> No mismatch was found between sub-image and structuring element.
    return 1
