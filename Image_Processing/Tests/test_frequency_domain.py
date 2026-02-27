# Imports #
import numpy as np

from Image_Processing.Source.Advanced.frequency_domain import (
    dft_2d, idft_2d,
    ideal_lowpass_filter, ideal_highpass_filter,
    butterworth_lowpass_filter, butterworth_highpass_filter,
    gaussian_lowpass_filter, gaussian_highpass_filter,
    notch_reject_filter,
    homomorphic_filter,
)
from constants import *


# ──────────────────────────────────────────────────────────────────────────── #
#  dft_2d tests                                                                 #
# ──────────────────────────────────────────────────────────────────────────── #

def test_dft_2d_output_shape():
    """
    Test purpose - The 2-D DFT preserves spatial dimensions.
    Criteria - The output of dft_2d has the same shape as the input.

    Test steps:
    1) Compute the 2-D DFT of KNOWN_3x3.
    2) Assert that the output shape equals (3, 3).
    """

    # Steps (1)+(2) - Transform and assert shape.
    F = dft_2d(image=KNOWN_3x3)
    assert F.shape == KNOWN_3x3.shape


def test_dft_2d_output_is_complex():
    """
    Test purpose - The DFT output is complex-valued.
    Criteria - The dtype of the dft_2d output has a complex kind ('c').

    Test steps:
    1) Compute the 2-D DFT of KNOWN_3x3.
    2) Assert that the dtype kind is 'c' (complex).
    """

    # Steps (1)+(2) - Transform and check dtype.
    F = dft_2d(image=KNOWN_3x3)
    assert np.iscomplexobj(F)


def test_dft_2d_dc_component_equals_pixel_sum():
    """
    Test purpose - The DC component F(0,0) equals the sum of all pixel values.
    Criteria - By the DFT definition, F(0,0) = Σ f(x,y) · e^0 = Σ f(x,y).

    Test steps:
    1) Compute the 2-D DFT of KNOWN_3x3.
    2) Assert that Re{F(0,0)} ≈ sum of KNOWN_3x3.
    3) Assert that Im{F(0,0)} ≈ 0.
    """

    # Steps (1)+(2)+(3) - Transform and verify DC.
    F = dft_2d(image=KNOWN_3x3)
    np.testing.assert_almost_equal(F[0, 0].real, np.sum(KNOWN_3x3), decimal=10)
    np.testing.assert_almost_equal(F[0, 0].imag, 0.0, decimal=10)


def test_dft_2d_uniform_image_only_dc_nonzero():
    """
    Test purpose - The DFT of a uniform image has energy only at DC.
    Criteria - For a constant-valued image, f(x,y) = c, the DFT is
               F(0,0) = M·N·c and F(u,v) = 0 for all (u,v) ≠ (0,0).

    Test steps:
    1) Compute the 2-D DFT of UNIFORM_5x5 (all pixels = 0.5).
    2) Assert that F(0,0).real ≈ 5×5×0.5 = 12.5.
    3) Assert that all off-DC magnitudes are ≈ 0.
    """

    # Steps (1)+(2) - Transform and verify DC value.
    F = dft_2d(image=UNIFORM_5x5)
    np.testing.assert_almost_equal(F[0, 0].real, 5 * 5 * 0.5, decimal=10)

    # Step (3) - Verify all other components are zero.
    F_copy = F.copy()
    F_copy[0, 0] = 0.0
    np.testing.assert_almost_equal(np.abs(F_copy).max(), 0.0, decimal=10)


# ──────────────────────────────────────────────────────────────────────────── #
#  idft_2d tests                                                                #
# ──────────────────────────────────────────────────────────────────────────── #

def test_idft_2d_output_shape():
    """
    Test purpose - The 2-D IDFT preserves spatial dimensions.
    Criteria - The output of idft_2d has the same shape as the input spectrum.

    Test steps:
    1) Compute the DFT of KNOWN_3x3.
    2) Compute the IDFT of the result.
    3) Assert the shape equals (3, 3).
    """

    # Steps (1)+(2)+(3) - Roundtrip and assert shape.
    F = dft_2d(image=KNOWN_3x3)
    result = idft_2d(dft=F)
    assert result.shape == KNOWN_3x3.shape


def test_dft_idft_roundtrip():
    """
    Test purpose - Applying IDFT after DFT perfectly reconstructs the original image.
    Criteria - idft_2d(dft_2d(image)) ≈ image to within floating-point tolerance.

    Test steps:
    1) Compute DFT of KNOWN_3x3.
    2) Compute IDFT of the DFT result.
    3) Assert that the reconstructed image matches KNOWN_3x3 element-wise.
    """

    # Steps (1)+(2)+(3) - Roundtrip and compare.
    reconstructed = idft_2d(dft=dft_2d(image=KNOWN_3x3))
    np.testing.assert_allclose(reconstructed, KNOWN_3x3, atol=1e-10)


# ──────────────────────────────────────────────────────────────────────────── #
#  ideal_lowpass_filter tests                                                   #
# ──────────────────────────────────────────────────────────────────────────── #

def test_ideal_lowpass_output_shape():
    """
    Test purpose - The ideal LPF preserves image dimensions.
    Criteria - The output of ideal_lowpass_filter has the same shape as the input.

    Test steps:
    1) Apply ideal_lowpass_filter to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Filter and assert shape.
    result = ideal_lowpass_filter(image=KNOWN_3x3, cutoff=5.0,
                                   normalization_method='unchanged')
    assert result.shape == KNOWN_3x3.shape


def test_ideal_lowpass_large_cutoff_preserves_image():
    """
    Test purpose - An ideal LPF with a very large cutoff acts as an all-pass filter.
    Criteria - When D₀ >> image diagonal, all frequencies are inside the pass-band,
               so the IFFT of the unmodified spectrum equals the original image.

    Test steps:
    1) Apply ideal_lowpass_filter to KNOWN_3x3 with cutoff=1000 (passes everything).
    2) Assert that the result ≈ KNOWN_3x3.
    """

    # Steps (1)+(2) - Filter and compare.
    result = ideal_lowpass_filter(image=KNOWN_3x3, cutoff=1000.0,
                                   normalization_method='unchanged')
    np.testing.assert_allclose(result, KNOWN_3x3, atol=1e-10)


# ──────────────────────────────────────────────────────────────────────────── #
#  ideal_highpass_filter tests                                                  #
# ──────────────────────────────────────────────────────────────────────────── #

def test_ideal_highpass_output_shape():
    """
    Test purpose - The ideal HPF preserves image dimensions.
    Criteria - The output of ideal_highpass_filter has the same shape as the input.

    Test steps:
    1) Apply ideal_highpass_filter to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Filter and assert shape.
    result = ideal_highpass_filter(image=KNOWN_3x3, cutoff=5.0,
                                    normalization_method='unchanged')
    assert result.shape == KNOWN_3x3.shape


def test_ideal_highpass_zero_cutoff_passes_everything():
    """
    Test purpose - An ideal HPF with D₀=0 passes all frequencies (only DC at D=0 is blocked,
                   but DC has measure zero in a finite spectrum).
    Criteria - With cutoff=0, H(u,v)=1 for all (u,v) with D>0; the only blocked component
               is the exact DC bin.  The result differs from the original only by its mean.

    Test steps:
    1) Apply ideal_highpass_filter to UNIFORM_5x5 with cutoff=0.
    2) Assert that the center pixel [2,2] of the result is ≈ 0 (DC removed from flat image).
    """

    # Steps (1)+(2) - Filter and verify DC removal.
    result = ideal_highpass_filter(image=UNIFORM_5x5, cutoff=0.0,
                                    normalization_method='unchanged')
    np.testing.assert_almost_equal(result[2, 2], 0.0, decimal=10)


# ──────────────────────────────────────────────────────────────────────────── #
#  Ideal LPF + HPF complementarity                                              #
# ──────────────────────────────────────────────────────────────────────────── #

def test_ideal_lowpass_plus_highpass_equals_original():
    """
    Test purpose - The ideal LPF and HPF are strict complements: H_LP + H_HP = 1.
    Criteria - IFFT{H_LP · F} + IFFT{H_HP · F} = IFFT{F} = f(x,y).
               With normalization_method='unchanged', the sum of the two filtered images
               must equal the original image element-wise.

    Test steps:
    1) Apply ideal_lowpass_filter  to KNOWN_3x3 with cutoff=1.5, normalization 'unchanged'.
    2) Apply ideal_highpass_filter to KNOWN_3x3 with cutoff=1.5, normalization 'unchanged'.
    3) Assert that lp_result + hp_result ≈ KNOWN_3x3.
    """

    # Steps (1)+(2) - Compute both filtered images.
    cutoff = 1.5
    lp = ideal_lowpass_filter( image=KNOWN_3x3, cutoff=cutoff, normalization_method='unchanged')
    hp = ideal_highpass_filter(image=KNOWN_3x3, cutoff=cutoff, normalization_method='unchanged')

    # Step (3) - Sum must equal original.
    np.testing.assert_allclose(lp + hp, KNOWN_3x3, atol=1e-10)


# ──────────────────────────────────────────────────────────────────────────── #
#  butterworth_lowpass_filter tests                                             #
# ──────────────────────────────────────────────────────────────────────────── #

def test_butterworth_lowpass_output_shape():
    """
    Test purpose - The Butterworth LPF preserves image dimensions.
    Criteria - The output of butterworth_lowpass_filter has the same shape as the input.

    Test steps:
    1) Apply butterworth_lowpass_filter to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Filter and assert shape.
    result = butterworth_lowpass_filter(image=KNOWN_3x3, cutoff=5.0, order=2,
                                         normalization_method='unchanged')
    assert result.shape == KNOWN_3x3.shape


def test_butterworth_lowpass_plus_highpass_equals_original():
    """
    Test purpose - Butterworth LPF and HPF are strict complements: H_LP + H_HP = 1.
    Criteria - Because H_BW_HP = 1 − H_BW_LP, their IFFT outputs sum to the original image.

    Test steps:
    1) Apply butterworth_lowpass_filter  to KNOWN_3x3, order=2, cutoff=1.5, normalization 'unchanged'.
    2) Apply butterworth_highpass_filter to KNOWN_3x3, order=2, cutoff=1.5, normalization 'unchanged'.
    3) Assert that lp_result + hp_result ≈ KNOWN_3x3.
    """

    # Steps (1)+(2) - Compute both filtered images.
    cutoff, order = 1.5, 2
    lp = butterworth_lowpass_filter( image=KNOWN_3x3, cutoff=cutoff, order=order,
                                      normalization_method='unchanged')
    hp = butterworth_highpass_filter(image=KNOWN_3x3, cutoff=cutoff, order=order,
                                      normalization_method='unchanged')

    # Step (3) - Sum must equal original.
    np.testing.assert_allclose(lp + hp, KNOWN_3x3, atol=1e-10)


# ──────────────────────────────────────────────────────────────────────────── #
#  butterworth_highpass_filter tests                                            #
# ──────────────────────────────────────────────────────────────────────────── #

def test_butterworth_highpass_output_shape():
    """
    Test purpose - The Butterworth HPF preserves image dimensions.
    Criteria - The output of butterworth_highpass_filter has the same shape as the input.

    Test steps:
    1) Apply butterworth_highpass_filter to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Filter and assert shape.
    result = butterworth_highpass_filter(image=KNOWN_3x3, cutoff=5.0, order=2,
                                          normalization_method='unchanged')
    assert result.shape == KNOWN_3x3.shape


def test_butterworth_highpass_uniform_image_near_zero():
    """
    Test purpose - The Butterworth HPF of a uniform image yields ≈ zero interior pixels.
    Criteria - A constant image has no high-frequency content, so the HPF output should
               be close to zero (the DC bin is completely blocked, and no other energy exists).

    Test steps:
    1) Apply butterworth_highpass_filter to UNIFORM_5x5, cutoff=1.0, order=2, normalization 'unchanged'.
    2) Assert that the center pixel [2,2] ≈ 0.
    """

    # Steps (1)+(2) - Filter and verify near-zero center.
    result = butterworth_highpass_filter(image=UNIFORM_5x5, cutoff=1.0, order=2,
                                          normalization_method='unchanged')
    np.testing.assert_almost_equal(result[2, 2], 0.0, decimal=5)


# ──────────────────────────────────────────────────────────────────────────── #
#  gaussian_lowpass_filter tests                                                #
# ──────────────────────────────────────────────────────────────────────────── #

def test_gaussian_lowpass_output_shape():
    """
    Test purpose - The Gaussian LPF preserves image dimensions.
    Criteria - The output of gaussian_lowpass_filter has the same shape as the input.

    Test steps:
    1) Apply gaussian_lowpass_filter to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Filter and assert shape.
    result = gaussian_lowpass_filter(image=KNOWN_3x3, sigma=5.0, normalization_method='unchanged')
    assert result.shape == KNOWN_3x3.shape


def test_gaussian_lowpass_large_sigma_preserves_image():
    """
    Test purpose - A Gaussian LPF with σ → ∞ acts as an all-pass filter.
    Criteria - At very large σ, H(u,v) = exp(−D²/2σ²) ≈ 1 for all D, so the
               filtered image ≈ original.

    Test steps:
    1) Apply gaussian_lowpass_filter to KNOWN_3x3 with σ=1e6.
    2) Assert that the result ≈ KNOWN_3x3.
    """

    # Steps (1)+(2) - Filter and compare.
    result = gaussian_lowpass_filter(image=KNOWN_3x3, sigma=1e6, normalization_method='unchanged')
    np.testing.assert_allclose(result, KNOWN_3x3, atol=1e-6)


# ──────────────────────────────────────────────────────────────────────────── #
#  gaussian_highpass_filter tests                                               #
# ──────────────────────────────────────────────────────────────────────────── #

def test_gaussian_highpass_output_shape():
    """
    Test purpose - The Gaussian HPF preserves image dimensions.
    Criteria - The output of gaussian_highpass_filter has the same shape as the input.

    Test steps:
    1) Apply gaussian_highpass_filter to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Filter and assert shape.
    result = gaussian_highpass_filter(image=KNOWN_3x3, sigma=5.0, normalization_method='unchanged')
    assert result.shape == KNOWN_3x3.shape


def test_gaussian_lowpass_plus_highpass_equals_original():
    """
    Test purpose - Gaussian LPF and HPF are strict complements: H_GLP + H_GHP = 1.
    Criteria - Because H_GHP = 1 − H_GLP, their IFFT outputs sum to the original image.

    Test steps:
    1) Apply gaussian_lowpass_filter  to KNOWN_3x3, σ=1.5, normalization 'unchanged'.
    2) Apply gaussian_highpass_filter to KNOWN_3x3, σ=1.5, normalization 'unchanged'.
    3) Assert that lp_result + hp_result ≈ KNOWN_3x3.
    """

    # Steps (1)+(2) - Compute both filtered images.
    sigma = 1.5
    lp = gaussian_lowpass_filter( image=KNOWN_3x3, sigma=sigma, normalization_method='unchanged')
    hp = gaussian_highpass_filter(image=KNOWN_3x3, sigma=sigma, normalization_method='unchanged')

    # Step (3) - Sum must equal original.
    np.testing.assert_allclose(lp + hp, KNOWN_3x3, atol=1e-10)


def test_gaussian_highpass_uniform_image_near_zero():
    """
    Test purpose - The Gaussian HPF of a uniform image yields ≈ zero interior pixels.
    Criteria - A constant image has all its energy at DC; the Gaussian HPF blocks DC
               (H=0 at D=0), so the filtered output should be ≈ 0 everywhere.

    Test steps:
    1) Apply gaussian_highpass_filter to UNIFORM_5x5, σ=1.0, normalization 'unchanged'.
    2) Assert that the center pixel [2,2] ≈ 0.
    """

    # Steps (1)+(2) - Filter and verify near-zero center.
    result = gaussian_highpass_filter(image=UNIFORM_5x5, sigma=1.0, normalization_method='unchanged')
    np.testing.assert_almost_equal(result[2, 2], 0.0, decimal=5)


# ──────────────────────────────────────────────────────────────────────────── #
#  notch_reject_filter tests                                                    #
# ──────────────────────────────────────────────────────────────────────────── #

def test_notch_reject_output_shape():
    """
    Test purpose - The notch reject filter preserves image dimensions.
    Criteria - The output of notch_reject_filter has the same shape as the input.

    Test steps:
    1) Apply notch_reject_filter to KNOWN_3x3 with one notch pair.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Filter and assert shape.
    result = notch_reject_filter(image=KNOWN_3x3, notch_centers=[(0, 1)],
                                  notch_radius=0.5, normalization_method='unchanged')
    assert result.shape == KNOWN_3x3.shape


def test_notch_reject_empty_notches_is_all_pass():
    """
    Test purpose - An empty notch list produces an all-pass filter.
    Criteria - With no notch centres, H = 1 everywhere, so the filtered image
               equals the original.

    Test steps:
    1) Apply notch_reject_filter to KNOWN_3x3 with notch_centers=[].
    2) Assert that the result ≈ KNOWN_3x3.
    """

    # Steps (1)+(2) - Filter and compare.
    result = notch_reject_filter(image=KNOWN_3x3, notch_centers=[],
                                  notch_radius=1.0, normalization_method='unchanged')
    np.testing.assert_allclose(result, KNOWN_3x3, atol=1e-10)


def test_notch_reject_suppresses_sinusoidal_noise():
    """
    Test purpose - A notch filter reduces energy at the targeted frequency pair.
    Criteria - Adding a known sinusoidal pattern (periodic noise) to a uniform base and
               then applying a notch at its frequency should yield a result closer to
               the base than the noisy image.

    Test steps:
    1) Build a 16×16 uniform base image (all pixels = 0.5).
    2) Add a sinusoidal noise pattern at frequency (u₀=4, v₀=0).
    3) Apply notch_reject_filter centred at (4, 0) with radius 1.
    4) Assert that the MSE between the notch-filtered image and the base is less than
       the MSE between the noisy image and the base.
    """

    M, N = 16, 16
    base = np.full((M, N), 0.5)

    # Step (2) - Sinusoidal noise at frequency u₀=4 along rows.
    u0 = 4
    x = np.arange(M).reshape(-1, 1)
    noise = 0.2 * np.cos(2 * np.pi * u0 * x / M) * np.ones((M, N))
    noisy = np.clip(base + noise, 0.0, 1.0)

    # Step (3) - Apply notch at the noise frequency pair (u₀=4, v₀=0).
    # Use 'unchanged' so values stay near 0.5; 'stretch' on a near-flat image would
    # amplify floating-point residuals and inflate the MSE.
    filtered = notch_reject_filter(image=noisy, notch_centers=[(u0, 0)],
                                    notch_radius=1.0, normalization_method='unchanged')

    # Step (4) - Compare MSE values.
    mse_noisy    = np.mean((noisy    - base) ** 2)
    mse_filtered = np.mean((filtered - base) ** 2)
    assert mse_filtered < mse_noisy


# ──────────────────────────────────────────────────────────────────────────── #
#  homomorphic_filter tests                                                     #
# ──────────────────────────────────────────────────────────────────────────── #

def test_homomorphic_filter_output_shape():
    """
    Test purpose - The homomorphic filter preserves image dimensions.
    Criteria - The output of homomorphic_filter has the same shape as the input.

    Test steps:
    1) Apply homomorphic_filter to KNOWN_3x3.
    2) Assert that the output shape equals KNOWN_3x3.shape.
    """

    # Steps (1)+(2) - Filter and assert shape.
    result = homomorphic_filter(image=KNOWN_3x3, gamma_l=0.25, gamma_h=2.0,
                                 c=1.0, sigma=1.5, normalization_method='stretch')
    assert result.shape == KNOWN_3x3.shape


def test_homomorphic_filter_output_normalized_with_stretch():
    """
    Test purpose - After 'stretch' normalization the homomorphic output is in [0, 1].
    Criteria - All pixel values of the output are between 0 and 1 inclusive.

    Test steps:
    1) Apply homomorphic_filter to KNOWN_3x3 with normalization_method='stretch'.
    2) Assert that the minimum pixel value ≥ 0.
    3) Assert that the maximum pixel value ≤ 1.
    """

    # Steps (1)+(2)+(3) - Filter and check range.
    result = homomorphic_filter(image=KNOWN_3x3, gamma_l=0.25, gamma_h=2.0,
                                 c=1.0, sigma=1.5, normalization_method='stretch')
    assert result.min() >= 0.0
    assert result.max() <= 1.0


def test_homomorphic_filter_gamma_l_equals_gamma_h_is_identity():
    """
    Test purpose - When γ_L = γ_H = 1 the homomorphic filter H(u,v) = 1 for all (u,v),
                   acting as an all-pass filter on the log-domain signal.
    Criteria - The pipeline log → FFT → H=1 → IFFT → exp is a no-op on the
               original image values (up to floating-point rounding).

    Test steps:
    1) Apply homomorphic_filter to KNOWN_3x3 with γ_L=1.0, γ_H=1.0, c=1.0, σ=1.5.
    2) Assert that the result ≈ KNOWN_3x3 (after stretch normalization).
    Note: stretch normalisation is applied to both sides of the comparison.
    """

    from Image_Processing.Source.Basic.common import image_normalization

    # Steps (1)+(2) - Identity homomorphic filter; compare stretch-normalised outputs.
    result = homomorphic_filter(image=KNOWN_3x3, gamma_l=1.0, gamma_h=1.0,
                                 c=1.0, sigma=1.5, normalization_method='stretch')
    expected = image_normalization(image=KNOWN_3x3.copy(), normalization_method='stretch')
    np.testing.assert_allclose(result, expected, atol=1e-6)
