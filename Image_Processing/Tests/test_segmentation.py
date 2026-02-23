# Imports #
import numpy as np
import pytest

from Image_Processing.Source.Advanced.segmentation import (
    thresholding, global_thresholding, otsu_global_thresholding, zero_crossing,
)
from constants import *


# ──────────────────────────────────────────────────────────── #
#  thresholding tests                                           #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize(
    "image, threshold_value, expected",
    [
        (
            BINARY_ONES_5x5, 0.5,
            np.ones((5, 5)),
        ),
        (
            BINARY_ZEROS_5x5, 0.5,
            np.zeros((5, 5)),
        ),
    ]
)
def test_thresholding_all_ones_and_zeros(image, threshold_value, expected):
    """
    Test purpose - Correct thresholding of uniform binary images.
    Criteria - An all-ones image thresholded above 0.5 remains all ones; an all-zeros image
    thresholded above 0.5 remains all zeros.

    Test steps:
    1) Apply thresholding to the parametrized image with threshold 0.5.
    2) Assert that the result equals the expected binary image.
    """

    # Steps (1)+(2) - Threshold and assert.
    result = thresholding(image=image, threshold_value=threshold_value)
    np.testing.assert_array_equal(result, expected)


def test_thresholding_known_values():
    """
    Test purpose - Correct pixel-wise thresholding of a mixed-value image.
    Criteria - KNOWN_3x3 thresholded at 0.5 produces 1 where value > 0.5 and 0 elsewhere.
    Values exactly equal to 0.5 are NOT strictly above the threshold and map to 0.

    Test steps:
    1) Apply thresholding to KNOWN_3x3 with threshold 0.5.
    2) Assert that the result matches the expected binary pattern.
    """

    # Steps (1)+(2) - Threshold and assert.
    result = thresholding(image=KNOWN_3x3, threshold_value=0.5)
    expected = np.array([
        [0, 0, 1],  # 0.1 <= 0.5 → 0; 0.5 not > 0.5 → 0; 0.9 > 0.5 → 1.
        [0, 1, 0],  # 0.3 ≤ 0.5 → 0; 0.7 > 0.5 → 1; 0.2 ≤ 0.5 → 0.
        [1, 0, 1],  # 0.8 > 0.5 → 1; 0.4 ≤ 0.5 → 0; 0.6 > 0.5 → 1.
    ], dtype=float)
    np.testing.assert_array_equal(result, expected)


def test_thresholding_output_is_binary():
    """
    Test purpose - The output of thresholding is a binary image.
    Criteria - Every pixel in the thresholded image is either 0.0 or 1.0.

    Test steps:
    1) Apply thresholding to KNOWN_3x3 with threshold 0.5.
    2) Assert that all pixel values are in {0.0, 1.0}.
    """

    # Steps (1)+(2) - Threshold and assert binary.
    result = thresholding(image=KNOWN_3x3, threshold_value=0.5)
    assert set(np.unique(result)).issubset({0.0, 1.0})


def test_thresholding_output_shape():
    """
    Test purpose - Thresholding preserves the spatial dimensions of the input.
    Criteria - The output shape of thresholding equals the input shape.

    Test steps:
    1) Apply thresholding to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Threshold and assert shape.
    result = thresholding(image=KNOWN_3x3, threshold_value=0.5)
    assert result.shape == KNOWN_3x3.shape


# ──────────────────────────────────────────────────────────── #
#  global_thresholding tests                                    #
# ──────────────────────────────────────────────────────────── #

def test_global_thresholding_output_is_binary():
    """
    Test purpose - Global thresholding produces a binary image.
    Criteria - Every pixel in the result is either 0.0 or 1.0.

    Test steps:
    1) Apply global thresholding to KNOWN_3x3 with an initial threshold of 0.5.
    2) Assert that all pixel values are in {0.0, 1.0}.
    """

    # Steps (1)+(2) - Threshold and assert binary.
    result = global_thresholding(image=KNOWN_3x3, initial_threshold=0.5, delta_t=0.01)
    assert set(np.unique(result)).issubset({0.0, 1.0})


def test_global_thresholding_output_shape():
    """
    Test purpose - Global thresholding preserves the spatial dimensions of the input.
    Criteria - The output shape of global_thresholding equals the input shape.

    Test steps:
    1) Apply global thresholding to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Threshold and assert shape.
    result = global_thresholding(image=KNOWN_3x3, initial_threshold=0.5, delta_t=0.01)
    assert result.shape == KNOWN_3x3.shape


def test_global_thresholding_uniform_image():
    """
    Test purpose - Global thresholding on a two-level image converges to a consistent partition.
    Criteria - For RAMP_5x5 with initial threshold 0.5, the result is a binary image that
    matches a simple threshold at the converged value.

    Test steps:
    1) Apply global thresholding to RAMP_5x5 with initial threshold 0.5.
    2) Assert that the output is a binary image.
    3) Assert that the output shape matches RAMP_5x5.
    """

    # Steps (1)+(2)+(3) - Threshold and assert.
    result = global_thresholding(image=RAMP_5x5, initial_threshold=0.5, delta_t=0.01)
    assert set(np.unique(result)).issubset({0.0, 1.0})
    assert result.shape == RAMP_5x5.shape


# ──────────────────────────────────────────────────────────── #
#  otsu_global_thresholding tests                               #
# ──────────────────────────────────────────────────────────── #

def test_otsu_thresholding_output_is_binary():
    """
    Test purpose - Otsu's thresholding produces a binary image.
    Criteria - Every pixel in the result is either 0.0 or 1.0.

    Test steps:
    1) Apply Otsu's global thresholding to KNOWN_3x3.
    2) Assert that all pixel values are in {0.0, 1.0}.
    """

    # Steps (1)+(2) - Threshold and assert binary.
    result = otsu_global_thresholding(image=KNOWN_3x3)
    assert set(np.unique(result)).issubset({0.0, 1.0})


def test_otsu_thresholding_output_shape():
    """
    Test purpose - Otsu's thresholding preserves the spatial dimensions of the input.
    Criteria - The output shape of otsu_global_thresholding equals the input shape.

    Test steps:
    1) Apply Otsu's global thresholding to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Threshold and assert shape.
    result = otsu_global_thresholding(image=KNOWN_3x3)
    assert result.shape == KNOWN_3x3.shape


# ──────────────────────────────────────────────────────────── #
#  zero_crossing tests                                          #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize(
    "sub_image, threshold, expected",
    [
        # Horizontal zero crossing: left positive, right negative, difference > threshold.
        (
            np.array([[0, 0, 0], [1.0, 0, -1.0], [0, 0, 0]]),
            0.5,
            1,
        ),
        # Vertical zero crossing: top positive, bottom negative, difference > threshold.
        (
            np.array([[0, 1.0, 0], [0, 0, 0], [0, -1.0, 0]]),
            0.5,
            1,
        ),
        # No zero crossing: all positive values.
        (
            np.array([[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, 0.5]]),
            0.1,
            0,
        ),
    ]
)
def test_zero_crossing_detection(sub_image, threshold, expected):
    """
    Test purpose - Correct detection of zero crossings in a 3×3 sub-image.
    Criteria - A horizontal or vertical sign change whose absolute difference exceeds the
    threshold is detected as a zero crossing (returns 1); otherwise returns 0.

    Test steps:
    1) Call zero_crossing with the parametrized sub-image and threshold.
    2) Assert that the return value matches the expected result.
    """

    # Steps (1)+(2) - Detect and assert.
    result = zero_crossing(sub_image=sub_image, threshold=threshold)
    assert result == expected


def test_zero_crossing_below_threshold_not_detected():
    """
    Test purpose - Zero crossings with difference below threshold are not detected.
    Criteria - A small sign change whose absolute difference is less than the threshold
    returns 0.

    Test steps:
    1) Create a sub-image with a small horizontal sign change (difference < threshold).
    2) Call zero_crossing with a threshold that exceeds the difference.
    3) Assert that the result is 0.
    """

    # Step (1) - Small sign change that is below the threshold.
    sub_image = np.array([[0, 0, 0], [0.1, 0, -0.1], [0, 0, 0]])

    # Steps (2)+(3) - Detect and assert.
    result = zero_crossing(sub_image=sub_image, threshold=0.5)
    assert result == 0