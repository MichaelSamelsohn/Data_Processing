# Imports #
import numpy as np
import pytest

from Image_Processing.Source.Advanced.intensity_transformations import negative, gamma_correction
from constants import *


# ──────────────────────────────────────────────────────────── #
#  negative tests                                               #
# ──────────────────────────────────────────────────────────── #

def test_negative_known_values():
    """
    Test purpose - Basic functionality of the image negative operation.
    Criteria - Every pixel value is replaced by 1 minus its original value.

    Test steps:
    1) Apply negative to KNOWN_3x3.
    2) Assert that the result equals (1 - KNOWN_3x3) element-wise.
    """

    # Steps (1)+(2) - Apply negative and assert.
    result = negative(image=KNOWN_3x3)
    np.testing.assert_array_equal(result, 1 - KNOWN_3x3)


def test_negative_uniform_image():
    """
    Test purpose - Negative of a uniform image produces a uniform image.
    Criteria - All pixels of the negative of UNIFORM_5x5 equal 0.5.

    Test steps:
    1) Apply negative to UNIFORM_5x5 (all pixels = 0.5).
    2) Assert that all pixels in the result equal 0.5 (1 - 0.5 = 0.5).
    """

    # Steps (1)+(2) - Apply negative and assert.
    result = negative(image=UNIFORM_5x5)
    np.testing.assert_array_equal(result, np.full_like(UNIFORM_5x5, 0.5))


def test_negative_double_negative_is_identity():
    """
    Test purpose - Applying negative twice recovers the original image.
    Criteria - negative(negative(image)) == image for any image.

    Test steps:
    1) Apply negative twice to KNOWN_3x3.
    2) Assert that the result is identical to KNOWN_3x3.
    """

    # Steps (1)+(2) - Double-negate and assert identity.
    result = negative(image=negative(image=KNOWN_3x3))
    np.testing.assert_array_almost_equal(result, KNOWN_3x3, decimal=10)


def test_negative_binary_ones_becomes_zeros():
    """
    Test purpose - The negative of an all-ones binary image is all zeros.
    Criteria - negative(BINARY_ONES_5x5) == BINARY_ZEROS_5x5.

    Test steps:
    1) Apply negative to BINARY_ONES_5x5.
    2) Assert that the result equals BINARY_ZEROS_5x5.
    """

    # Steps (1)+(2) - Apply and assert.
    result = negative(image=BINARY_ONES_5x5)
    np.testing.assert_array_equal(result, BINARY_ZEROS_5x5)


# ──────────────────────────────────────────────────────────── #
#  gamma_correction tests                                       #
# ──────────────────────────────────────────────────────────── #

def test_gamma_correction_identity():
    """
    Test purpose - Gamma correction with gamma=1 is the identity transformation.
    Criteria - gamma_correction(image, gamma=1) returns the image unchanged.

    Test steps:
    1) Apply gamma correction with gamma=1.0 to KNOWN_3x3.
    2) Assert that the result equals KNOWN_3x3.
    """

    # Steps (1)+(2) - Apply gamma=1 and assert identity.
    result = gamma_correction(image=KNOWN_3x3, gamma=1.0)
    np.testing.assert_array_almost_equal(result, KNOWN_3x3, decimal=10)


@pytest.mark.parametrize(
    "gamma, comparison",
    [
        (0.5, "brighter"),  # gamma < 1 brightens (raises power < 1 of values in (0,1)).
        (2.0, "darker"),    # gamma > 1 darkens (raises power > 1 of values in (0,1)).
    ]
)
def test_gamma_correction_direction(gamma, comparison):
    """
    Test purpose - Gamma correction shifts pixel intensities in the expected direction.
    Criteria - For gamma < 1 the corrected image is brighter (values closer to 1) than the original;
    for gamma > 1 it is darker (values closer to 0).

    Test steps:
    1) Apply gamma correction with the parametrized gamma to RAMP_5x5 (excludes 0 and 1).
    2) Assert that the mean of the result is higher (brighter) or lower (darker) than the original mean.
    """

    # Step (1) - Apply gamma correction (excluding boundary pixels 0 and 1).
    interior = RAMP_5x5[:, 1:4]  # Columns 1-3 have values 0.25, 0.5, 0.75.
    result = gamma_correction(image=interior, gamma=gamma)

    # Step (2) - Assert direction of change.
    if comparison == "brighter":
        assert np.mean(result) > np.mean(interior)
    else:
        assert np.mean(result) < np.mean(interior)


def test_gamma_correction_known_values():
    """
    Test purpose - Gamma correction computes the power function element-wise.
    Criteria - gamma_correction(image, gamma=2) equals image ** 2 element-wise.

    Test steps:
    1) Apply gamma correction with gamma=2 to KNOWN_3x3.
    2) Assert that the result equals KNOWN_3x3 ** 2 element-wise.
    """

    # Steps (1)+(2) - Apply gamma=2 and assert.
    result = gamma_correction(image=KNOWN_3x3, gamma=2)
    np.testing.assert_array_almost_equal(result, KNOWN_3x3 ** 2, decimal=10)


def test_gamma_correction_output_shape():
    """
    Test purpose - Gamma correction preserves the spatial dimensions of the input.
    Criteria - The output shape of gamma_correction equals the input shape.

    Test steps:
    1) Apply gamma correction with gamma=0.5 to KNOWN_3x3.
    2) Assert that the output shape equals the input shape.
    """

    # Steps (1)+(2) - Apply and assert shape.
    result = gamma_correction(image=KNOWN_3x3, gamma=0.5)
    assert result.shape == KNOWN_3x3.shape