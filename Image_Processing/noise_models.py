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


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 5.2 - Restoration in the Presence of Noise Only—Spatial Filtering, p.319-320")
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

    log.debug("Calculating the probability distribution and generating the noise")
    noise = np.zeros(shape=image.shape)
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            # Calculating the probability distribution.
            exponent_factor = -np.power(pixel_intensity_values - mean, 2) / exponent_factor_denominator
            probability_distribution = constant * np.exp(exponent_factor)
            probability_distribution /= probability_distribution.sum()  # Normalizing the distribution vector.

            # Randomizing noise value.
            noise[row][col] = random.choice(pixel_intensity_values, p=probability_distribution)

    log.debug("Adding the noise to the image (and normalizing it to avoid out of range values)")
    noisy_image = image_normalization(image=image + noise, normalization_method="cutoff")  # Normalization.

    return noisy_image


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 5.2 - Restoration in the Presence of Noise Only—Spatial Filtering, p.320")
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

    log.debug("Calculating the probability distribution and generating the noise")
    noise = np.zeros(shape=image.shape)
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            # Calculating the probability distribution.
            exponent_factor = -np.power(pixel_intensity_values - a, 2) / b
            probability_distribution = (2 / b) * (pixel_intensity_values - a) * np.exp(exponent_factor)
            """
            The following operation is to ensure that no values in pixel_intensity_values below a are non-zero. Due to 
            the calculation above, if pixel_intensity_values < a, then it follows that (pixel_intensity_values - a) < 0,
            and it is the only condition that causes the probability_distribution to be negative at lower values (b is 
            positive and so does an exponential value). Therefore, it is enough to nullify values according to condition
            probability_distribution < 0.  
            """
            probability_distribution[probability_distribution < 0] = 0
            probability_distribution /= probability_distribution.sum()  # Normalizing the distribution vector.

            # Randomizing noise value.
            noise[row][col] = random.choice(pixel_intensity_values, p=probability_distribution)

    log.debug("Adding the noise to the image (and normalizing it to avoid out of range values)")
    noisy_image = image_normalization(image=image + noise, normalization_method="cutoff")  # Normalization.

    return noisy_image


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

    log.debug("Calculating the probability distribution and generating the noise")
    noise = np.zeros(shape=image.shape)
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            # Calculating the probability distribution.
            exponent_factor = -a * pixel_intensity_values
            nominator_factor = np.power(a, b) * np.power(pixel_intensity_values, b - 1)
            denominator_factor = math.factorial(b - 1)
            probability_distribution = (nominator_factor * np.exp(exponent_factor)) / denominator_factor
            probability_distribution /= probability_distribution.sum()  # Normalizing the distribution vector.

            # Randomizing noise value.
            noise[row][col] = random.choice(pixel_intensity_values, p=probability_distribution)

    log.debug("Adding the noise to the image (and normalizing it to avoid out of range values)")
    noisy_image = image_normalization(image=image + noise, normalization_method="cutoff")  # Normalization.

    return noisy_image


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 5.2 - Restoration in the Presence of Noise Only—Spatial Filtering, p.320-321")
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

    log.debug("Calculating the probability distribution and generating the noise")
    noise = np.zeros(shape=image.shape)
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            # Calculating the probability distribution.
            probability_distribution = a * np.exp(-a * pixel_intensity_values)
            probability_distribution /= probability_distribution.sum()  # Normalizing the distribution vector.

            # Randomizing noise value.
            noise[row][col] = random.choice(pixel_intensity_values, p=probability_distribution)

    log.debug("Adding the noise to the image (and normalizing it to avoid out of range values)")
    noisy_image = image_normalization(image=image + noise, normalization_method="cutoff")  # Normalization.

    return noisy_image


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 5.2 - Restoration in the Presence of Noise Only—Spatial Filtering, p.320-322")
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

    log.debug("Calculating the probability distribution and generating the noise")
    noise = np.zeros(shape=image.shape)
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            # Calculating the probability distribution.
            probability_distribution = np.ones(513)
            probability_distribution[pixel_intensity_values < a] = 0  # Nullifying left out-of-range values.
            probability_distribution[pixel_intensity_values > b] = 0  # Nullifying right out-of-range values.
            probability_distribution /= probability_distribution.sum()  # Normalizing the distribution vector.

            # Randomizing noise value.
            noise[row][col] = random.choice(pixel_intensity_values, p=probability_distribution)

    log.debug("Adding the noise to the image (and normalizing it to avoid out of range values)")
    noisy_image = image_normalization(image=image + noise, normalization_method="cutoff")  # Normalization.

    return noisy_image


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 5.2 - Restoration in the Presence of Noise Only—Spatial Filtering, p.322-324")
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


# TODO: Add a method (two images as input) to deduct (string as output) the noise type.