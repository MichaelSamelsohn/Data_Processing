"""
Script Name - metrics.py

Purpose - Standard full-reference image quality metrics for evaluating the fidelity of a processed or restored image
relative to a clean reference.

Three complementary metrics are provided:

    MSE  (Mean Square Error)
         Measures the average squared pixel-level difference. Simple and fast, but does not correlate well with
         perceived image quality because it treats all errors equally regardless of their spatial structure.

    PSNR (Peak Signal-to-Noise Ratio)
         A logarithmic (dB) rescaling of MSE relative to the signal peak. Widely used as a benchmark in image
         compression and restoration. Higher is better; values above ~30 dB are generally considered acceptable. Returns
         np.inf for identical images.

    SSIM (Structural Similarity Index Measure)
         Decomposes the comparison into three perceptually meaningful components — luminance, contrast, and structure —
         evaluated locally using a Gaussian sliding window. Correlates significantly better with human visual quality
         judgements than either MSE or PSNR. Returns 1.0 for identical images; values in (0, 1) for typical distortions
         (theoretical range is [-1, 1]).

Created by Michael Samelsohn, 28/02/26.
"""

# Imports #
import numpy as np
from numpy import ndarray
from scipy.ndimage import gaussian_filter

from Image_Processing.Settings.image_settings import *
from Utilities.decorators import book_reference, article_reference

# References #
_WANG_2004 = ("Wang, Z., Bovik, A.C., Sheikh, H.R., Simoncelli, E.P. (2004). "
              "Image Quality Assessment: From Error Visibility to Structural Similarity. "
              "IEEE Transactions on Image Processing, 13(4), 600-612.")


# ──────────────────────────────────────────────────────────── #
# Internal helper                                               #
# ──────────────────────────────────────────────────────────── #

def _check_shapes(image_a: ndarray, image_b: ndarray) -> None:
    """Raise ValueError if the two images do not share the same shape."""
    if image_a.shape != image_b.shape:
        log.raise_exception(
            message=f"Images must have the same shape; got {image_a.shape} and {image_b.shape}.",
            exception=ValueError)


# ──────────────────────────────────────────────────────────── #
# MSE                                                           #
# ──────────────────────────────────────────────────────────── #

@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 8.4 - Image Quality Assessment, p.567")
def mse(image_a: ndarray, image_b: ndarray) -> float:
    """
    Compute the Mean Square Error between two images.

    MSE is defined as the average of the squared pixel-wise differences: MSE = (1 / MN) · Σ Σ [f(x,y) − g(x,y)]²

    MSE = 0 indicates identical images.  As a difference-based measure it is sensitive to global intensity offsets and
    independent pixel errors but ignores spatial structure, so a low MSE does not necessarily imply high perceptual
    quality.

    :param image_a: First image (reference), pixel values in [0, 1].
    :param image_b: Second image (distorted), same shape as image_a.

    :return:        Non-negative scalar MSE value.
    """

    log.info("Computing Mean Square Error (MSE)")
    _check_shapes(image_a, image_b)

    result = float(np.mean((image_a.astype(float) - image_b.astype(float)) ** 2))
    log.info(f"MSE = {result:.6f}")
    return result


# ──────────────────────────────────────────────────────────── #
# PSNR                                                          #
# ──────────────────────────────────────────────────────────── #

@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 8.4 - Image Quality Assessment, p.568")
def psnr(image_a: ndarray, image_b: ndarray,
         max_value: float = DEFAULT_PSNR_MAX_VALUE) -> float:
    """
    Compute the Peak Signal-to-Noise Ratio between two images.

    PSNR expresses the ratio between the maximum possible power of the signal and the power of the corrupting noise on a
    logarithmic decibel scale: PSNR = 10 · log₁₀(MAX² / MSE)
    where MAX is the maximum representable pixel value (1.0 for images normalised to [0, 1]).  Higher values indicate
    better fidelity:
        * ≥ 40 dB  — visually lossless or near-lossless.
        * 30–40 dB — acceptable; typical of moderate compression or mild noise.
        * < 30 dB  — noticeable degradation.
        * np.inf   — images are identical (MSE = 0).

    :param image_a:   Reference image, pixel values in [0, 1].
    :param image_b:   Distorted image, same shape as image_a.
    :param max_value: Peak signal value (default 1.0 for normalised images).

    :return:          PSNR in decibels, or np.inf if the images are identical.
    """

    log.info("Computing Peak Signal-to-Noise Ratio (PSNR)")
    _check_shapes(image_a, image_b)

    error = mse(image_a, image_b)

    if error == 0.0:
        log.info("PSNR = inf (images are identical)")
        return np.inf

    result = float(10.0 * np.log10(max_value ** 2 / error))
    log.info(f"PSNR = {result:.2f} dB")
    return result


# ──────────────────────────────────────────────────────────── #
# SSIM                                                          #
# ──────────────────────────────────────────────────────────── #

@article_reference(article=_WANG_2004)
def ssim(image_a: ndarray, image_b: ndarray,
         sigma: float = DEFAULT_SSIM_SIGMA,
         k1: float = DEFAULT_SSIM_K1,
         k2: float = DEFAULT_SSIM_K2) -> float:
    """
    Compute the mean Structural Similarity Index Measure (MSSIM) between two images.

    SSIM decomposes image fidelity into three locally-evaluated components using a Gaussian sliding window of standard
    deviation σ:
        l(x, y)  — luminance:  (2·μ_x·μ_y + C₁) / (μ_x² + μ_y² + C₁)
        c(x, y)  — contrast:   (2·σ_x·σ_y + C₂) / (σ_x² + σ_y² + C₂)
        s(x, y)  — structure:  (σ_xy + C₃)       / (σ_x·σ_y + C₃

    With α = β = γ = 1 and C₃ = C₂/2, the combined formula simplifies to:
        SSIM(x, y) = [(2·μ_x·μ_y + C₁)(2·σ_xy + C₂)]
                   / [(μ_x² + μ_y² + C₁)(σ_x² + σ_y² + C₂)]
    where:
        μ_x, μ_y    — local Gaussian-weighted means.
        σ_x², σ_y²  — local Gaussian-weighted variances.
        σ_xy        — local Gaussian-weighted covariance.
        C₁ = (K₁·L)², C₂ = (K₂·L)² — small stability constants (L = 1.0 here).

    The returned value is the mean of the SSIM map over all spatial positions.

    :param image_a: Reference image, pixel values in [0, 1].
    :param image_b: Distorted image, same shape as image_a.
    :param sigma:   Standard deviation of the Gaussian window used for local statistics.
    :param k1:      Stability constant for the luminance term (default 0.01).
    :param k2:      Stability constant for the contrast/structure term (default 0.03).

    :return:        Mean SSIM scalar in [-1, 1]; 1.0 indicates perfect similarity.
    """

    log.info(f"Computing Structural Similarity Index (SSIM) with σ={sigma}, K1={k1}, K2={k2}")
    _check_shapes(image_a, image_b)

    a = image_a.astype(float)
    b = image_b.astype(float)

    L = 1.0                   # dynamic range for [0, 1] images
    C1 = (k1 * L) ** 2       # luminance stability constant
    C2 = (k2 * L) ** 2       # contrast/structure stability constant

    log.debug("Computing local means via Gaussian filtering")
    mu_a = gaussian_filter(a, sigma=sigma)
    mu_b = gaussian_filter(b, sigma=sigma)

    mu_a_sq = mu_a ** 2
    mu_b_sq = mu_b ** 2
    mu_ab   = mu_a * mu_b

    log.debug("Computing local variances and covariance")
    sigma_a_sq = gaussian_filter(a ** 2, sigma=sigma) - mu_a_sq
    sigma_b_sq = gaussian_filter(b ** 2, sigma=sigma) - mu_b_sq
    sigma_ab   = gaussian_filter(a * b,  sigma=sigma) - mu_ab

    log.debug("Assembling the SSIM map")
    numerator   = (2.0 * mu_ab + C1) * (2.0 * sigma_ab + C2)
    denominator = (mu_a_sq + mu_b_sq + C1) * (sigma_a_sq + sigma_b_sq + C2)
    ssim_map    = numerator / denominator

    result = float(np.mean(ssim_map))
    log.info(f"SSIM = {result:.4f}")
    return result


# ──────────────────────────────────────────────────────────── #
# ImageComparator                                               #
# ──────────────────────────────────────────────────────────── #

class ImageComparator:
    """
    Compute and display all three quality metrics for an original / distorted image pair.

    All three metrics are evaluated on construction and cached so that repeated calls to print() or as_dict() are free.
    Usage:
        comparator = ImageComparator(original=clean, distorted=restored)
        comparator.print()

        ┌──────────────────────────────────┐
        │  MSE   : 0.001420                │
        │  PSNR  : 28.47 dB               │
        │  SSIM  : 0.8912                  │
        └──────────────────────────────────┘

    The individual values are also accessible as properties::

        comparator.mse_value    # float
        comparator.psnr_value   # float or np.inf
        comparator.ssim_value   # float in [-1, 1]
    """

    def __init__(self, original: ndarray, distorted: ndarray) -> None:
        """
        :param original:  Clean reference image, pixel values in [0, 1].
        :param distorted: Processed / degraded image; must be the same shape as original.
        """
        log.info("ImageComparator: computing MSE, PSNR, and SSIM")
        self.mse_value  = mse( image_a=original, image_b=distorted)
        self.psnr_value = psnr(image_a=original, image_b=distorted)
        self.ssim_value = ssim(image_a=original, image_b=distorted)

    # ── Formatted output ─────────────────────────────────────────────────── #

    def report(self) -> str:
        """
        Build and return the formatted quality report as a multi-line string.

        The box width adapts to the longest row so that values are never truncated.
        """
        psnr_str = "∞ dB" if self.psnr_value == np.inf else f"{self.psnr_value:.2f} dB"

        rows = [
            f"  {'MSE':<6}: {self.mse_value:.6f}",
            f"  {'PSNR':<6}: {psnr_str}",
            f"  {'SSIM':<6}: {self.ssim_value:.4f}",
        ]

        inner_width = max(34, max(len(r) for r in rows) + 2)
        top    = "┌" + "─" * inner_width + "┐"
        bottom = "└" + "─" * inner_width + "┘"
        body   = "\n".join(f"│{row:<{inner_width}}│" for row in rows)

        return "\n".join([top, body, bottom])

    def print(self) -> None:
        """Print the formatted quality report to stdout."""
        print(self.report())

    # ── Data access ──────────────────────────────────────────────────────── #

    def as_dict(self) -> dict:
        """Return the three metric values as a plain dictionary."""
        return {
            "MSE":  self.mse_value,
            "PSNR": self.psnr_value,
            "SSIM": self.ssim_value,
        }

    def __repr__(self) -> str:
        psnr_str = "inf" if self.psnr_value == np.inf else f"{self.psnr_value:.2f}"
        return (f"ImageComparator("
                f"MSE={self.mse_value:.6f}, "
                f"PSNR={psnr_str} dB, "
                f"SSIM={self.ssim_value:.4f})")
