# Imports #
import numpy as np

from Image_Processing.Source.Advanced.spatial_filtering import (
    blur_image, laplacian_gradient, laplacian_image_sharpening, sobel_filter,
)
from constants import *


# ──────────────────────────────────────────────────────────── #
#  blur_image tests                                             #
# ──────────────────────────────────────────────────────────── #

def test_blur_image_output_shape():
    """
    Test purpose - Blurring preserves the spatial dimensions of the input.
    Criteria - The output of blur_image has the same shape as the input image.

    Test steps:
    1) Apply a 3×3 box blur to KNOWN_3x3.
    2) Assert that the output shape equals the input shape.
    """

    # Steps (1)+(2) - Blur and assert shape.
    result = blur_image(image=KNOWN_3x3, filter_type='box', filter_size=3,
                        padding_type='zero', sigma=1.0, normalization_method='unchanged')
    assert result.shape == KNOWN_3x3.shape


def test_blur_image_uniform_center_pixel_unchanged():
    """
    Test purpose - Blurring a uniform image leaves interior pixels unchanged.
    Criteria - The center pixel of UNIFORM_5x5 after box blurring equals 0.5 (average of 0.5 values).

    Test steps:
    1) Apply a 3×3 box blur to UNIFORM_5x5 with unchanged normalization.
    2) Assert that the center pixel [2, 2] equals 0.5.
    """

    # Steps (1)+(2) - Blur and assert center value.
    result = blur_image(image=UNIFORM_5x5, filter_type='box', filter_size=3,
                        padding_type='zero', sigma=1.0, normalization_method='unchanged')
    np.testing.assert_almost_equal(result[2, 2], 0.5, decimal=10)


def test_blur_image_reduces_contrast():
    """
    Test purpose - Blurring reduces the range of pixel values.
    Criteria - The standard deviation of a blurred image is less than or equal to that of the
    original image (blurring smooths out variations).

    Test steps:
    1) Apply a 3×3 box blur to KNOWN_3x3 with unchanged normalization.
    2) Assert that the standard deviation of the result is less than that of KNOWN_3x3.
    """

    # Steps (1)+(2) - Blur and compare standard deviations.
    result = blur_image(image=KNOWN_3x3, filter_type='box', filter_size=3,
                        padding_type='zero', sigma=1.0, normalization_method='unchanged')
    assert np.std(result) <= np.std(KNOWN_3x3)


def test_blur_image_gaussian_sums_preserved_at_center():
    """
    Test purpose - A Gaussian blur of a uniform image also preserves the center value.
    Criteria - The center pixel of UNIFORM_5x5 after Gaussian blurring equals 0.5.

    Test steps:
    1) Apply a 3×3 Gaussian blur (σ=1) to UNIFORM_5x5.
    2) Assert that the center pixel [2, 2] equals 0.5.
    """

    # Steps (1)+(2) - Blur and assert center value.
    result = blur_image(image=UNIFORM_5x5, filter_type='gaussian', filter_size=3,
                        padding_type='zero', sigma=1.0, normalization_method='unchanged')
    np.testing.assert_almost_equal(result[2, 2], 0.5, decimal=10)


# ──────────────────────────────────────────────────────────── #
#  laplacian_gradient tests                                     #
# ──────────────────────────────────────────────────────────── #

def test_laplacian_gradient_output_shape():
    """
    Test purpose - The Laplacian gradient preserves image dimensions.
    Criteria - The output of laplacian_gradient has the same shape as the input.

    Test steps:
    1) Apply the Laplacian gradient to KNOWN_3x3.
    2) Assert that the output shape equals the input shape.
    """

    # Steps (1)+(2) - Apply Laplacian and assert shape.
    result = laplacian_gradient(image=KNOWN_3x3, padding_type='zero',
                                include_diagonal_terms=False, normalization_method='unchanged')
    assert result.shape == KNOWN_3x3.shape


def test_laplacian_gradient_interior_pixel_zero_for_uniform():
    """
    Test purpose - The Laplacian of a constant image is zero at interior pixels.
    Criteria - The second derivative of a flat intensity field equals zero at positions
    where no zero-padding boundary effect occurs.

    Test steps:
    1) Apply the Laplacian gradient to UNIFORM_5x5 with unchanged normalization.
    2) Assert that the center pixel [2, 2] equals exactly 0.0.
    """

    # Steps (1)+(2) - Apply and assert center value.
    result = laplacian_gradient(image=UNIFORM_5x5, padding_type='zero',
                                include_diagonal_terms=False, normalization_method='unchanged')
    np.testing.assert_almost_equal(result[2, 2], 0.0, decimal=10)


def test_laplacian_gradient_diagonal_vs_no_diagonal():
    """
    Test purpose - Including diagonal terms changes the Laplacian response.
    Criteria - The Laplacian with and without diagonal terms produces different results on a
    non-uniform image.

    Test steps:
    1) Apply the Laplacian gradient to KNOWN_3x3 without diagonal terms.
    2) Apply the Laplacian gradient to KNOWN_3x3 with diagonal terms.
    3) Assert that the two results are not identical.
    """

    # Steps (1)+(2) - Apply both versions.
    result_no_diag = laplacian_gradient(image=KNOWN_3x3, padding_type='zero',
                                        include_diagonal_terms=False, normalization_method='unchanged')
    result_with_diag = laplacian_gradient(image=KNOWN_3x3, padding_type='zero',
                                          include_diagonal_terms=True, normalization_method='unchanged')

    # Step (3) - Assert results differ.
    assert not np.allclose(result_no_diag, result_with_diag)


# ──────────────────────────────────────────────────────────── #
#  laplacian_image_sharpening tests                             #
# ──────────────────────────────────────────────────────────── #

def test_laplacian_sharpening_output_shape():
    """
    Test purpose - Laplacian image sharpening preserves image dimensions.
    Criteria - The output of laplacian_image_sharpening has the same shape as the input.

    Test steps:
    1) Apply Laplacian image sharpening to KNOWN_3x3.
    2) Assert that the output shape equals the input shape.
    """

    # Steps (1)+(2) - Sharpen and assert shape.
    result = laplacian_image_sharpening(image=KNOWN_3x3, padding_type='zero',
                                        include_diagonal_terms=False)
    assert result.shape == KNOWN_3x3.shape


def test_laplacian_sharpening_uniform_image_unchanged():
    """
    Test purpose - Sharpening a uniform image produces no change.
    Criteria - The center pixel of a uniform image is unchanged after Laplacian sharpening
    because the Laplacian of a flat field is zero.

    Test steps:
    1) Apply Laplacian image sharpening to UNIFORM_5x5.
    2) Assert that the center pixel [2, 2] equals 0.5 (original value minus zero Laplacian).
    """

    # Steps (1)+(2) - Sharpen and assert center value.
    result = laplacian_image_sharpening(image=UNIFORM_5x5, padding_type='zero',
                                        include_diagonal_terms=False)
    np.testing.assert_almost_equal(result[2, 2], 0.5, decimal=10)


# ──────────────────────────────────────────────────────────── #
#  sobel_filter tests                                           #
# ──────────────────────────────────────────────────────────── #

def test_sobel_filter_returns_magnitude_and_direction():
    """
    Test purpose - The Sobel filter returns a dictionary with both output images.
    Criteria - The result of sobel_filter contains the keys 'Magnitude' and 'Direction'.

    Test steps:
    1) Apply the Sobel filter to KNOWN_3x3.
    2) Assert that the result contains the key 'Magnitude'.
    3) Assert that the result contains the key 'Direction'.
    """

    # Steps (1)+(2)+(3) - Apply and assert keys.
    result = sobel_filter(image=KNOWN_3x3, padding_type='zero', normalization_method='unchanged')
    assert 'Magnitude' in result
    assert 'Direction' in result


def test_sobel_filter_output_shapes():
    """
    Test purpose - Both Sobel output images have the same shape as the input.
    Criteria - The 'Magnitude' and 'Direction' images match the input dimensions.

    Test steps:
    1) Apply the Sobel filter to KNOWN_3x3.
    2) Assert that the shape of 'Magnitude' equals KNOWN_3x3.shape.
    3) Assert that the shape of 'Direction' equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2)+(3) - Apply and assert shapes.
    result = sobel_filter(image=KNOWN_3x3, padding_type='zero', normalization_method='unchanged')
    assert result['Magnitude'].shape == KNOWN_3x3.shape
    assert result['Direction'].shape == KNOWN_3x3.shape


def test_sobel_filter_uniform_center_zero_magnitude():
    """
    Test purpose - The Sobel magnitude of a uniform image is zero at interior pixels.
    Criteria - There is no gradient in a constant-intensity region; the magnitude at the
    center of UNIFORM_5x5 is 0.

    Test steps:
    1) Apply the Sobel filter to UNIFORM_5x5 with unchanged normalization.
    2) Assert that the center pixel [2, 2] of the 'Magnitude' image equals 0.
    """

    # Steps (1)+(2) - Apply and assert center magnitude.
    result = sobel_filter(image=UNIFORM_5x5, padding_type='zero', normalization_method='unchanged')
    np.testing.assert_almost_equal(result['Magnitude'][2, 2], 0.0, decimal=10)