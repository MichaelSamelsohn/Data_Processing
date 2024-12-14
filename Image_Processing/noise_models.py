"""
Script Name - noise_models.py

Created by Michael Samelsohn, 11/12/24
"""

# Imports #
import math
import numpy as np
from numpy import ndarray, random
from Basic.common import image_normalization
from Settings.image_settings import *
from Utilities.decorators import book_reference
from Settings.settings import log


@book_reference(book=GONZALES_WOODS_BOOK, reference="Chapter 5.2 - Noise Models, p.319-320")
def add_gaussian_noise(image: ndarray, mean=DEFAULT_GAUSSIAN_MEAN, sigma=DEFAULT_GAUSSIAN_SIGMA) -> ndarray:
    """
    Add Gaussian noise to an image.
    TODO: Extend the docstring.

    Assumption - The image pixel values range is [0, 1].

    :param image: The image for distortion.
    :param mean: The mean value of the Gaussian distribution (the value with the highest probability).
    :param sigma: The standard deviation of the Gaussian distribution.

    :return: Noisy image.
    """

    log.info("Adding Gaussian noise to the image")

    log.debug("Generating array of possible random values - [-1, 1]")
    pixel_intensity_values = np.linspace(-1, 1, 513)

    log.debug("Calculating the Gaussian constants")
    constant = 1 / (np.sqrt(2 * np.pi) * sigma)
    exponent_factor_denominator = (2 * np.power(sigma, 2))

    log.debug("Calculating the probability distribution")
    exponent_factor = -np.power(pixel_intensity_values - mean, 2) / exponent_factor_denominator
    probability_distribution = constant * np.exp(exponent_factor)
    probability_distribution /= probability_distribution.sum()  # Normalizing the distribution vector.

    # Generating noisy image.
    return generate_noise(image=image, pixel_intensity_values=pixel_intensity_values,
                          probability_distribution=probability_distribution)


@book_reference(book=GONZALES_WOODS_BOOK, reference="Chapter 5.2 - Noise Models, p.320")
def add_rayleigh_noise(image: ndarray, a=DEFAULT_RAYLEIGH_A, b=DEFAULT_RAYLEIGH_B) -> ndarray:
    """
    Add Rayleigh noise to an image.
    TODO: Extend the docstring.

    Assumption - The image pixel values range is [0, 1].

    :param image: The image for distortion.
    :param a: Parameter controlling the cutoff on the left side.
    :param b: Parameter controlling the probability of the most probable value.
    Note - Since the most probable value equals 0.607*sqrt(2/b), the lower b, the higher the probability that the random
    value is closer to the original one.

    :return: Noisy image.
    """

    log.info("Adding Rayleigh noise to the image")

    log.debug("Generating array of possible random values - [-1, 1]")
    pixel_intensity_values = np.linspace(-1, 1, 513)

    log.debug("Calculating the probability distribution")
    exponent_factor = -np.power(pixel_intensity_values - a, 2) / b
    probability_distribution = (2 / b) * (pixel_intensity_values - a) * np.exp(exponent_factor)
    """
    The following operation is to ensure that no values in pixel_intensity_values below a are non-zero. Due to the 
    calculation above, if pixel_intensity_values < a, then it follows that (pixel_intensity_values - a) < 0, and it is 
    the only condition that causes the probability_distribution to be negative at lower values (b is positive and so 
    does an exponential value). Therefore, it is enough to nullify values according to condition 
    probability_distribution < 0.  
    """
    probability_distribution[probability_distribution < 0] = 0
    probability_distribution /= probability_distribution.sum()  # Normalizing the distribution vector.

    # Generating noisy image.
    return generate_noise(image=image, pixel_intensity_values=pixel_intensity_values,
                          probability_distribution=probability_distribution)


@book_reference(book=GONZALES_WOODS_BOOK, reference="Chapter 5.2 - Noise Models, p.321")
def add_erlang_noise(image: ndarray, a=DEFAULT_ERLANG_A, b=DEFAULT_ERLANG_A) -> ndarray:
    """
    Add Erlang (Gamma) noise to an image.
    TODO: Extend the docstring.

    Assumption - The image pixel values range is [0, 1].

    :param image: The image for distortion.
    TODO: Complete the description fro a, b parameters.
    :param a: Must be bigger than b.
    :param b: Positive integer.

    :return: Noisy image.
    """

    log.info("Adding Erlang (Gamma) noise to the image")

    log.debug("Generating array of possible random values - [0, 1]")
    pixel_intensity_values = np.linspace(0, 1, 257)

    log.debug("Calculating the probability distribution")
    exponent_factor = -a * pixel_intensity_values
    nominator_factor = np.power(a, b) * np.power(pixel_intensity_values, b - 1)
    denominator_factor = math.factorial(b - 1)
    probability_distribution = (nominator_factor * np.exp(exponent_factor)) / denominator_factor
    probability_distribution /= probability_distribution.sum()  # Normalizing the distribution vector.

    # Generating noisy image.
    return generate_noise(image=image, pixel_intensity_values=pixel_intensity_values,
                          probability_distribution=probability_distribution)


@book_reference(book=GONZALES_WOODS_BOOK, reference="Chapter 5.2 - Noise Models, p.320-321")
def add_exponential_noise(image: ndarray, a=DEFAULT_EXPONENTIAL_DECAY) -> ndarray:
    """
    Add exponential noise to an image.
    TODO: Extend the docstring.

    Assumption - The image pixel values range is [0, 1].

    :param image: The image for distortion.
    :param a: Decay factor (the higher it is, the random value will be more likely to be zero).

    :return: Noisy image.
    """

    log.info("Adding exponential noise to the image")

    log.debug("Generating array of possible random values - [0, 1]")
    pixel_intensity_values = np.linspace(0, 1, 257)

    log.debug("Calculating the probability distribution")
    probability_distribution = a * np.exp(-a * pixel_intensity_values)
    probability_distribution /= probability_distribution.sum()  # Normalizing the distribution vector.

    # Generating noisy image.
    return generate_noise(image=image, pixel_intensity_values=pixel_intensity_values,
                          probability_distribution=probability_distribution)


@book_reference(book=GONZALES_WOODS_BOOK, reference="Chapter 5.2 - Noise Models, p.320-322")
def add_uniform_noise(image: ndarray, a=DEFAULT_UNIFORM_A, b=DEFAULT_UNIFORM_B) -> ndarray:
    """
    Add uniform noise to an image.
    TODO: Extend the docstring.

    Assumption - The image pixel values range is [0, 1].

    :param image: The image for distortion.
    :param a: Left value of the uniform range.
    :param b: Right value of the uniform range.

    :return: Noisy image.
    """

    log.info("Adding exponential noise to the image")

    log.debug("Generating array of possible random values - [-1, 1]")
    pixel_intensity_values = np.linspace(-1, 1, 513)

    log.debug("Calculating the probability distribution")
    probability_distribution = np.ones(513)
    probability_distribution[pixel_intensity_values < a] = 0  # Nullifying left out-of-range values.
    probability_distribution[pixel_intensity_values > b] = 0  # Nullifying right out-of-range values.
    probability_distribution /= probability_distribution.sum()  # Normalizing the distribution vector.

    # Generating noisy image.
    return generate_noise(image=image, pixel_intensity_values=pixel_intensity_values,
                          probability_distribution=probability_distribution)


@book_reference(book=GONZALES_WOODS_BOOK, reference="Chapter 5.2 - Noise Models, p.322-324")
def add_salt_and_pepper(image: ndarray, pepper=DEFAULT_PEPPER, salt=DEFAULT_SALT) -> ndarray:
    """
    Add salt and pepper (white and black) pixels to an image at random.
    TODO: Extend the docstring.

    :param image: The image for distortion.
    :param pepper: Percentage of black pixels to be randomized into the image.
    :param salt: Percentage of white pixels to be randomized into the image.

    :return: Noisy image.
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


def generate_noise(image: ndarray, pixel_intensity_values: ndarray, probability_distribution: ndarray) -> ndarray:
    """
    Generating noise process which includes three steps:
    1) Generate noise image according to provided parameters.
    2) Add the noise image to the original one.
    3) Normalize the noisy image, to avoid values out of range.

    :param image: The original image.
    :param pixel_intensity_values: The possible noise values.
    :param probability_distribution: The probability distribution for the noise.

    :return: Noisy image.
    """

    log.debug("Generating the noise")
    noise = np.zeros(shape=image.shape)
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            # Randomizing noise value.
            noise[row][col] = random.choice(pixel_intensity_values, p=probability_distribution)

    log.debug("Adding the noise to the original image")
    # Normalizing the noisy image to avoid out of range values.
    return image_normalization(image=image + noise, normalization_method="cutoff")


def identify_noise_model(image: ndarray, noisy_image: ndarray):
    """
    TODO: Complete the docstring.
    """

    # TODO: Check if images are identical (no noise).

    image_size = image.shape[0] * image.shape[1]

    delta = noisy_image - image

    mean = np.sum(delta) / image_size
    sigma_squared = np.sum(np.power(delta - mean, 2)) / image_size
    sigma = np.sqrt(sigma_squared)

    log.debug("Checking salt-and-pepper noise model")
    """
    If the noise model is salt-and-pepper, then all the "noisy pixels" (pixels in the noisy image that differ from the 
    original one) should either be black (0) or white (1). Therefore, we check if all noisy pixels are either [0] 
    (pepper only), [1] (salt only) or [0, 1] (salt-and-pepper).
    """
    noisy_pixels = noisy_image[delta != 0]
    unique_noise_values = np.unique(noisy_pixels)
    if len(unique_noise_values) <= 2:
        if (unique_noise_values == [0, 1]).all():
            return "salt-and-pepper"
        elif (unique_noise_values == [0]).all():
            return "pepper"
        elif (unique_noise_values == [1]).all():
            return "salt"

    log.debug("Calculating the histogram (and noise distribution) of the delta image (noise - original)")
    delta_histogram = np.zeros(513)
    noise_values = np.linspace(-1, 1, 513)
    for row in range(delta.shape[0]):
        for col in range(delta.shape[1]):
            delta_histogram[np.where(noise_values == delta[row][col])[0][0]] += 1
    noise_distribution = delta_histogram / np.sum(delta_histogram)

    log.debug("Checking uniform noise model")
    # TODO: Complete the explanation.
    """
    """
    if np.abs(np.min(noise_distribution[np.nonzero(noise_distribution)]) - np.max(noise_distribution)) < 0.01:
        return "uniform"

    log.debug("Checking Gaussian noise model")
    # TODO: Complete the explanation.
    """
    """
    most_probable_error_index = np.argmax(noise_distribution)
    left_side_distribution = np.sum(noise_distribution[:most_probable_error_index])
    right_side_distribution = np.sum(noise_distribution[most_probable_error_index + 1:])
    if (right_side_distribution - left_side_distribution) < 0.01:
        return "gaussian"

    return