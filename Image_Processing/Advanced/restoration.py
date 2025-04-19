"""
Script Name - restoration.py

Created by Michael Samelsohn, 06/11/24
"""

# Imports #
import warnings
import numpy as np
from numpy import ndarray
from Image_Processing.Basic.common import pad_image, extract_sub_image
from Settings.image_settings import *
from Utilities.decorators import book_reference
from Settings.settings import log


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 5.3 - Restoration in the Presence of Noise Only—Spatial Filtering, p.328-330")
def mean_filter(image: ndarray, filter_type=DEFAULT_MEAN_FILTER_TYPE, padding_type=DEFAULT_PADDING_TYPE,
                filter_size=DEFAULT_FILTER_SIZE, **kwargs) -> ndarray:
    """
    TODO: Complete the docstring.

    Note - Since more computations are done than necessary, this implementation is not optimal, rather for simplicity
    of use.

    :param image: The image for filtering.
    :param filter_type: The filter type used for the mean filtering.
    :param padding_type: Padding type used for applying the filter.
    :param filter_size: The filter size used for the image restoration.

    :return: Filtered image.
    """

    log.info(f"Applying a {filter_type} mean filter on the image")

    # Checking that 'q' is specified in the keyword arguments (if filter type is contra-harmonic). Setting default
    # value otherwise.
    if filter_type == "contra-harmonic":
        if "q" not in kwargs:
            log.warning("the order of the filter (Q) is not defined. Will use default value, 0 "
                        "(=arithmetic mean filter)")
            filter_type = DEFAULT_MEAN_FILTER_TYPE

    # Padding the image so the kernel can be applied to the image boundaries.
    padded_image = pad_image(image=image, padding_type=padding_type, padding_size=filter_size // 2)

    log.debug("Scanning the padded image and assigning the geometric mean pixel value for each scanned pixel")
    mean_filter_image = np.zeros(shape=image.shape)
    for row in range(filter_size // 2, image.shape[0] + filter_size // 2):
        for col in range(filter_size // 2, image.shape[1] + filter_size // 2):
            # Extract the sub-image.
            sub_image = extract_sub_image(image=padded_image, position=(row, col), sub_image_size=filter_size)

            # Finding the appropriate mean value of the sub-image and assigning it.
            match filter_type:
                case "arithmetic":
                    """
                    The arithmetic mean filter is the simplest of the mean filters (the arithmetic mean filter is the 
                    same as the box filter).
                    """
                    mean_filter_image[row - filter_size // 2][col - filter_size // 2] = np.average(sub_image)
                case "geometric":
                    """
                    A geometric mean filter achieves smoothing comparable to an arithmetic mean (box kernel) filter, but 
                    it tends to lose less image detail in the process.
                    """
                    power = 1 / np.power(filter_size, 2)
                    mean_filter_image[row - filter_size // 2][col - filter_size // 2] = \
                        np.power(np.prod(sub_image), power)
                case "harmonic":
                    """
                    The harmonic mean filter works well for salt noise, but fails for pepper noise. It does well also 
                    with other types of noise like Gaussian noise.
                    """
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        """
                        1 / sub_image can raise the 'RuntimeWarning: divide by zero encountered in divide' in case any 
                        of the pixels is zero (which is very likely). Therefore, the warning suppression is in effect. 
                        If any of the pixels is zero, the denominator evaluates to infinity, which means zero for the 
                        end result (due to the nominator being a constant non-zero integer). This coincides with the 
                        argument that the harmonic filter works poorly with pepper noise, as a single black pixel in the 
                        neighborhood nullifies the pixel under investigation (causing the whole neighborhood to become 
                        black).
                        """
                        denominator = np.sum(1 / sub_image)
                    mean_filter_image[row - filter_size // 2][col - filter_size // 2] = \
                        np.power(filter_size, 2) / denominator
                case "contra-harmonic":
                    """
                    This filter is well suited for reducing or virtually eliminating the effects of salt-and-pepper 
                    noise. Q is called the order of the filter. For positive values of Q, the filter eliminates pepper 
                    noise. For negative values of Q, it eliminates salt noise. It cannot do both simultaneously. Note 
                    that the contra-harmonic filter reduces to the arithmetic mean filter if Q = 0, and to the harmonic 
                    mean filter if Q = −1.
                    """
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        # Same explanation as in the harmonic mean filter.
                        nominator = np.sum(np.power(sub_image, kwargs["q"]+1))
                        denominator = np.sum(np.power(sub_image, kwargs["q"]))
                        mean_filter_image[row - filter_size // 2][col - filter_size // 2] = nominator / denominator

    return mean_filter_image


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 5.3 - Restoration in the Presence of Noise Only—Spatial Filtering, p.330-332")
def order_statistic_filter(image: ndarray, filter_type=DEFAULT_ORDER_STATISTIC_FILTER_TYPE,
                           padding_type=DEFAULT_PADDING_TYPE, filter_size=DEFAULT_FILTER_SIZE, **kwargs) -> ndarray:
    """
    TODO: Expand on order-statistic filters.

    Note - Since more computations are done than necessary, this implementation is not optimal, rather for simplicity
    of use.

    :param image: The image for filtering.
    :param filter_type: The filter type used for the mean filtering.
    :param padding_type: Padding type used for applying the filter.
    :param filter_size: The filter size used for the image restoration.

    :return: Filtered image.
    """

    log.info("Applying a median filter on the image")

    # Checking that 'percentile' is specified in the keyword arguments (if filter type is contra-harmonic). Setting
    # default value otherwise.
    if filter_type == "custom":
        if "percentile" not in kwargs:
            log.warning("the percentile value is not defined. Will use default value, median filter")
            filter_type = DEFAULT_ORDER_STATISTIC_FILTER_TYPE

    # Padding the image so the kernel can be applied to the image boundaries.
    padded_image = pad_image(image=image, padding_type=padding_type, padding_size=filter_size // 2)

    log.debug("Scanning the padded image and assigning the median pixel value for each scanned pixel")
    median_image = np.zeros(shape=image.shape)
    for row in range(filter_size // 2, image.shape[0] + filter_size // 2):
        for col in range(filter_size // 2, image.shape[1] + filter_size // 2):
            # Extract the sub-image.
            sub_image = extract_sub_image(image=padded_image, position=(row, col), sub_image_size=filter_size)
            # Flattening and sorting the sub-image.
            sorted_flat_sub_image = np.sort(np.ndarray.flatten(sub_image))

            # Finding the order statistic value of the sub-image and assigning it.
            match filter_type:
                case "median":
                    """
                    The best-known order-statistic filter in image processing is the median filter, which, as its name 
                    implies, replaces the value of a pixel by the median of the intensity levels in a predefined 
                    neighborhood of that pixel. The value of the pixel is included in the computation of the median.
                    Median filters are quite popular because, for certain types of random noise, they provide excellent 
                    noise-reduction capabilities, with considerably less blurring than linear smoothing filters of 
                    similar size. Median filters are particularly effective in the presence of both bipolar and unipolar 
                    impulse noise.
                    """
                    median_image[row - filter_size // 2][col - filter_size // 2] = \
                        sorted_flat_sub_image[filter_size**2 // 2]
                case "max":
                    """
                    This filter is useful for finding the brightest points in an image or for eroding dark regions 
                    adjacent to bright areas. Also, because pepper noise has very low values, it is reduced by this 
                    filter as a result of the max selection process in the sub-image area.
                    """
                    median_image[row - filter_size // 2][col - filter_size // 2] = sorted_flat_sub_image[-1]
                case "min":
                    """
                    This filter is useful for finding the darkest points in an image or for eroding light regions 
                    adjacent to dark areas. Also, it reduces salt noise as a result of the min operation.
                    """
                    median_image[row - filter_size // 2][col - filter_size // 2] = sorted_flat_sub_image[0]
                case "midpoint":
                    """
                    This filter combines order statistics and averaging. It works best for randomly distributed noise, 
                    like Gaussian or uniform noise.
                    """
                    median_image[row - filter_size // 2][col - filter_size // 2] = \
                        np.average(sorted_flat_sub_image[0] + sorted_flat_sub_image[-1])
                case "custom":
                    """Custom option to perform order-statistic filter with selected percentile"""
                    median_image[row - filter_size // 2][col - filter_size // 2] = \
                        sorted_flat_sub_image[kwargs["percentile"]]

    return median_image
