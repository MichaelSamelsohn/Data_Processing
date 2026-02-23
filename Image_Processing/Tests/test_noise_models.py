# Imports #
import numpy as np
import pytest

from Image_Processing.Source.Advanced.noise_models import (
    add_gaussian_noise, add_uniform_noise, add_salt_and_pepper,
    add_rayleigh_noise, add_exponential_noise, generate_noise,
)
from constants import *


# ──────────────────────────────────────────────────────────── #
#  add_gaussian_noise tests                                     #
# ──────────────────────────────────────────────────────────── #

def test_gaussian_noise_output_shape():
    """
    Test purpose - Gaussian noise addition preserves the spatial dimensions of the input.
    Criteria - The output of add_gaussian_noise has the same shape as the input image.

    Test steps:
    1) Add Gaussian noise to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Add noise and assert shape.
    result = add_gaussian_noise(image=KNOWN_3x3, mean=0, sigma=0.01)
    assert result.shape == KNOWN_3x3.shape


def test_gaussian_noise_output_in_range():
    """
    Test purpose - Gaussian noise addition produces output values within [0, 1].
    Criteria - After applying cutoff normalization, all pixels are clipped to [0, 1].

    Test steps:
    1) Add Gaussian noise to KNOWN_3x3.
    2) Assert that all pixel values are >= 0.
    3) Assert that all pixel values are <= 1.
    """

    # Step (1) - Add noise.
    result = add_gaussian_noise(image=KNOWN_3x3, mean=0, sigma=0.01)

    # Steps (2)+(3) - Assert range.
    assert result.min() >= 0
    assert result.max() <= 1


# ──────────────────────────────────────────────────────────── #
#  add_uniform_noise tests                                      #
# ──────────────────────────────────────────────────────────── #

def test_uniform_noise_output_shape():
    """
    Test purpose - Uniform noise addition preserves the spatial dimensions of the input.
    Criteria - The output of add_uniform_noise has the same shape as the input image.

    Test steps:
    1) Add uniform noise to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Add noise and assert shape.
    result = add_uniform_noise(image=KNOWN_3x3, a=-0.1, b=0.1)
    assert result.shape == KNOWN_3x3.shape


def test_uniform_noise_output_in_range():
    """
    Test purpose - Uniform noise addition produces output values within [0, 1].
    Criteria - After applying cutoff normalization, all pixels are clipped to [0, 1].

    Test steps:
    1) Add uniform noise to KNOWN_3x3 with range [-0.1, 0.1].
    2) Assert that all pixel values are >= 0.
    3) Assert that all pixel values are <= 1.
    """

    # Step (1) - Add noise.
    result = add_uniform_noise(image=KNOWN_3x3, a=-0.1, b=0.1)

    # Steps (2)+(3) - Assert range.
    assert result.min() >= 0
    assert result.max() <= 1


# ──────────────────────────────────────────────────────────── #
#  add_salt_and_pepper tests                                    #
# ──────────────────────────────────────────────────────────── #

def test_salt_and_pepper_output_shape():
    """
    Test purpose - Salt-and-pepper noise addition preserves the spatial dimensions of the input.
    Criteria - The output of add_salt_and_pepper has the same shape as the input image.

    Test steps:
    1) Add salt-and-pepper noise to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Add noise and assert shape.
    result = add_salt_and_pepper(image=KNOWN_3x3, pepper=0.1, salt=0.1)
    assert result.shape == KNOWN_3x3.shape


def test_salt_and_pepper_zero_noise_unchanged():
    """
    Test purpose - Salt-and-pepper with zero probability leaves the image unchanged.
    Criteria - When both pepper and salt probabilities are 0, every pixel retains its original value.

    Test steps:
    1) Add salt-and-pepper noise to KNOWN_3x3 with pepper=0 and salt=0.
    2) Assert that the result equals KNOWN_3x3.
    """

    # Steps (1)+(2) - Add zero noise and assert identity.
    result = add_salt_and_pepper(image=KNOWN_3x3, pepper=0, salt=0)
    np.testing.assert_array_equal(result, KNOWN_3x3)


def test_salt_and_pepper_output_values_in_range():
    """
    Test purpose - Salt-and-pepper noise produces output values within [0, 1].
    Criteria - Each pixel is set to 0, 1, or the original value; all are within [0, 1].

    Test steps:
    1) Add salt-and-pepper noise to KNOWN_3x3 with moderate probabilities.
    2) Assert that all pixel values are >= 0.
    3) Assert that all pixel values are <= 1.
    """

    # Step (1) - Add noise.
    result = add_salt_and_pepper(image=KNOWN_3x3, pepper=0.1, salt=0.1)

    # Steps (2)+(3) - Assert range.
    assert result.min() >= 0
    assert result.max() <= 1


# ──────────────────────────────────────────────────────────── #
#  add_rayleigh_noise tests                                     #
# ──────────────────────────────────────────────────────────── #

def test_rayleigh_noise_output_shape():
    """
    Test purpose - Rayleigh noise addition preserves the spatial dimensions of the input.
    Criteria - The output of add_rayleigh_noise has the same shape as the input image.

    Test steps:
    1) Add Rayleigh noise to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Add noise and assert shape.
    result = add_rayleigh_noise(image=KNOWN_3x3, a=-0.125, b=0.01)
    assert result.shape == KNOWN_3x3.shape


def test_rayleigh_noise_output_in_range():
    """
    Test purpose - Rayleigh noise addition produces output values within [0, 1].
    Criteria - After applying cutoff normalization, all pixels are clipped to [0, 1].

    Test steps:
    1) Add Rayleigh noise to KNOWN_3x3.
    2) Assert that all pixel values are >= 0.
    3) Assert that all pixel values are <= 1.
    """

    # Step (1) - Add noise.
    result = add_rayleigh_noise(image=KNOWN_3x3, a=-0.125, b=0.01)

    # Steps (2)+(3) - Assert range.
    assert result.min() >= 0
    assert result.max() <= 1


# ──────────────────────────────────────────────────────────── #
#  add_exponential_noise tests                                  #
# ──────────────────────────────────────────────────────────── #

def test_exponential_noise_output_shape():
    """
    Test purpose - Exponential noise addition preserves the spatial dimensions of the input.
    Criteria - The output of add_exponential_noise has the same shape as the input image.

    Test steps:
    1) Add exponential noise to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Add noise and assert shape.
    result = add_exponential_noise(image=KNOWN_3x3, a=50)
    assert result.shape == KNOWN_3x3.shape


def test_exponential_noise_output_in_range():
    """
    Test purpose - Exponential noise addition produces output values within [0, 1].
    Criteria - After applying cutoff normalization, all pixels are clipped to [0, 1].

    Test steps:
    1) Add exponential noise to KNOWN_3x3.
    2) Assert that all pixel values are >= 0.
    3) Assert that all pixel values are <= 1.
    """

    # Step (1) - Add noise.
    result = add_exponential_noise(image=KNOWN_3x3, a=50)

    # Steps (2)+(3) - Assert range.
    assert result.min() >= 0
    assert result.max() <= 1


# ──────────────────────────────────────────────────────────── #
#  generate_noise tests                                         #
# ──────────────────────────────────────────────────────────── #

def test_generate_noise_output_in_range():
    """
    Test purpose - generate_noise clips the noisy image to [0, 1] using cutoff normalization.
    Criteria - All pixels of the noisy output are within [0, 1].

    Test steps:
    1) Define a simple uniform probability distribution over noise values [−1, 1].
    2) Call generate_noise with KNOWN_3x3.
    3) Assert that all pixel values are >= 0 and <= 1.
    """

    # Step (1) - Uniform distribution over [-1, 1].
    pixel_intensity_values = np.linspace(-1, 1, 513)
    probability_distribution = np.ones(513) / 513

    # Step (2) - Generate noisy image.
    result = generate_noise(image=KNOWN_3x3, pixel_intensity_values=pixel_intensity_values,
                            probability_distribution=probability_distribution)

    # Step (3) - Assert range.
    assert result.min() >= 0
    assert result.max() <= 1


def test_generate_noise_output_shape():
    """
    Test purpose - generate_noise preserves the spatial dimensions of the input.
    Criteria - The output shape of generate_noise equals the input image shape.

    Test steps:
    1) Define a simple probability distribution.
    2) Call generate_noise with KNOWN_3x3.
    3) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Define distribution and generate.
    pixel_intensity_values = np.linspace(-1, 1, 513)
    probability_distribution = np.ones(513) / 513
    result = generate_noise(image=KNOWN_3x3, pixel_intensity_values=pixel_intensity_values,
                            probability_distribution=probability_distribution)

    # Step (3) - Assert shape.
    assert result.shape == KNOWN_3x3.shape