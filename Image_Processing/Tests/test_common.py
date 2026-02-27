# Imports #
import numpy as np
import pytest

from Image_Processing.Source.Basic.common import (
    convert_to_grayscale, scale_image, image_normalization, contrast_stretching,
    calculate_histogram, pad_image, generate_filter, extract_sub_image, convolution_2d,
)
from constants import *


# ──────────────────────────────────────────────────────────── #
#  convert_to_grayscale tests                                   #
# ──────────────────────────────────────────────────────────── #

def test_convert_to_grayscale_color():
    """
    Test purpose - NTSC-weighted color-to-grayscale conversion.
    Criteria - Each row of a single-column RGB image is converted to the correct luminance value using
    0.2989·R + 0.5870·G + 0.1140·B.

    Test steps:
    1) Pass COLOR_3x1 (one red, one green, one blue pixel) through convert_to_grayscale.
    2) Assert that the result matches GRAY_3x1 to four decimal places.
    """

    # Steps (1)+(2) - Convert and assert.
    result = convert_to_grayscale(image=COLOR_3x1)
    np.testing.assert_array_almost_equal(result, GRAY_3x1, decimal=4)


def test_convert_to_grayscale_passthrough():
    """
    Test purpose - Grayscale image is returned unchanged.
    Criteria - Passing an already-grayscale image to convert_to_grayscale returns the same array.

    Test steps:
    1) Pass KNOWN_3x3 (grayscale) through convert_to_grayscale.
    2) Assert that the returned array is identical to the input.
    """

    # Steps (1)+(2) - Convert and assert identity.
    result = convert_to_grayscale(image=KNOWN_3x3)
    np.testing.assert_array_equal(result, KNOWN_3x3)


# ──────────────────────────────────────────────────────────── #
#  scale_image tests                                            #
# ──────────────────────────────────────────────────────────── #

def test_scale_image_upscale_produces_int_array():
    """
    Test purpose - Scaling by 255 converts image to an integer array.
    Criteria - The resulting array has integer dtype and values equal to (image * 255).astype(int).

    Test steps:
    1) Scale KNOWN_3x3 upward by a factor of 255.
    2) Assert that the dtype is integer.
    3) Assert that the pixel values match the expected integer conversion.
    """

    # Step (1) - Scale the image.
    result = scale_image(image=KNOWN_3x3, scale_factor=255)
    expected = (KNOWN_3x3 * 255).astype(int)

    # Steps (2)+(3) - Check dtype and values.
    assert np.issubdtype(result.dtype, np.integer)
    np.testing.assert_array_equal(result, expected)


def test_scale_image_round_trip():
    """
    Test purpose - Scaling up then down recovers the original image.
    Criteria - Scaling by 2 then by 0.5 returns the original pixel values.

    Test steps:
    1) Scale KNOWN_3x3 by factor 2.
    2) Scale the result by factor 0.5.
    3) Assert that the final values match KNOWN_3x3.
    """

    # Steps (1)+(2) - Scale up then down.
    scaled_up = scale_image(image=KNOWN_3x3, scale_factor=2)
    result = scale_image(image=scaled_up, scale_factor=0.5)

    # Step (3) - Assert round-trip accuracy.
    np.testing.assert_array_almost_equal(result, KNOWN_3x3, decimal=10)


# ──────────────────────────────────────────────────────────── #
#  image_normalization tests                                    #
# ──────────────────────────────────────────────────────────── #

def test_image_normalization_unchanged():
    """
    Test purpose - The 'unchanged' method returns the image as-is.
    Criteria - Out-of-range values are preserved without modification.

    Test steps:
    1) Create an image containing values outside [0, 1].
    2) Normalize with method 'unchanged'.
    3) Assert that the values are identical to the original.
    """

    # Step (1) - Image with out-of-range values.
    image_with_outliers = np.array([[-0.5, 0.5], [1.5, 0.3]])

    # Steps (2)+(3) - Normalize and assert identity.
    result = image_normalization(image=image_with_outliers.copy(), normalization_method='unchanged')
    np.testing.assert_array_equal(result, image_with_outliers)


def test_image_normalization_cutoff_clips_values():
    """
    Test purpose - The 'cutoff' method clips values to [0, 1].
    Criteria - Values below 0 become 0 and values above 1 become 1; in-range values are unchanged.

    Test steps:
    1) Create an image with one value below 0 and one above 1.
    2) Normalize with method 'cutoff'.
    3) Assert that all values fall within [0, 1].
    4) Assert that in-range values are unchanged.
    """

    # Step (1) - Image with outliers.
    image_with_outliers = np.array([[-0.5, 0.5], [1.5, 0.3]])

    # Step (2) - Normalize.
    result = image_normalization(image=image_with_outliers.copy(), normalization_method='cutoff')

    # Steps (3)+(4) - Assert range and preservation of in-range values.
    assert result.min() >= 0
    assert result.max() <= 1
    assert result[0, 1] == 0.5
    assert result[1, 1] == 0.3


def test_image_normalization_stretch_fills_range():
    """
    Test purpose - The 'stretch' method maps the image to [0, 1].
    Criteria - The minimum pixel value becomes exactly 0 and the maximum becomes exactly 1.

    Test steps:
    1) Normalize KNOWN_3x3 (min=0.1, max=0.9) with method 'stretch'.
    2) Assert that the minimum of the result is 0.
    3) Assert that the maximum of the result is 1.
    """

    # Step (1) - Normalize.
    result = image_normalization(image=KNOWN_3x3.copy(), normalization_method='stretch')

    # Steps (2)+(3) - Assert min and max.
    np.testing.assert_almost_equal(result.min(), 0.0, decimal=10)
    np.testing.assert_almost_equal(result.max(), 1.0, decimal=10)


# ──────────────────────────────────────────────────────────── #
#  contrast_stretching tests                                    #
# ──────────────────────────────────────────────────────────── #

def test_contrast_stretching_maps_to_unit_range():
    """
    Test purpose - Contrast stretching linearly maps pixel values to [0, 1].
    Criteria - The minimum of the stretched image is 0 and the maximum is 1.

    Test steps:
    1) Apply contrast stretching to KNOWN_3x3 (min=0.1, max=0.9).
    2) Assert that the minimum of the result is 0.
    3) Assert that the maximum of the result is 1.
    """

    # Step (1) - Stretch.
    result = contrast_stretching(image=KNOWN_3x3.copy())

    # Steps (2)+(3) - Assert range.
    np.testing.assert_almost_equal(result.min(), 0.0, decimal=10)
    np.testing.assert_almost_equal(result.max(), 1.0, decimal=10)


def test_contrast_stretching_preserves_ordering():
    """
    Test purpose - Contrast stretching is a monotone transformation.
    Criteria - The relative ordering of pixel values is preserved after stretching.

    Test steps:
    1) Apply contrast stretching to KNOWN_3x3.
    2) Assert that pixels originally larger remain larger after stretching.
    """

    # Steps (1)+(2) - Stretch and assert ordering.
    result = contrast_stretching(image=KNOWN_3x3.copy())
    assert result[0, 2] > result[0, 1]  # 0.9 > 0.5 in original → should stay larger.
    assert result[1, 1] > result[0, 0]  # 0.7 > 0.1 in original → should stay larger.


# ──────────────────────────────────────────────────────────── #
#  calculate_histogram tests                                    #
# ──────────────────────────────────────────────────────────── #

def test_calculate_histogram_pixel_count():
    """
    Test purpose - Histogram counts the number of pixels per intensity level.
    Criteria - All 25 pixels of UNIFORM_5x5 map to bin 127 (int(0.5 * 255) = 127).

    Test steps:
    1) Calculate the (non-normalized) histogram of UNIFORM_5x5.
    2) Assert that bin 127 contains exactly 25 counts and all other bins are zero.
    """

    # Step (1) - Calculate histogram.
    histogram = calculate_histogram(image=UNIFORM_5x5, normalize=False)

    # Step (2) - Assert bin counts.
    assert histogram[127] == 25
    assert np.sum(histogram) == 25  # All pixels accounted for in a single bin.


def test_calculate_histogram_normalized_sums_to_one():
    """
    Test purpose - A normalized histogram sums to 1.
    Criteria - When all pixels share the same intensity, the normalized histogram has a single
    bin equal to 1.0 and the total sum equals 1.0.

    Test steps:
    1) Calculate the normalized histogram of UNIFORM_5x5.
    2) Assert that bin 127 equals 1.0.
    3) Assert that the total sum of the histogram equals 1.0.
    """

    # Step (1) - Calculate normalized histogram.
    histogram = calculate_histogram(image=UNIFORM_5x5, normalize=True)

    # Steps (2)+(3) - Assert values.
    np.testing.assert_almost_equal(histogram[127], 1.0, decimal=5)
    np.testing.assert_almost_equal(np.sum(histogram), 1.0, decimal=5)


# ──────────────────────────────────────────────────────────── #
#  pad_image tests                                              #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize("padding_type", ["zero", "mirror", "wrap"])
def test_pad_image_output_dimensions(padding_type):
    """
    Test purpose - Every padding type increases image dimensions by 2 * padding_size on each axis.
    Criteria - A 3×3 image padded with size 1 produces a 5×5 output regardless of padding type.

    Test steps:
    1) Pad KNOWN_3x3 with the given padding type and size 1.
    2) Assert that the padded image has shape (5, 5).
    """

    # Steps (1)+(2) - Pad and assert shape.
    result = pad_image(image=KNOWN_3x3, padding_type=padding_type, padding_size=1)
    assert result.shape == (5, 5)


@pytest.mark.parametrize("padding_type", ["zero", "mirror", "wrap"])
def test_pad_image_interior_preserved(padding_type):
    """
    Test purpose - Every padding type leaves the original image data in the interior of the result.
    Criteria - The 3×3 interior block of a size-1 padded 5×5 result equals KNOWN_3x3.

    Test steps:
    1) Pad KNOWN_3x3 with the given padding type and size 1.
    2) Assert that result[1:4, 1:4] matches KNOWN_3x3 exactly.
    """

    # Steps (1)+(2) - Pad and assert interior.
    result = pad_image(image=KNOWN_3x3, padding_type=padding_type, padding_size=1)
    np.testing.assert_array_equal(result[1:4, 1:4], KNOWN_3x3)


def test_pad_image_zero_border_is_zeros():
    """
    Test purpose - Zero-padding fills the entire border with zeros.
    Criteria - The top and bottom border rows of a size-1 padded image are all zero.

    Test steps:
    1) Pad KNOWN_3x3 with zero padding of size 1.
    2) Assert that the top row is all zeros.
    3) Assert that the bottom row is all zeros.
    """

    # Step (1) - Pad.
    result = pad_image(image=KNOWN_3x3, padding_type='zero', padding_size=1)

    # Steps (2)+(3) - Assert border zeros.
    np.testing.assert_array_equal(result[0, :], np.zeros(5))
    np.testing.assert_array_equal(result[-1, :], np.zeros(5))


def test_pad_image_mirror_top_row_reflects_second_row():
    """
    Test purpose - Mirror padding reflects pixel values without repeating the edge pixel.
    Criteria - For a 3×3 image with size-1 mirror padding, the top border row's interior columns
    equal the second row of the original image, because 'reflect' skips the edge pixel.

    Reflection rule: for a 1D slice [a, b, c] the result is [b, a, b, c, b] (edge pixel 'a' is
    the axis of reflection and is not duplicated into the border).

    Test steps:
    1) Pad KNOWN_3x3 with mirror padding of size 1.
    2) Assert that result[0, 1:4] equals KNOWN_3x3[1, :] (top border interior = original row 1).
    3) Assert that result[1:4, 0] equals KNOWN_3x3[:, 1] (left border interior = original col 1).
    """

    # Step (1) - Pad.
    result = pad_image(image=KNOWN_3x3, padding_type='mirror', padding_size=1)

    # Step (2) - Top border interior reflects row 1 of the original.
    np.testing.assert_array_equal(result[0, 1:4], KNOWN_3x3[1, :])

    # Step (3) - Left border interior reflects col 1 of the original.
    np.testing.assert_array_equal(result[1:4, 0], KNOWN_3x3[:, 1])


def test_pad_image_mirror_preserves_no_artificial_zeros():
    """
    Test purpose - Mirror padding never introduces zeros that are not present in the original image.
    Criteria - For an image with no zero-valued pixels, a mirror-padded result also contains no zeros.

    Test steps:
    1) Create a 3×3 image with all positive values (min value > 0).
    2) Pad with mirror padding of size 1.
    3) Assert that the padded result contains no zeros.
    """

    # Step (1) - All-positive image.
    positive_image = np.full((3, 3), 0.5)

    # Step (2) - Pad.
    result = pad_image(image=positive_image, padding_type='mirror', padding_size=1)

    # Step (3) - No zeros in the result.
    assert np.all(result > 0)


def test_pad_image_wrap_top_row_equals_last_row():
    """
    Test purpose - Wrap padding tiles the image periodically so opposite edges connect.
    Criteria - The top border row's interior columns equal the last row of the original image,
    and the left border column's interior rows equal the last column.

    Wrap rule: for a 1D slice [a, b, c] the result is [c, a, b, c, a] (right end wraps to left).

    Test steps:
    1) Pad KNOWN_3x3 with wrap padding of size 1.
    2) Assert that result[0, 1:4] equals KNOWN_3x3[-1, :] (top border interior = original last row).
    3) Assert that result[1:4, 0] equals KNOWN_3x3[:, -1] (left border interior = original last col).
    """

    # Step (1) - Pad.
    result = pad_image(image=KNOWN_3x3, padding_type='wrap', padding_size=1)

    # Step (2) - Top border interior = last row of original.
    np.testing.assert_array_equal(result[0, 1:4], KNOWN_3x3[-1, :])

    # Step (3) - Left border interior = last column of original.
    np.testing.assert_array_equal(result[1:4, 0], KNOWN_3x3[:, -1])


def test_pad_image_wrap_bottom_row_equals_first_row():
    """
    Test purpose - Wrap padding also connects the bottom edge back to the top of the image.
    Criteria - The bottom border row's interior columns equal the first row of the original image.

    Test steps:
    1) Pad KNOWN_3x3 with wrap padding of size 1.
    2) Assert that result[-1, 1:4] equals KNOWN_3x3[0, :] (bottom border interior = original first row).
    """

    # Steps (1)+(2) - Pad and assert.
    result = pad_image(image=KNOWN_3x3, padding_type='wrap', padding_size=1)
    np.testing.assert_array_equal(result[-1, 1:4], KNOWN_3x3[0, :])


def test_pad_image_color_image_channel_axis_unchanged():
    """
    Test purpose - Padding does not alter the channel dimension of a color image.
    Criteria - A (3, 3, 3) color image padded with size 1 produces a (5, 5, 3) result; the
    channel count stays the same for zero, mirror, and wrap padding.

    Test steps:
    1) Create a 3×3 RGB image (shape 3×3×3).
    2) Pad with each padding type and size 1.
    3) Assert that the output shape is (5, 5, 3) in all three cases.
    """

    # Step (1) - 3×3 RGB image.
    color_image = np.random.rand(3, 3, 3)

    # Steps (2)+(3) - Pad and assert shape for each type.
    for padding_type in ("zero", "mirror", "wrap"):
        result = pad_image(image=color_image, padding_type=padding_type, padding_size=1)
        assert result.shape == (5, 5, 3), f"Wrong shape for padding_type='{padding_type}'"


# ──────────────────────────────────────────────────────────── #
#  generate_filter tests                                        #
# ──────────────────────────────────────────────────────────── #

def test_generate_filter_box_sums_to_one():
    """
    Test purpose - A box filter is a normalized all-ones kernel.
    Criteria - The sum of all elements in a 3×3 box filter equals 1.0.

    Test steps:
    1) Generate a 3×3 box filter.
    2) Assert that the sum of all elements equals 1.0.
    """

    # Steps (1)+(2) - Generate and assert sum.
    kernel = generate_filter(filter_type='box', filter_size=3)
    np.testing.assert_almost_equal(np.sum(kernel), 1.0, decimal=10)


def test_generate_filter_box_uniform_weights():
    """
    Test purpose - All coefficients of a box filter are equal.
    Criteria - Every element of a 3×3 box filter equals 1/9.

    Test steps:
    1) Generate a 3×3 box filter.
    2) Assert that every element equals 1/9.
    """

    # Steps (1)+(2) - Generate and assert uniformity.
    kernel = generate_filter(filter_type='box', filter_size=3)
    np.testing.assert_array_almost_equal(kernel, np.full((3, 3), 1 / 9), decimal=10)


def test_generate_filter_gaussian_sums_to_one():
    """
    Test purpose - A Gaussian filter is normalized so its coefficients sum to 1.
    Criteria - The sum of all elements in a 3×3 Gaussian filter (σ=1) equals 1.0.

    Test steps:
    1) Generate a 3×3 Gaussian filter with sigma=1.
    2) Assert that the sum of all elements equals 1.0.
    """

    # Steps (1)+(2) - Generate and assert sum.
    kernel = generate_filter(filter_type='gaussian', filter_size=3, sigma=1.0)
    np.testing.assert_almost_equal(np.sum(kernel), 1.0, decimal=10)


def test_generate_filter_gaussian_center_is_maximum():
    """
    Test purpose - A Gaussian filter has its maximum coefficient at the center.
    Criteria - The center element of a 3×3 Gaussian filter is strictly larger than all other elements.

    Test steps:
    1) Generate a 3×3 Gaussian filter with sigma=1.
    2) Assert that the center element is the maximum.
    """

    # Steps (1)+(2) - Generate and assert center dominance.
    kernel = generate_filter(filter_type='gaussian', filter_size=3, sigma=1.0)
    assert kernel[1, 1] == np.max(kernel)


# ──────────────────────────────────────────────────────────── #
#  extract_sub_image tests                                      #
# ──────────────────────────────────────────────────────────── #

def test_extract_sub_image_center_of_uniform():
    """
    Test purpose - Sub-image extraction returns the correct neighbourhood.
    Criteria - Extracting a 3×3 patch from the center of UNIFORM_5x5 returns an all-0.5 array.

    Test steps:
    1) Extract a 3×3 sub-image centered at position (2, 2) of UNIFORM_5x5.
    2) Assert that the result has shape (3, 3) and all elements equal 0.5.
    """

    # Steps (1)+(2) - Extract and assert.
    result = extract_sub_image(image=UNIFORM_5x5, position=(2, 2), sub_image_size=3)
    assert result.shape == (3, 3)
    np.testing.assert_array_equal(result, np.full((3, 3), 0.5))


def test_extract_sub_image_center_recovers_original():
    """
    Test purpose - Sub-image extraction centered at the origin of an embedded image recovers it.
    Criteria - Extracting a 3×3 patch centered at (2, 2) of a zero-padded 5×5 version of
    KNOWN_3x3 returns the original 3×3 image unchanged.

    Test steps:
    1) Pad KNOWN_3x3 with size-1 zero padding to create a 5×5 image.
    2) Extract a 3×3 sub-image centered at (2, 2) of the padded image.
    3) Assert that the result equals KNOWN_3x3.
    """

    # Steps (1)+(2)+(3) - Pad, extract, and assert.
    padded = pad_image(image=KNOWN_3x3, padding_type='zero', padding_size=1)
    result = extract_sub_image(image=padded, position=(2, 2), sub_image_size=3)
    np.testing.assert_array_equal(result, KNOWN_3x3)


# ──────────────────────────────────────────────────────────── #
#  convolution_2d tests                                         #
# ──────────────────────────────────────────────────────────── #

def test_convolution_2d_delta_kernel_is_identity():
    """
    Test purpose - Convolution with a delta (identity) kernel returns the original image.
    Criteria - Convolving any image with a 3×3 kernel that has 1 at the center and 0 elsewhere
    reproduces the original image exactly.

    Test steps:
    1) Construct a 3×3 delta kernel.
    2) Convolve KNOWN_3x3 with the delta kernel (zero padding, unchanged normalization).
    3) Assert that the result equals KNOWN_3x3.
    """

    # Step (1) - Delta kernel.
    delta_kernel = np.array([[0, 0, 0],
                             [0, 1, 0],
                             [0, 0, 0]], dtype=float)

    # Steps (2)+(3) - Convolve and assert.
    result = convolution_2d(image=KNOWN_3x3, kernel=delta_kernel, padding_type='zero',
                            normalization_method='unchanged')
    np.testing.assert_array_almost_equal(result, KNOWN_3x3, decimal=10)


def test_convolution_2d_output_shape_matches_input():
    """
    Test purpose - Convolution preserves the spatial dimensions of the input.
    Criteria - The output of convolution_2d has the same shape as the input image.

    Test steps:
    1) Convolve KNOWN_3x3 with a 3×3 box kernel.
    2) Assert that the output shape equals the input shape.
    """

    # Steps (1)+(2) - Convolve and assert shape.
    kernel = generate_filter(filter_type='box', filter_size=3)
    result = convolution_2d(image=KNOWN_3x3, kernel=kernel, padding_type='zero',
                            normalization_method='unchanged')
    assert result.shape == KNOWN_3x3.shape