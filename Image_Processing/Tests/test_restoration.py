# Imports #
import numpy as np
import pytest

from Image_Processing.Source.Advanced.restoration import mean_filter, order_statistic_filter
from constants import *


# ──────────────────────────────────────────────────────────── #
#  mean_filter tests                                            #
# ──────────────────────────────────────────────────────────── #

def test_mean_filter_output_shape():
    """
    Test purpose - Mean filtering preserves the spatial dimensions of the input.
    Criteria - The output of mean_filter has the same shape as the input image.

    Test steps:
    1) Apply an arithmetic mean filter to KNOWN_3x3.
    2) Assert that the output shape equals the input shape.
    """

    # Steps (1)+(2) - Filter and assert shape.
    result = mean_filter(image=KNOWN_3x3, filter_type='arithmetic',
                         padding_type='zero', filter_size=3)
    assert result.shape == KNOWN_3x3.shape


def test_mean_filter_arithmetic_center_value():
    """
    Test purpose - The arithmetic mean filter averages the neighbourhood.
    Criteria - For a uniform image, the center pixel is unchanged (average of equal values equals
    the same value).

    Test steps:
    1) Apply an arithmetic mean filter to UNIFORM_5x5 with filter size 3.
    2) Assert that the center pixel [2, 2] equals 0.5.
    """

    # Steps (1)+(2) - Filter and assert center value.
    result = mean_filter(image=UNIFORM_5x5, filter_type='arithmetic',
                         padding_type='zero', filter_size=3)
    np.testing.assert_almost_equal(result[2, 2], 0.5, decimal=10)


def test_mean_filter_geometric_center_value():
    """
    Test purpose - The geometric mean filter preserves a uniform neighbourhood.
    Criteria - For a uniform image, the center pixel computed as (0.5^9)^(1/9) = 0.5 is unchanged.

    Test steps:
    1) Apply a geometric mean filter to UNIFORM_5x5 with filter size 3.
    2) Assert that the center pixel [2, 2] equals 0.5.
    """

    # Steps (1)+(2) - Filter and assert center value.
    result = mean_filter(image=UNIFORM_5x5, filter_type='geometric',
                         padding_type='zero', filter_size=3)
    np.testing.assert_almost_equal(result[2, 2], 0.5, decimal=10)


@pytest.mark.parametrize(
    "filter_type",
    ["arithmetic", "geometric"],
)
def test_mean_filter_output_values_in_range(filter_type):
    """
    Test purpose - Mean filtering produces output values within [0, 1].
    Criteria - All pixels of the filtered image lie in [0, 1].

    Test steps:
    1) Apply the parametrized mean filter to KNOWN_3x3.
    2) Assert that all pixel values are >= 0.
    3) Assert that all pixel values are <= 1.
    """

    # Step (1) - Filter.
    result = mean_filter(image=KNOWN_3x3, filter_type=filter_type,
                         padding_type='zero', filter_size=3)

    # Steps (2)+(3) - Assert range.
    assert result.min() >= 0
    assert result.max() <= 1


# ──────────────────────────────────────────────────────────── #
#  order_statistic_filter tests                                 #
# ──────────────────────────────────────────────────────────── #

def test_order_statistic_filter_output_shape():
    """
    Test purpose - Order-statistic filtering preserves image dimensions.
    Criteria - The output of order_statistic_filter has the same shape as the input.

    Test steps:
    1) Apply a median order-statistic filter to KNOWN_3x3.
    2) Assert that the output shape equals the input shape.
    """

    # Steps (1)+(2) - Filter and assert shape.
    result = order_statistic_filter(image=KNOWN_3x3, filter_type='median',
                                    padding_type='zero', filter_size=3)
    assert result.shape == KNOWN_3x3.shape


def test_order_statistic_median_center_value():
    """
    Test purpose - The median filter selects the middle value of the neighbourhood.
    Criteria - For a uniform image, the median of a 3×3 all-0.5 neighbourhood is 0.5.

    Test steps:
    1) Apply a median filter to UNIFORM_5x5 with filter size 3.
    2) Assert that the center pixel [2, 2] equals 0.5.
    """

    # Steps (1)+(2) - Filter and assert center value.
    result = order_statistic_filter(image=UNIFORM_5x5, filter_type='median',
                                    padding_type='zero', filter_size=3)
    np.testing.assert_almost_equal(result[2, 2], 0.5, decimal=10)


def test_order_statistic_max_center_value():
    """
    Test purpose - The max filter selects the highest value in the neighbourhood.
    Criteria - For a uniform image, the max of an all-0.5 neighbourhood is 0.5.

    Test steps:
    1) Apply a max order-statistic filter to UNIFORM_5x5 with filter size 3.
    2) Assert that the center pixel [2, 2] equals 0.5.
    """

    # Steps (1)+(2) - Filter and assert center value.
    result = order_statistic_filter(image=UNIFORM_5x5, filter_type='max',
                                    padding_type='zero', filter_size=3)
    np.testing.assert_almost_equal(result[2, 2], 0.5, decimal=10)


def test_order_statistic_min_center_value():
    """
    Test purpose - The min filter selects the lowest value in the neighbourhood.
    Criteria - For a uniform image, the min of an all-0.5 neighbourhood is 0.5.

    Test steps:
    1) Apply a min order-statistic filter to UNIFORM_5x5 with filter size 3.
    2) Assert that the center pixel [2, 2] equals 0.5.
    """

    # Steps (1)+(2) - Filter and assert center value.
    result = order_statistic_filter(image=UNIFORM_5x5, filter_type='min',
                                    padding_type='zero', filter_size=3)
    np.testing.assert_almost_equal(result[2, 2], 0.5, decimal=10)


@pytest.mark.parametrize(
    "filter_type",
    ["median", "max", "min"],
)
def test_order_statistic_filter_output_values_in_range(filter_type):
    """
    Test purpose - Order-statistic filtering produces values within the input range.
    Criteria - All pixels of the filtered image are >= 0 and <= 1 when applied to KNOWN_3x3.

    Test steps:
    1) Apply the parametrized order-statistic filter to KNOWN_3x3.
    2) Assert that all pixel values are >= 0.
    3) Assert that all pixel values are <= 1.
    """

    # Step (1) - Filter.
    result = order_statistic_filter(image=KNOWN_3x3, filter_type=filter_type,
                                    padding_type='zero', filter_size=3)

    # Steps (2)+(3) - Assert range.
    assert result.min() >= 0
    assert result.max() <= 1