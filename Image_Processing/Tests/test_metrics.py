"""
Script Name - test_metrics.py

Purpose - Unit tests for Image_Processing/Source/Advanced/metrics.py.
          Covers the three standalone metric functions (mse, psnr, ssim) and the
          ImageComparator convenience class.

Created by Michael Samelsohn, 28/02/26.
"""

# Imports #
import pytest

from metrics import mse, psnr, ssim, ImageComparator
from constants import *


# ──────────────────────────────────────────────────────────── #
#  mse tests                                                    #
# ──────────────────────────────────────────────────────────── #

def test_mse_identical_images_is_zero():
    """
    Test purpose - MSE between a pair of identical images is exactly zero.
    Criteria - mse(a, a) == 0.0 for any image a.

    Test steps:
    1) Call mse with KNOWN_3x3 as both arguments.
    2) Assert the result is 0.0.
    """

    # Steps (1)+(2) - Compute and assert.
    assert mse(image_a=KNOWN_3x3, image_b=KNOWN_3x3) == 0.0


def test_mse_all_zeros_vs_all_ones_is_one():
    """
    Test purpose - MSE between a black and a white image equals the maximum value of 1.
    Criteria - mse(zeros, ones) == 1.0.

    Test steps:
    1) Call mse with a 3×3 all-zeros image and a 3×3 all-ones image.
    2) Assert the result equals 1.0.
    """

    # Steps (1)+(2) - Compute and assert.
    result = mse(image_a=np.zeros((3, 3)), image_b=np.ones((3, 3)))
    assert result == pytest.approx(1.0)


def test_mse_known_value():
    """
    Test purpose - MSE matches a hand-calculated reference value.
    Criteria - mse(zeros, 0.5·ones) == 0.25, since mean((0 − 0.5)²) = 0.25.

    Test steps:
    1) Call mse with BINARY_ZEROS_5x5 and UNIFORM_5x5.
    2) Assert the result equals 0.25.
    """

    # Steps (1)+(2) - Compute and assert.
    result = mse(image_a=BINARY_ZEROS_5x5, image_b=UNIFORM_5x5)
    assert result == pytest.approx(0.25)


def test_mse_is_symmetric():
    """
    Test purpose - MSE is symmetric: swapping the two arguments gives the same result.
    Criteria - mse(a, b) == mse(b, a).

    Test steps:
    1) Compute mse(KNOWN_3x3, complement) where complement = 1 − KNOWN_3x3.
    2) Compute mse(complement, KNOWN_3x3).
    3) Assert both results are equal.
    """

    complement = 1.0 - KNOWN_3x3

    # Steps (1)+(2) - Compute both orderings.
    result_ab = mse(image_a=KNOWN_3x3,   image_b=complement)
    result_ba = mse(image_a=complement, image_b=KNOWN_3x3)

    # Step (3) - Assert symmetry.
    assert result_ab == pytest.approx(result_ba)


def test_mse_shape_mismatch_raises_value_error():
    """
    Test purpose - MSE raises ValueError when the two images differ in shape.
    Criteria - Passing images of shape (3, 3) and (5, 5) must raise ValueError.

    Test steps:
    1) Call mse with KNOWN_3x3 (shape 3×3) and UNIFORM_5x5 (shape 5×5).
    2) Assert that a ValueError is raised.
    """

    # Steps (1)+(2) - Assert the expected exception.
    with pytest.raises(ValueError):
        mse(image_a=KNOWN_3x3, image_b=UNIFORM_5x5)


# ──────────────────────────────────────────────────────────── #
#  psnr tests                                                   #
# ──────────────────────────────────────────────────────────── #

def test_psnr_identical_images_is_inf():
    """
    Test purpose - PSNR between two identical images is infinite.
    Criteria - psnr(a, a) == np.inf for any image a.

    Test steps:
    1) Call psnr with KNOWN_3x3 as both arguments.
    2) Assert the result is np.inf.
    """

    # Steps (1)+(2) - Compute and assert.
    assert psnr(image_a=KNOWN_3x3, image_b=KNOWN_3x3) == np.inf


def test_psnr_known_value():
    """
    Test purpose - PSNR matches a hand-calculated reference value.
    Criteria - With MSE = 0.25 and MAX = 1.0:
                   PSNR = 10 · log₁₀(1.0² / 0.25) = 10 · log₁₀(4) ≈ 6.021 dB.

    Test steps:
    1) Call psnr with BINARY_ZEROS_5x5 and UNIFORM_5x5 (which gives MSE = 0.25).
    2) Assert the result equals 10 · log₁₀(4) within floating-point tolerance.
    """

    expected = 10.0 * np.log10(4.0)  # ≈ 6.0206 dB

    # Steps (1)+(2) - Compute and assert.
    result = psnr(image_a=BINARY_ZEROS_5x5, image_b=UNIFORM_5x5)
    assert result == pytest.approx(expected, rel=1e-5)


def test_psnr_is_symmetric():
    """
    Test purpose - PSNR is symmetric: swapping the two arguments gives the same result.
    Criteria - psnr(a, b) == psnr(b, a).

    Test steps:
    1) Compute psnr(KNOWN_3x3, complement) where complement = 1 − KNOWN_3x3.
    2) Compute psnr(complement, KNOWN_3x3).
    3) Assert both results are equal.
    """

    complement = 1.0 - KNOWN_3x3

    # Steps (1)+(2) - Compute both orderings.
    result_ab = psnr(image_a=KNOWN_3x3,   image_b=complement)
    result_ba = psnr(image_a=complement, image_b=KNOWN_3x3)

    # Step (3) - Assert symmetry.
    assert result_ab == pytest.approx(result_ba)


def test_psnr_decreases_with_greater_distortion():
    """
    Test purpose - PSNR decreases monotonically as distortion grows.
    Criteria - psnr(ref, mild) > psnr(ref, strong) when |mild − ref| < |strong − ref|.

    Test steps:
    1) Set reference = UNIFORM_5x5 (all 0.5).
    2) Create mild distortion by adding 0.1 (→ 0.6) and strong distortion by adding 0.3 (→ 0.8).
    3) Assert that the mild-distortion PSNR exceeds the strong-distortion PSNR.
    """

    ref    = UNIFORM_5x5
    mild   = ref + 0.1   # all 0.6, MSE = 0.01  → PSNR ≈ 20.0 dB
    strong = ref + 0.3   # all 0.8, MSE = 0.09  → PSNR ≈ 10.5 dB

    # Step (3) - Compare.
    assert psnr(image_a=ref, image_b=mild) > psnr(image_a=ref, image_b=strong)


def test_psnr_custom_max_value():
    """
    Test purpose - The max_value parameter is used correctly in the PSNR formula.
    Criteria - With MSE = 0.25 and MAX = 2.0:
                   PSNR = 10 · log₁₀(2.0² / 0.25) = 10 · log₁₀(16) ≈ 12.041 dB.

    Test steps:
    1) Call psnr with BINARY_ZEROS_5x5 and UNIFORM_5x5 and max_value=2.0.
    2) Assert the result equals 10 · log₁₀(16) within floating-point tolerance.
    """

    expected = 10.0 * np.log10(16.0)  # ≈ 12.041 dB

    # Steps (1)+(2) - Compute and assert.
    result = psnr(image_a=BINARY_ZEROS_5x5, image_b=UNIFORM_5x5, max_value=2.0)
    assert result == pytest.approx(expected, rel=1e-5)


def test_psnr_shape_mismatch_raises_value_error():
    """
    Test purpose - PSNR raises ValueError when the two images differ in shape.
    Criteria - Passing images of shape (3, 3) and (5, 5) must raise ValueError.

    Test steps:
    1) Call psnr with KNOWN_3x3 (shape 3×3) and UNIFORM_5x5 (shape 5×5).
    2) Assert that a ValueError is raised.
    """

    # Steps (1)+(2) - Assert the expected exception.
    with pytest.raises(ValueError):
        psnr(image_a=KNOWN_3x3, image_b=UNIFORM_5x5)


# ──────────────────────────────────────────────────────────── #
#  ssim tests                                                   #
# ──────────────────────────────────────────────────────────── #

def test_ssim_identical_images_is_one():
    """
    Test purpose - SSIM between two identical images is 1.0 (perfect similarity).
    Criteria - ssim(a, a) ≈ 1.0 for any image a.

    Test steps:
    1) Call ssim with KNOWN_3x3 as both arguments.
    2) Assert the result is approximately 1.0.
    """

    # Steps (1)+(2) - Compute and assert.
    assert ssim(image_a=KNOWN_3x3, image_b=KNOWN_3x3) == pytest.approx(1.0)


def test_ssim_result_is_in_valid_range():
    """
    Test purpose - SSIM always falls within the theoretical range [-1, 1].
    Criteria - ssim(a, b) ∈ [-1, 1] for any same-shape image pair.

    Test steps:
    1) Compute ssim between KNOWN_3x3 and its complement (1 − KNOWN_3x3).
    2) Assert the result is ≥ -1.
    3) Assert the result is ≤  1.
    """

    result = ssim(image_a=KNOWN_3x3, image_b=1.0 - KNOWN_3x3)

    # Steps (2)+(3) - Assert bounds.
    assert result >= -1.0
    assert result <=  1.0


def test_ssim_is_symmetric():
    """
    Test purpose - SSIM is symmetric: swapping the two arguments gives the same result.
    Criteria - ssim(a, b) == ssim(b, a).

    Test steps:
    1) Compute ssim(KNOWN_3x3, complement) where complement = 1 − KNOWN_3x3.
    2) Compute ssim(complement, KNOWN_3x3).
    3) Assert both results are equal.
    """

    complement = 1.0 - KNOWN_3x3

    # Steps (1)+(2) - Compute both orderings.
    result_ab = ssim(image_a=KNOWN_3x3,   image_b=complement)
    result_ba = ssim(image_a=complement, image_b=KNOWN_3x3)

    # Step (3) - Assert symmetry.
    assert result_ab == pytest.approx(result_ba)


def test_ssim_decreases_with_greater_distortion():
    """
    Test purpose - SSIM decreases monotonically as distortion grows.
    Criteria - ssim(ref, mild) > ssim(ref, strong) when |mild − ref| < |strong − ref|.

    Test steps:
    1) Set reference = UNIFORM_5x5 (all 0.5).
    2) Create mild distortion by adding 0.1 (→ 0.6) and strong distortion by adding 0.3 (→ 0.8).
    3) Assert that the mild-distortion SSIM exceeds the strong-distortion SSIM.
    """

    ref    = UNIFORM_5x5
    mild   = ref + 0.1   # all 0.6
    strong = ref + 0.3   # all 0.8

    # Step (3) - Compare.
    assert ssim(image_a=ref, image_b=mild) > ssim(image_a=ref, image_b=strong)


def test_ssim_custom_sigma_changes_result():
    """
    Test purpose - The sigma parameter controls the Gaussian window width and affects the result.
    Criteria - ssim with sigma=0.5 and sigma=3.0 return different values for a non-trivial pair.

    Test steps:
    1) Compute ssim(RAMP_5x5, 1 − RAMP_5x5) with sigma=0.5.
    2) Compute ssim(RAMP_5x5, 1 − RAMP_5x5) with sigma=3.0.
    3) Assert the two results differ.
    """

    distorted = 1.0 - RAMP_5x5

    # Steps (1)+(2) - Compute with different sigma values.
    result_narrow = ssim(image_a=RAMP_5x5, image_b=distorted, sigma=0.5)
    result_wide   = ssim(image_a=RAMP_5x5, image_b=distorted, sigma=3.0)

    # Step (3) - Assert that sigma affects the result.
    assert result_narrow != pytest.approx(result_wide)


def test_ssim_shape_mismatch_raises_value_error():
    """
    Test purpose - SSIM raises ValueError when the two images differ in shape.
    Criteria - Passing images of shape (3, 3) and (5, 5) must raise ValueError.

    Test steps:
    1) Call ssim with KNOWN_3x3 (shape 3×3) and UNIFORM_5x5 (shape 5×5).
    2) Assert that a ValueError is raised.
    """

    # Steps (1)+(2) - Assert the expected exception.
    with pytest.raises(ValueError):
        ssim(image_a=KNOWN_3x3, image_b=UNIFORM_5x5)


# ──────────────────────────────────────────────────────────── #
#  ImageComparator tests                                        #
# ──────────────────────────────────────────────────────────── #

def test_comparator_metric_values_match_standalone_functions():
    """
    Test purpose - ImageComparator stores values that agree with the standalone metric functions.
    Criteria - comp.mse_value == mse(a, b), comp.psnr_value == psnr(a, b),
               comp.ssim_value == ssim(a, b).

    Test steps:
    1) Construct an ImageComparator from KNOWN_3x3 (original) and its complement (distorted).
    2) Assert mse_value matches the standalone mse() result.
    3) Assert psnr_value matches the standalone psnr() result.
    4) Assert ssim_value matches the standalone ssim() result.
    """

    distorted = 1.0 - KNOWN_3x3
    comp = ImageComparator(original=KNOWN_3x3, distorted=distorted)

    # Steps (2)+(3)+(4) - Compare stored values against their standalone counterparts.
    assert comp.mse_value  == pytest.approx(mse( image_a=KNOWN_3x3, image_b=distorted))
    assert comp.psnr_value == pytest.approx(psnr(image_a=KNOWN_3x3, image_b=distorted))
    assert comp.ssim_value == pytest.approx(ssim(image_a=KNOWN_3x3, image_b=distorted))


def test_comparator_as_dict_contains_all_keys():
    """
    Test purpose - as_dict() exposes all three metrics under the expected string keys.
    Criteria - The returned dict has exactly the keys "MSE", "PSNR", and "SSIM".

    Test steps:
    1) Construct an ImageComparator from KNOWN_3x3 (identical pair).
    2) Call as_dict().
    3) Assert the key set equals {"MSE", "PSNR", "SSIM"}.
    """

    comp = ImageComparator(original=KNOWN_3x3, distorted=KNOWN_3x3)

    # Steps (2)+(3) - Retrieve and check keys.
    assert set(comp.as_dict().keys()) == {"MSE", "PSNR", "SSIM"}


def test_comparator_as_dict_values_match_attributes():
    """
    Test purpose - as_dict() values agree with the corresponding object attributes.
    Criteria - d["MSE"] == comp.mse_value, d["PSNR"] == comp.psnr_value,
               d["SSIM"] == comp.ssim_value.

    Test steps:
    1) Construct an ImageComparator from KNOWN_3x3 and its complement.
    2) Call as_dict() and store the result.
    3) Assert each dict value equals the matching attribute.
    """

    distorted = 1.0 - KNOWN_3x3
    comp = ImageComparator(original=KNOWN_3x3, distorted=distorted)
    d    = comp.as_dict()

    # Step (3) - Assert correspondence.
    assert d["MSE"]  == comp.mse_value
    assert d["PSNR"] == comp.psnr_value
    assert d["SSIM"] == comp.ssim_value


def test_comparator_identical_images():
    """
    Test purpose - ImageComparator on identical images reports perfect scores across all metrics.
    Criteria - mse_value == 0.0, psnr_value == np.inf, ssim_value ≈ 1.0.

    Test steps:
    1) Construct an ImageComparator with KNOWN_3x3 as both original and distorted.
    2) Assert mse_value == 0.0.
    3) Assert psnr_value == np.inf.
    4) Assert ssim_value ≈ 1.0.
    """

    comp = ImageComparator(original=KNOWN_3x3, distorted=KNOWN_3x3)

    # Steps (2)+(3)+(4) - Assert each metric independently.
    assert comp.mse_value  == 0.0
    assert comp.psnr_value == np.inf
    assert comp.ssim_value == pytest.approx(1.0)


def test_comparator_report_is_string():
    """
    Test purpose - report() returns a plain Python string.
    Criteria - isinstance(comp.report(), str) is True.

    Test steps:
    1) Construct an ImageComparator from KNOWN_3x3 and its complement.
    2) Call report() and assert the result is a str instance.
    """

    comp = ImageComparator(original=KNOWN_3x3, distorted=1.0 - KNOWN_3x3)

    # Step (2) - Assert type.
    assert isinstance(comp.report(), str)


def test_comparator_report_contains_metric_labels():
    """
    Test purpose - report() includes a label for each metric.
    Criteria - The report string contains the substrings "MSE", "PSNR", and "SSIM".

    Test steps:
    1) Construct an ImageComparator from KNOWN_3x3 and its complement.
    2) Call report().
    3) Assert "MSE", "PSNR", and "SSIM" all appear in the string.
    """

    report = ImageComparator(original=KNOWN_3x3, distorted=1.0 - KNOWN_3x3).report()

    # Step (3) - Assert label presence.
    assert "MSE"  in report
    assert "PSNR" in report
    assert "SSIM" in report


def test_comparator_report_has_box_border():
    """
    Test purpose - report() wraps the output in a Unicode box-drawing border.
    Criteria - The report string contains the top-left corner "┌" and the bottom-left corner "└".

    Test steps:
    1) Construct an ImageComparator from KNOWN_3x3 and its complement.
    2) Call report().
    3) Assert the string contains "┌" and "└".
    """

    report = ImageComparator(original=KNOWN_3x3, distorted=1.0 - KNOWN_3x3).report()

    # Step (3) - Assert border characters.
    assert "┌" in report
    assert "└" in report


def test_comparator_report_shows_infinity_symbol_for_identical_images():
    """
    Test purpose - report() renders the infinity symbol "∞" when PSNR is infinite.
    Criteria - For identical images (PSNR = np.inf) the report string contains "∞".

    Test steps:
    1) Construct an ImageComparator with KNOWN_3x3 as both original and distorted.
    2) Call report().
    3) Assert the string contains "∞".
    """

    report = ImageComparator(original=KNOWN_3x3, distorted=KNOWN_3x3).report()

    # Step (3) - Assert infinity symbol.
    assert "∞" in report


def test_comparator_repr_contains_class_name_and_metric_labels():
    """
    Test purpose - __repr__ identifies the class and labels all three metrics.
    Criteria - repr(comp) starts with "ImageComparator(" and contains "MSE=", "PSNR=", "SSIM=".

    Test steps:
    1) Construct an ImageComparator from KNOWN_3x3 and its complement.
    2) Call repr().
    3) Assert it starts with "ImageComparator(" and contains the three metric labels.
    """

    comp = ImageComparator(original=KNOWN_3x3, distorted=1.0 - KNOWN_3x3)
    r    = repr(comp)

    # Step (3) - Assert format.
    assert r.startswith("ImageComparator(")
    assert "MSE="  in r
    assert "PSNR=" in r
    assert "SSIM=" in r
