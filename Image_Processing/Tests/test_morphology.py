# Imports #
import numpy as np

from Image_Processing.Source.Advanced.morphology import (
    erosion, dilation, opening, closing, boundary_extraction, reflect_structuring_element,
    local_erosion, local_dilation,
)
from constants import *


# ──────────────────────────────────────────────────────────── #
#  reflect_structuring_element tests                            #
# ──────────────────────────────────────────────────────────── #

def test_reflect_structuring_element_symmetric():
    """
    Test purpose - Reflecting a symmetric structuring element yields the same element.
    Criteria - Reflecting SE_3x3 (all ones) returns an all-ones matrix.

    Test steps:
    1) Reflect SE_3x3.
    2) Assert that the reflected element equals SE_3x3.
    """

    # Steps (1)+(2) - Reflect and assert.
    result = reflect_structuring_element(structuring_element=SE_3x3)
    np.testing.assert_array_equal(result, SE_3x3)


def test_reflect_structuring_element_asymmetric():
    """
    Test purpose - Reflecting an asymmetric structuring element produces the 180° rotation.
    Criteria - SE_ASYMMETRIC ([[1,0,0],[0,1,0],[0,0,0]]) reflected equals [[0,0,0],[0,1,0],[0,0,1]].

    Test steps:
    1) Reflect SE_ASYMMETRIC.
    2) Assert that the result equals the expected 180°-rotated element.
    """

    # Step (1) - Reflect.
    result = reflect_structuring_element(structuring_element=SE_ASYMMETRIC)

    # Step (2) - Assert.
    expected = np.array([
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ], dtype=float)
    np.testing.assert_array_equal(result, expected)


# ──────────────────────────────────────────────────────────── #
#  local_erosion and local_dilation tests                       #
# ──────────────────────────────────────────────────────────── #

def test_local_erosion_full_match():
    """
    Test purpose - local_erosion returns 1 when every SE foreground pixel matches the sub-image.
    Criteria - A 3×3 all-ones sub-image with a 3×3 all-ones SE has no mismatch → result is 1.

    Test steps:
    1) Call local_erosion with an all-ones sub-image and SE_3x3.
    2) Assert that the result is 1.
    """

    # Steps (1)+(2) - Erode and assert.
    result = local_erosion(sub_image=np.ones((3, 3)), structuring_element=SE_3x3)
    assert result == 1


def test_local_erosion_partial_mismatch():
    """
    Test purpose - local_erosion returns 0 when any SE foreground pixel mismatches the sub-image.
    Criteria - A sub-image that is all zeros cannot satisfy the all-ones SE → result is 0.

    Test steps:
    1) Call local_erosion with an all-zeros sub-image and SE_3x3.
    2) Assert that the result is 0.
    """

    # Steps (1)+(2) - Erode and assert.
    result = local_erosion(sub_image=np.zeros((3, 3)), structuring_element=SE_3x3)
    assert result == 0


def test_local_dilation_no_match():
    """
    Test purpose - local_dilation returns 0 when there is no overlap between the SE and the sub-image.
    Criteria - An all-zeros sub-image with any SE produces no match → result is 0.

    Test steps:
    1) Call local_dilation with an all-zeros sub-image and SE_3x3.
    2) Assert that the result is 0.
    """

    # Steps (1)+(2) - Dilate and assert.
    result = local_dilation(sub_image=np.zeros((3, 3)), structuring_element=SE_3x3)
    assert result == 0


def test_local_dilation_single_match():
    """
    Test purpose - local_dilation returns 1 when at least one SE foreground pixel matches.
    Criteria - A sub-image with a single center foreground pixel is sufficient for dilation.

    Test steps:
    1) Create a 3×3 sub-image with a single 1 at the center.
    2) Call local_dilation with this sub-image and SE_3x3.
    3) Assert that the result is 1.
    """

    # Step (1) - Sub-image with single center pixel.
    sub_image = np.zeros((3, 3))
    sub_image[1, 1] = 1

    # Steps (2)+(3) - Dilate and assert.
    result = local_dilation(sub_image=sub_image, structuring_element=SE_3x3)
    assert result == 1


# ──────────────────────────────────────────────────────────── #
#  erosion tests                                                #
# ──────────────────────────────────────────────────────────── #

def test_erosion_ones_with_3x3_se_yields_center_block():
    """
    Test purpose - Eroding an all-ones image leaves only the pixels whose full 3×3 neighbourhood
    lies within the image (zero-padded boundary reduces the surviving region).
    Criteria - Eroding BINARY_ONES_5x5 with SE_3x3 produces BINARY_SQUARE_5x5 (3×3 center block).

    Test steps:
    1) Erode BINARY_ONES_5x5 with SE_3x3 using zero padding.
    2) Assert that the result equals BINARY_SQUARE_5x5.
    """

    # Steps (1)+(2) - Erode and assert.
    result = erosion(image=BINARY_ONES_5x5, structuring_element=SE_3x3, padding_type='zero')
    np.testing.assert_array_equal(result, BINARY_SQUARE_5x5)


def test_erosion_zeros_yields_zeros():
    """
    Test purpose - Eroding an all-zeros image always yields all zeros.
    Criteria - erosion(BINARY_ZEROS_5x5) == BINARY_ZEROS_5x5.

    Test steps:
    1) Erode BINARY_ZEROS_5x5 with SE_3x3.
    2) Assert that the result equals BINARY_ZEROS_5x5.
    """

    # Steps (1)+(2) - Erode and assert.
    result = erosion(image=BINARY_ZEROS_5x5, structuring_element=SE_3x3, padding_type='zero')
    np.testing.assert_array_equal(result, BINARY_ZEROS_5x5)


def test_erosion_square_with_3x3_se_yields_center_pixel():
    """
    Test purpose - Eroding a 3×3 filled square with a 3×3 SE leaves only the center pixel.
    Criteria - erosion(BINARY_SQUARE_5x5, SE_3x3) == BINARY_SINGLE_PIXEL_5x5.

    Test steps:
    1) Erode BINARY_SQUARE_5x5 with SE_3x3 using zero padding.
    2) Assert that the result equals BINARY_SINGLE_PIXEL_5x5.
    """

    # Steps (1)+(2) - Erode and assert.
    result = erosion(image=BINARY_SQUARE_5x5, structuring_element=SE_3x3, padding_type='zero')
    np.testing.assert_array_equal(result, BINARY_SINGLE_PIXEL_5x5)


# ──────────────────────────────────────────────────────────── #
#  dilation tests                                               #
# ──────────────────────────────────────────────────────────── #

def test_dilation_single_pixel_with_3x3_se_yields_square():
    """
    Test purpose - Dilating a single foreground pixel with a 3×3 all-ones SE fills a 3×3 region.
    Criteria - dilation(BINARY_SINGLE_PIXEL_5x5, SE_3x3) == BINARY_SQUARE_5x5.

    Test steps:
    1) Dilate BINARY_SINGLE_PIXEL_5x5 with SE_3x3 using zero padding.
    2) Assert that the result equals BINARY_SQUARE_5x5.
    """

    # Steps (1)+(2) - Dilate and assert.
    result = dilation(image=BINARY_SINGLE_PIXEL_5x5, structuring_element=SE_3x3, padding_type='zero')
    np.testing.assert_array_equal(result, BINARY_SQUARE_5x5)


def test_dilation_zeros_yields_zeros():
    """
    Test purpose - Dilating an all-zeros image always yields all zeros.
    Criteria - dilation(BINARY_ZEROS_5x5) == BINARY_ZEROS_5x5.

    Test steps:
    1) Dilate BINARY_ZEROS_5x5 with SE_3x3.
    2) Assert that the result equals BINARY_ZEROS_5x5.
    """

    # Steps (1)+(2) - Dilate and assert.
    result = dilation(image=BINARY_ZEROS_5x5, structuring_element=SE_3x3, padding_type='zero')
    np.testing.assert_array_equal(result, BINARY_ZEROS_5x5)


# ──────────────────────────────────────────────────────────── #
#  opening tests                                                #
# ──────────────────────────────────────────────────────────── #

def test_opening_single_pixel_removed():
    """
    Test purpose - Opening removes isolated foreground pixels smaller than the SE.
    Criteria - A single pixel cannot survive erosion by a 3×3 SE, so opening it yields all zeros.

    Test steps:
    1) Apply opening to BINARY_SINGLE_PIXEL_5x5 with SE_3x3.
    2) Assert that the result equals BINARY_ZEROS_5x5.
    """

    # Steps (1)+(2) - Open and assert.
    result = opening(image=BINARY_SINGLE_PIXEL_5x5, structuring_element=SE_3x3, padding_type='zero')
    np.testing.assert_array_equal(result, BINARY_ZEROS_5x5)


def test_opening_large_rectangle_preserved():
    """
    Test purpose - Opening preserves large objects that are bigger than the SE.
    Criteria - The 5×5 foreground block in BINARY_RECT_7x7 is large enough to survive erosion
    and be fully recovered by dilation, so the result equals BINARY_RECT_7x7.

    Test steps:
    1) Apply opening to BINARY_RECT_7x7 with SE_3x3.
    2) Assert that the result equals BINARY_RECT_7x7.
    """

    # Steps (1)+(2) - Open and assert.
    result = opening(image=BINARY_RECT_7x7, structuring_element=SE_3x3, padding_type='zero')
    np.testing.assert_array_equal(result, BINARY_RECT_7x7)


# ──────────────────────────────────────────────────────────── #
#  closing tests                                                #
# ──────────────────────────────────────────────────────────── #

def test_closing_idempotent_on_rect():
    """
    Test purpose - Closing is an idempotent operation.
    Criteria - Applying closing once to BINARY_RECT_7x7 returns BINARY_RECT_7x7, demonstrating
    that the image is already closed with respect to SE_3x3.

    Test steps:
    1) Apply closing to BINARY_RECT_7x7 with SE_3x3.
    2) Assert that the result equals BINARY_RECT_7x7.
    """

    # Steps (1)+(2) - Close and assert idempotency.
    result = closing(image=BINARY_RECT_7x7, structuring_element=SE_3x3, padding_type='zero')
    np.testing.assert_array_equal(result, BINARY_RECT_7x7)


def test_closing_zeros_yields_zeros():
    """
    Test purpose - Closing an all-zeros image always yields all zeros.
    Criteria - closing(BINARY_ZEROS_5x5) == BINARY_ZEROS_5x5.

    Test steps:
    1) Apply closing to BINARY_ZEROS_5x5 with SE_3x3.
    2) Assert that the result equals BINARY_ZEROS_5x5.
    """

    # Steps (1)+(2) - Close and assert.
    result = closing(image=BINARY_ZEROS_5x5, structuring_element=SE_3x3, padding_type='zero')
    np.testing.assert_array_equal(result, BINARY_ZEROS_5x5)


# ──────────────────────────────────────────────────────────── #
#  boundary_extraction tests                                    #
# ──────────────────────────────────────────────────────────── #

def test_boundary_extraction_square_outer_ring():
    """
    Test purpose - Boundary extraction retains only the outer-ring pixels of a foreground region.
    Criteria - boundary_extraction(BINARY_SQUARE_5x5) returns the 8 border pixels of the 3×3
    block, with the center pixel removed.

    Test steps:
    1) Apply boundary extraction to BINARY_SQUARE_5x5 with SE_3x3.
    2) Assert that the result matches the expected outer-ring binary image.
    """

    # Step (1) - Extract boundary.
    result = boundary_extraction(image=BINARY_SQUARE_5x5, structuring_element=SE_3x3,
                                 padding_type='zero')

    # Step (2) - Construct expected boundary (3×3 block minus center pixel).
    expected = BINARY_SQUARE_5x5.copy()
    expected[2, 2] = 0  # Center pixel is removed by erosion.
    np.testing.assert_array_equal(result, expected)


def test_boundary_extraction_zeros_yields_zeros():
    """
    Test purpose - Boundary extraction of an all-zeros image yields all zeros.
    Criteria - boundary_extraction(BINARY_ZEROS_5x5) == BINARY_ZEROS_5x5.

    Test steps:
    1) Apply boundary extraction to BINARY_ZEROS_5x5.
    2) Assert that the result equals BINARY_ZEROS_5x5.
    """

    # Steps (1)+(2) - Extract and assert.
    result = boundary_extraction(image=BINARY_ZEROS_5x5, structuring_element=SE_3x3,
                                 padding_type='zero')
    np.testing.assert_array_equal(result, BINARY_ZEROS_5x5)