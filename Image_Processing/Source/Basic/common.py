"""
Script Name - common.py

Purpose - Commonly used functions.

Created by Michael Samelsohn, 12/05/22.
"""

# Imports #
import copy
import logging
import math
import numpy as np
from numpy import ndarray
from Image_Processing.Settings.image_settings import *
from Utilities.decorators import measure_runtime, log_suppression


def convert_to_grayscale(image: ndarray) -> ndarray:
    """
    Convert a color image to grayscale.
    The RGB values are converted to grayscale using the NTSC formula: 0.299 ∙ Red + 0.587 ∙ Green + 0.114 ∙ Blue.
    This formula closely represents the average person's relative perception of the brightness of red, green, and blue
    light.

    :param image: Color image for conversion. If image is grayscale, it is returned as is.

    :return: Grayscale image.
    """

    log.info("Converting image to grayscale")

    log.debug("Checking image shape")
    if len(image.shape) == 3:
        log.debug("Extracting the red, green and blue images")
        red, green, blue = image[:, :, 0], image[:, :, 1], image[:, :, 2]
        log.debug("Performing the conversion")
        # NTSC luminance weights: green contributes most because the human eye is most sensitive to it.
        grayscale_image = 0.2989 * red + 0.5870 * green + 0.1140 * blue
        return grayscale_image
    else:
        log.warning("Image is already grayscale")
        return image


def use_lookup_table(image, lookup_table: ndarray | list) -> ndarray:
    """
    Convert image using lookup table values.
    The lookup table provides a transformation value for each possible intensity value (normally, 0-255).
    Lookup tables are extremely time-efficient when it comes to pixel-wise (as opposed to neighbourhood) transformations
    where there is a formula for each intensity value -> O(1).
    Otherwise, the calculation is done for every pixel -> O(N*M) (N, M are the image dimensions).

    :param image: The image to be used for the lookup table.
    :param lookup_table: The lookup table.
    :return: Result image where every pixel was transformed according to its corresponding index value in the lookup
    table.
    """

    log.info("Applying lookup table to the image")

    new_image = copy.deepcopy(image)  # Deep copy, so the original is not altered.
    new_image[:, :] = lookup_table[image[:, :]]  # NumPy fancy indexing: use pixel values as indices into the LUT.
    return new_image


def scale_pixel_values(scale_factor=DEFAULT_SCALING_FACTOR):
    # Decorator factory: scales the image to [0, 255] before the wrapped function and back to [0, 1] after.
    def wrapper(func):
        def inner(*args, **kwargs):
            kwargs["image"] = scale_image(image=kwargs["image"], scale_factor=scale_factor)
            return_image = func(*args, **kwargs)
            return scale_image(image=return_image, scale_factor=1 / scale_factor)

        return inner

    return wrapper


def scale_image(image: ndarray, scale_factor=DEFAULT_SCALING_FACTOR) -> ndarray:
    """
    Scale the pixel values of an image by the provided scaling factor.
    This function is useful when the pixel range is [0, 1] and it needs to be converted to integer values (scaling
    upwards by 255) and vice versa.

    :param image: The image to be scaled.
    :param scale_factor: The scaling factor.
    Note - For scaling factor 255, the image is also set as int type (rather than float).

    :return: Scaled image.
    """

    log.info(f"Scaling the image by a factor of {scale_factor}")

    scaled_image = copy.deepcopy(image * scale_factor)  # Deep copy, so the original is not altered.

    if scale_factor == 255:
        log.debug("Scale factor is 255 -> Setting the image as int type")
        scaled_image = scaled_image.astype(int)

    return scaled_image


def calculate_histogram(image: ndarray,
                        normalize=DEFAULT_HISTOGRAM_NORMALIZATION) -> tuple[ndarray, ndarray, ndarray] | ndarray:
    """
    Calculate the histogram of an image. A histogram shows the amount of pixels per pixel intensity value.
    If the histogram is normalized, it shows the probabilities per pixel intensity value.
    Note - if the image is a color one, the return value will contain three histograms (one for each color channel).

    :param image: The image.
    :param normalize: Boolean value indicating if the histogram is to be normalized or not.

    :return: Histogram of the provided image.
    """

    log.info("Calculating histogram of an image")

    if len(image.shape) == 3:
        log.debug("Color image -> Splitting the image to its three channels")

        log.debug("Extracting the red, green and blue images")
        red, green, blue = image[:, :, 0], image[:, :, 1], image[:, :, 2]
        return calculate_histogram(image=red, normalize=normalize), \
            calculate_histogram(image=green, normalize=normalize), \
            calculate_histogram(image=blue, normalize=normalize)

    log.debug("Scaling the image to have a histogram with integer values")
    # TODO: Need to understand if this is always 255?
    image = scale_image(image=image, scale_factor=255)

    log.debug("Performing the histogram calculation")
    histogram = np.zeros(256)
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            histogram[image[row][col]] += 1  # Incrementing the counter for the current pixel value.

    if normalize:
        log.debug("Normalizing the histogram (converting to probabilities per pixel intensity value)")
        histogram /= (image.shape[0] * image.shape[1])

    return histogram


def generate_filter(filter_type=DEFAULT_FILTER_TYPE, filter_size=DEFAULT_FILTER_SIZE,
                    sigma=DEFAULT_SIGMA_VALUE) -> ndarray:
    """
    Generate a spatial filter (kernel) of the specified type and size.

    A filter (kernel) is a small matrix used to perform neighbourhood operations on an image via convolution. The choice
    of filter type determines the frequency-domain characteristics of the operation (e.g., low-pass blurring). The
    filter size should be an odd integer so that the kernel has a well-defined center pixel. Larger kernels capture
    wider neighbourhoods but increase computation time. For Gaussian filters, the size should be at least 2·ceil(3σ)+1
    to cover ±3σ of the bell curve.

    Types of filters:
        * Box filter      - A uniform averaging filter: an all-ones matrix divided by the total number of elements. All
                            pixels in the neighbourhood contribute equally to the output, providing simple low-pass
                            (blurring) behaviour.
        * Gaussian filter - A weighted averaging filter constructed from the 2D Gaussian function:
                                                        G(x, y) = exp(−(x² + y²) / (2·σ²))
                            Pixels closer to the center of the kernel contribute more than those at the edges, producing
                            smoother blurring with less ringing than the box filter. After computing the kernel values,
                            the matrix is normalised so its elements sum to 1. The σ parameter controls the width of the
                            bell curve: larger σ yields heavier blurring.

    :param filter_type: The type of filter to be generated.
    :param filter_size: The size of the filter to be generated. Can be either an integer or a tuple of integers.
    :param sigma: Standard deviation (relevant only if filter_type='gaussian').

    :return: Matrix array with the specified dimensions and based on the selected filter type.
    """

    log.info(f"Generating filter of type, {filter_type} with size {filter_size}")

    # Asserting that filter size is an odd number and is symmetrical.
    filter_size_square = 1
    if isinstance(filter_size, int):
        if filter_size % 2 == 0:
            log.raise_exception(message="Filter size is an even number. Filters should be odd number size",
                                exception=ValueError)
        else:  # Selected filter size is odd.
            # Setting the shape of the filter to be symmetrical.
            filter_size_square = (filter_size, filter_size)

    log.debug("Identifying the filter type and generating it")
    kernel_matrix = np.zeros(shape=filter_size_square)
    match filter_type:
        case "box":
            log.debug("Box type filter selected")
            kernel_matrix = np.ones(shape=filter_size_square)
            kernel_matrix /= np.sum(kernel_matrix)  # Normalize.
        case "gaussian":
            log.debug("Gaussian type filter selected with parameters:")
            log.debug(f"Sigma = {sigma}")
            center_position = filter_size // 2
            for row in range(filter_size):
                for col in range(filter_size):
                    r_squared = math.pow(row - center_position, 2) + math.pow(col - center_position, 2)
                    # Unnormalised Gaussian G(x,y) = exp(-(x²+y²)/(2σ²)); normalisation below ensures the kernel sums 1.
                    kernel_matrix[row][col] = math.exp(-r_squared / (2 * math.pow(sigma, 2)))
            kernel_matrix /= np.sum(kernel_matrix)  # Normalize so convolution preserves average brightness.

    return kernel_matrix


def pad_image(image: ndarray, padding_type=DEFAULT_PADDING_TYPE, padding_size=DEFAULT_PADDING_SIZE) -> ndarray:
    """
    Padding the image boundaries.

    :param image: The image for padding.
    :param padding_type: The padding type.
    Types of padding methods:
        * Zero padding   ("zero")   - Fill the border with zeros. Simple and fast; can introduce artificial edges at
                                      boundaries because the abrupt transition to zero may create a strong gradient
                                      where there was none in the original signal.
        * Mirror padding ("mirror") - Reflect pixel values around the image border without repeating the edge pixel.
                                      For a 1D slice [a, b, c] with padding size 1, the result is [b, a, b, c, b].
                                      Reduces boundary artifacts for spatial filtering because the padded values are
                                      drawn from the real image content rather than an artificial constant.
        * Wrap padding   ("wrap")   - Tile the image periodically so the right edge connects to the left and the bottom
                                      connects to the top. For a 1D slice [a, b, c] with padding size 1, the result is
                                      [c, a, b, c, a]. Appropriate when the signal is known to be periodic (e.g.,
                                      textures or frequency-domain processing).
    :param padding_size: The number of pixel rows/columns added to each side of the image.

    :return: Padded image with shape (H + 2*padding_size, W + 2*padding_size) for grayscale or
    (H + 2*padding_size, W + 2*padding_size, C) for color.
    """

    log.info(f"Padding image boundaries with '{padding_type}' (size={padding_size})")

    # Build pad_width: apply padding_size on each spatial axis; leave the channel axis untouched for color images.
    pad_width = ((padding_size, padding_size), (padding_size, padding_size))
    if len(image.shape) == 3:
        pad_width = pad_width + ((0, 0),)

    log.debug("Identifying the padding type and applying it")
    match padding_type:
        case "zero":
            log.debug("Zero padding selected")
            return np.pad(image, pad_width, mode='constant', constant_values=0)
        case "mirror":
            log.debug("Mirror padding selected (reflection without edge repetition)")
            return np.pad(image, pad_width, mode='reflect')
        case "wrap":
            log.debug("Wrap padding selected (periodic boundary)")
            return np.pad(image, pad_width, mode='wrap')
        case _:
            log.warning(f"Unknown padding type '{padding_type}', falling back to zero padding")
            return np.pad(image, pad_width, mode='constant', constant_values=0)


@measure_runtime
def convolution_2d(image: ndarray, kernel: ndarray, padding_type=DEFAULT_PADDING_TYPE,
                   normalization_method=DEFAULT_NORMALIZATION_METHOD) -> ndarray:
    """
    Perform convolution on an image with a kernel matrix. Mainly used for spatial filtering.

    :param image: The image to be convolved.
    :param kernel: Kernel matrix.
    :param padding_type: The padding type used for extending the image boundaries.
    :param normalization_method: Preferred normalization method for the convoluted image. Options are - unchanged,
    stretch and cutoff.

    :return: Convolution of the image with the convolution object.
    """

    log.info("Performing 2D convolution on the image")

    log.debug("Asserting that kernel is symmetrical")
    kernel_size = kernel.shape[0]  # TODO: Make sure this is correct.
    if kernel.shape[0] != kernel.shape[1]:
        log.raise_exception(message="Kernel is not symmetrical", exception=ValueError)

    # Padding the image so the kernel can be applied to the image boundaries.
    padded_image = pad_image(image=image, padding_type=padding_type, padding_size=kernel_size // 2)

    log.debug("Performing the convolution between the padded image and the kernel matrix")
    convolution_image = np.zeros(shape=image.shape)
    for row in range(kernel_size // 2, image.shape[0] + kernel_size // 2):
        for col in range(kernel_size // 2, image.shape[1] + kernel_size // 2):
            # Extract the sub-image.
            sub_image = extract_sub_image(image=padded_image, position=(row, col), sub_image_size=kernel_size)
            # Perform the convolution for the sub-image.
            convolution_image[row - kernel_size // 2, col - kernel_size // 2] = [
                np.sum(sub_image[:, :, 0] * kernel),
                np.sum(sub_image[:, :, 1] * kernel),
                np.sum(sub_image[:, :, 2] * kernel)] if len(image.shape) == 3 else np.sum(sub_image * kernel)

    return image_normalization(image=convolution_image, normalization_method=normalization_method)


def image_normalization(image: ndarray, normalization_method=DEFAULT_NORMALIZATION_METHOD) -> ndarray:
    """
    Normalize image according to one of the following methods:
    • unchanged - Image remains as is. In this case, there might be values exceeding the expected image range of [0, 1].
    • stretch - The pixel values are compressed or stretched to the boundaries of 0 and 1. This means that the lowest
      pixel value turns to 0 and the highest turns to 1. The rest are linearly distributed between them.
    • cutoff - Eliminate all values exceeding the range of [0, 1]. This means that pixel values below 0, become 0, and
      pixel values above 1, become 1.

    :param image: The image for normalization.
    :param normalization_method: The normalization method (as mentioned in the description above).

    :return: Normalized image.
    """

    log.info(f"Normalizing image according to the following method - {normalization_method}")

    match normalization_method:
        case 'unchanged':
            log.debug("Returning image as is")
            log.warning("Image might contain pixel values exceeding the range of [0, 1]")
            return image
        case 'stretch':
            # Stretching the image contrast to range [0, 1].
            return contrast_stretching(image=image)
        case 'cutoff':
            log.debug("'Cutting' values above 1 or below 0")
            image[image > 1] = 1
            image[image < 0] = 0
            log.warning("Image might lose information due to this normalization method")
            return image
        case _:
            log.error(f"Normalization method, {normalization_method}, is not a recognized option")
            log.error("Available options are - unchanged, stretch, cutoff (read convolution_2d (part of common.py) "
                      "docstring for a better understanding as to what each method does)")
            log.warning("Will use default method - unchanged")
            return image


def extract_sub_image(image: ndarray, position: tuple[int, int], sub_image_size: int) -> ndarray:
    """
    Extract sub-image from an image. Mainly used for performing neighbourhood operations.

    :param image: The image.
    :param position: The x,y position of the center pixel (of the sub-image).
    :param sub_image_size: The size of the sub-image.

    :return: Sub-image, where the center pixel is based on the selected position.
    """

    # Asserting that sub-image size is an odd number (so it can have a center pixel).
    if sub_image_size % 2 == 0:
        log.raise_exception(message="The selected sub image is an even integer (sub image must have a center pixel, "
                                    "therefore, its size must be an odd integer)", exception=ValueError)

    # Setting the positions for the rows.
    row_start = position[0] - (sub_image_size // 2)
    row_end = position[0] + (sub_image_size // 2) + 1

    # Setting the positions for the cols.
    col_start = position[1] - (sub_image_size // 2)
    col_end = position[1] + (sub_image_size // 2) + 1

    # Extracting the sub image.
    sub_image = image[row_start:row_end, col_start:col_end]

    return sub_image


def contrast_stretching(image: ndarray) -> ndarray:
    """
    Perform contrast stretching on an image. Contrast stretching is useful only when the image has values which are
    outside the normal range [0, 1]. This normally happens when performing high-pass filtering (image sharpening).

    :param image: The image for contrast stretching.
    :return: Image with pixels values stretched to range [0, 1].
    """

    log.info("Stretching the contrast of the image to the range of [0, 1]")

    log.debug("Calculating the min/max values found in the image")
    max_value = np.max(image)
    log.debug(f"Maximum value is - {max_value}")
    min_value = np.min(image)
    log.debug(f"Minimum value is - {min_value}")

    log.debug("Calculating the slope")
    # Slope m maps [min, max] → [0, 1] via the linear transform: out = m * (pixel - min).
    m = 1 / (max_value - min_value)
    log.debug(f"Slope is - {m}")

    log.warning("Assuming that the normal pixel value range for the image is - [0, 1] "
                "(apply the scale_image function if not)")
    return m * (image[:, :] - min_value)


"""
In order to identify objects in a digital pattern, we need to locate groups of black pixels that are "connected" to each 
other. In other words, the objects in a given digital pattern are the connected components of that pattern.
 
In general, a connected component is a set of black pixels, P, such that for every pair of pixels pi and pj in P, there 
exists a sequence of pixels  pi, ..., pj such that:
a) All pixels in the sequence are in the set P i.e. are black.
b) Every 2 pixels that are adjacent in the sequence are "neighbors".

This gives rise to 2 types of connectedness, namely: 4-connectivity (also known as a direct-neighbor) and 8-connectivity 
(also known as an indirect-neighbor).
"""


@log_suppression(level=logging.ERROR)
def connected_component_4(image: ndarray, row, col) -> ndarray:
    """
    Find the 4-connected component in regard to the given pixel.

    Definition of a 4-neighbor:
    A pixel, Q, is a 4-neighbor of a given pixel, P, if Q and P share an edge. The 4-neighbors of pixel P (namely pixels
    P2,P4,P6 and P8) are shown below,
                                                          P2

                                                    P8    P     P4

                                                          P6

    Definition of a 4-connected component:
    A set of black pixels, P, is a 4-connected component if for every pair of pixels pi and pj in P, there exists a
    sequence of pixels  pi, ..., pj such that:
    a) All pixels in the sequence are in the set P i.e. are black.
    b) Every 2 pixels that are adjacent in the sequence are 4-neighbors.

    Assumptions:
    1) The image is binary.
    2) The provided pixel is part of the connected component, therefore, it is always tagged.

    :param image: Binary image.
    :param row: Row number of the given pixel.
    :param col: Column number of the given pixel.

    :return: 4-Connected component of the given pixel.
    """

    # Initializing the connected components image (with the selected pixel as on).
    connected_image = np.zeros(shape=image.shape)
    connected_image[row][col] = 1

    # Stopping condition - Check if there are any 4-connected components.
    if not image[row][col-1] and not image[row][col+1] and not image[row-1][col] and not image[row+1][col]:
        return connected_image

    # Zeroing the visited pixel prevents revisiting it via a different path (avoids infinite recursion).
    copy_image = copy.deepcopy(image)
    copy_image[row][col] = 0

    # Recursion advancement.
    # Proceed to the next 4-neighbor pixels, while avoiding cyclic paths.
    if image[row][col - 1] and col != 0:  # Left.
        connected_image += connected_component_4(image=copy_image, row=row, col=col - 1)
    if image[row][col + 1] and col != image.shape[1] - 1:  # Right.
        connected_image += connected_component_4(image=copy_image, row=row, col=col + 1)
    if image[row - 1][col] and row != 0:  # Up.
        connected_image += connected_component_4(image=copy_image, row=row - 1, col=col)
    if image[row + 1][col] and row != image.shape[0] - 1:  # Down.
        connected_image += connected_component_4(image=copy_image, row=row + 1, col=col)

    # When the connected image is accumulated, it can have the same pixel value added more than once, thus creating
    # values above 1. Therefore, a cutoff normalization is necessary.
    return image_normalization(image=connected_image, normalization_method='cutoff')


@log_suppression(level=logging.ERROR)
def connected_component_8(image: ndarray, row, col) -> ndarray:
    """
    Find the 8-connected component in regard to the given pixel.

    Definition of an 8-neighbor:
    A pixel, Q, is an 8-neighbor (or simply a neighbor) of a given pixel, P, if Q and P either share an edge or a
    vertex. The 8-neighbors of a given pixel P make up the Moore neighborhood (3x3 neighborhood) of that pixel.

    Definition of an 8-connected component:
    A set of black pixels, P, is an 8-connected component if for every pair of pixels pi and pj in P, there exists a
    sequence of pixels  pi, ..., pj such that:
    a) All pixels in the sequence are in the set P i.e. are black.
    b) Every 2 pixels that are adjacent in the sequence are 8-neighbors.

    Note - All 4-connected patterns are 8-connected i.e. 4-connected patterns are a subset of the set of 8-connected
    patterns. On the other hand, an 8-connected pattern may not be 4-connected.

    Assumptions:
    1) The image is binary.
    2) The provided pixel is part of the connected component, therefore, it is always tagged.

    :param image: Binary image.
    :param row: Row number of the given pixel.
    :param col: Column number of the given pixel.

    :return: 8-Connected component of the given pixel.
    """

    # Initializing the connected components image (with the selected pixel as on).
    connected_image = np.zeros(shape=image.shape)
    connected_image[row][col] = 1

    # Stopping condition - Check if there are any 8-connected components.
    if not image[row][col-1] and not image[row][col+1] and not image[row-1][col] and not image[row+1][col]\
       and not image[row-1][col-1] and not image[row+1][col-1] and not image[row-1][col+1] and not image[row+1][col+1]:
        return connected_image

    # Zeroing the visited pixel prevents revisiting it via a different diagonal or cardinal path.
    copy_image = copy.deepcopy(image)
    copy_image[row][col] = 0

    # Recursion advancement.
    # Proceed to the next 4-neighbor pixels, while avoiding cyclic paths.
    if image[row][col-1] and col != 0:  # Left.
        connected_image += connected_component_8(image=copy_image, row=row, col=col - 1)
    if image[row][col+1] and col != image.shape[1] - 1:  # Right.
        connected_image += connected_component_8(image=copy_image, row=row, col=col + 1)
    if image[row-1][col] and row != 0:  # Up.
        connected_image += connected_component_8(image=copy_image, row=row - 1, col=col)
    if image[row+1][col] and row != image.shape[0] - 1:  # Down.
        connected_image += connected_component_8(image=copy_image, row=row + 1, col=col)
    # Proceed to the next non-4-neighbor pixels, while avoiding cyclic paths.
    if image[row-1][col-1] and row != 0 and col != 0:
        connected_image += connected_component_8(image=copy_image, row=row - 1, col=col - 1)
    if image[row+1][col-1] and row != image.shape[0] - 1 and col != 0:
        connected_image += connected_component_8(image=copy_image, row=row + 1, col=col - 1)
    if image[row-1][col+1] and row != 0 and col != image.shape[1] - 1:
        connected_image += connected_component_8(image=copy_image, row=row - 1, col=col + 1)
    if image[row+1][col+1] and row != image.shape[0] - 1 and col != image.shape[1] - 1:
        connected_image += connected_component_8(image=copy_image, row=row + 1, col=col + 1)

    # When the connected image is accumulated, it can have the same pixel value added more than once, thus creating
    # values above 1. Therefore, a cutoff normalization is necessary.
    return image_normalization(image=connected_image, normalization_method='cutoff')
