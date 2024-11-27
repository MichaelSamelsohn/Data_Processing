"""
Script Name - restoration.py

Created by Michael Samelsohn, 06/11/24
"""

# Imports #
import numpy as np
from numpy import ndarray, random
from common import pad_image, extract_sub_image
from Settings import image_settings
from Utilities.decorators import book_reference
from Settings.settings import log


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 5.2 - Restoration in the Presence of Noise Only—Spatial Filtering, p.322-324")
def salt_and_pepper(image: ndarray, pepper=0.001, salt=0.001) -> ndarray:
    """
    Add salt and pepper (white and black) pixels to an image at random.
    TODO: Extend the docstring.

    :param image: The image for distortion.
    :param pepper: Percentage of black pixels to be randomized into the image.
    :param salt: Percentage of white pixels to be randomized into the image.

    :return: Distorted image.
    """

    log.info("Adding salt and pepper to the image")

    pepper_pixels, salt_pixels = 0, 0  # Counters for the salt and pepper pixels.
    noisy_image = np.zeros(shape=image.shape)
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            # Randomizing the new pixel value according to the following three options - salt, pepper, unchanged.
            new_pixel = random.choice([0, 1, image[row][col]], p=[pepper, salt, 1 - (pepper + salt)])

            # Checking that pixel wasn't already pepper (black).
            if new_pixel == 0 and image[row][col] != 0:
                pepper_pixels += 1  # Incrementing salt counter.
            # Checking that pixel wasn't already salt (white).
            if new_pixel == 1 and image[row][col] != 1:
                salt_pixels += 1  # Incrementing salt counter.
            # Setting the new pixel value.
            noisy_image[row][col] = new_pixel

    log.info(
        f"Pepper pixels - {pepper_pixels} ({round(100 * pepper_pixels / (image.shape[0] * image.shape[1]), 2)}% of "
        f"total pixels)")
    log.info(
        f"Salt pixels - {salt_pixels} ({round(100 * salt_pixels / (image.shape[0] * image.shape[1]), 2)}% of "
        f"total pixels)")

    return noisy_image

@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 5.3 - Restoration in the Presence of Noise Only—Spatial Filtering, p.330-332")
def median_filter(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                  filter_size=image_settings.DEFAULT_FILTER_SIZE) -> ndarray:
    """
    The best-known order-statistic filter in image processing is the median filter, which, as its name implies, replaces
    the value of a pixel by the median of the intensity levels in a predefined neighborhood of that pixel. The value of
    the pixel is included in the computation of the median.

    Median filters are quite popular because, for certain types of random noise, they provide excellent noise-reduction
    capabilities, with considerably less blurring than linear smoothing filters of similar size. Median filters are
    particularly effective in the presence of both bipolar and unipolar impulse noise.

    :param image: The image for filtering.
    :param padding_type: Padding type used for applying the filter.
    :param filter_size: The filter size used for the image restoration.

    :return: Filtered image.
    """

    log.info("Applying a median filter on the image")

    # Padding the image so the kernel can be applied to the image boundaries.
    padded_image = pad_image(image=image, padding_type=padding_type, padding_size=filter_size // 2)

    log.debug("Scanning the padded image and assigning the median pixel value for each scanned pixel")
    median_image = np.zeros(shape=image.shape)
    for row in range(filter_size // 2, image.shape[0] + filter_size // 2):
        for col in range(filter_size // 2, image.shape[1] + filter_size // 2):
            # Extract the sub-image.
            sub_image = extract_sub_image(image=padded_image, position=(row, col), sub_image_size=filter_size)
            # Finding the median value of the sub-image and assign it.
            flat_sub_image = np.ndarray.flatten(sub_image)
            median_image[row - filter_size // 2][col - filter_size // 2] = np.sort(flat_sub_image)[filter_size**2 // 2]

    return median_image
