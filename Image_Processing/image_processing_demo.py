"""
Script Name - image_processing_demo.py

Purpose - Demonstrate the Image Processing module using the classic Lena image.

Structure
---------
Part 1 – Standalone showcases (single functions, side-by-side comparisons)
    1a. Noise model zoo         – four common noise types at a glance
    1b. Frequency filter family – ideal / Butterworth / Gaussian low-pass compared
    1c. Edge detector survey    – Sobel, Marr-Hildreth, Canny

Part 2 – Pipelines (chained steps achieving a coherent result)
    2a. Impulse-noise restoration – S&P corruption → median filter → Otsu segmentation
    2b. Blur & Wiener recovery    – Gaussian blur + noise → Wiener deconvolution → edge comparison
    2c. Homomorphic equalisation  – simulated dark gradient → homomorphic filter → histogram

Quality metrics (MSE, PSNR, SSIM) are reported in both the console and the figures
wherever a meaningful reference image exists.

Created by Michael Samelsohn, 28/02/26.
"""

# Imports #
import os
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

from Image_Processing.Source.Basic.common import convert_to_grayscale, generate_filter
from Image_Processing.Source.Advanced.noise_models import (
    add_gaussian_noise, add_salt_and_pepper, add_rayleigh_noise, add_uniform_noise,
)
from Image_Processing.Source.Advanced.spatial_filtering import blur_image, sobel_filter
from Image_Processing.Source.Advanced.segmentation import (
    marr_hildreth_edge_detection, canny_edge_detection, otsu_global_thresholding,
)
from Image_Processing.Source.Advanced.restoration import order_statistic_filter, wiener_filter
from Image_Processing.Source.Advanced.frequency_domain import (
    ideal_lowpass_filter, butterworth_lowpass_filter, gaussian_lowpass_filter, homomorphic_filter,
)
from Image_Processing.Source.Advanced.metrics import ImageComparator, psnr, ssim
from settings import log


# ──────────────────────────────────────────────────────────── #
# Internal helpers                                              #
# ──────────────────────────────────────────────────────────── #

_LENA_PATH = os.path.join(os.path.dirname(__file__), 'Images', 'Lena.png')


def _load_lena_color() -> np.ndarray:
    """Load Lena.png as float64 RGB in [0, 1]."""
    img = mpimg.imread(_LENA_PATH)
    if img.ndim == 3 and img.shape[2] == 4:   # drop alpha channel if present
        img = img[:, :, :3]
    return img.astype(np.float64)


def _load_lena_gray() -> np.ndarray:
    """Load Lena.png and convert to grayscale float64 in [0, 1]."""
    return convert_to_grayscale(image=_load_lena_color())


def _imshow(ax: plt.Axes, image: np.ndarray, title: str) -> None:
    """Render one image on *ax* with a title and no axis ticks."""
    cmap = 'gray' if image.ndim == 2 else None
    ax.imshow(image, cmap=cmap, vmin=0, vmax=1)
    ax.set_title(title, fontsize=9)
    ax.axis('off')


def _show(figure_title: str) -> None:
    """Apply a bold super-title, tighten layout, and display the current figure."""
    plt.suptitle(figure_title, fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.show()


def _section(label: str) -> None:
    log.info(f"{'─' * 60}")
    log.info(f"{label}")
    log.info(f"{'─' * 60}")


def _metrics_str(reference: np.ndarray, image: np.ndarray) -> str:
    """Return a one-line 'PSNR X.X dB | SSIM X.XXX' annotation string."""
    p = psnr(reference, image)
    s = ssim(reference, image)
    psnr_fmt = "∞" if p == np.inf else f"{p:.1f}"
    return f"PSNR {psnr_fmt} dB  |  SSIM {s:.3f}"


def _print_comparator(label: str, reference: np.ndarray, image: np.ndarray) -> None:
    """Print a labelled ImageComparator report to the console."""
    log.info(f"Metrics — {label}")
    ImageComparator(original=reference, distorted=image).print()


# ──────────────────────────────────────────────────────────── #
# Part 1a — Noise model zoo                                     #
# ──────────────────────────────────────────────────────────── #

def showcase_noise_zoo() -> None:
    """
    Display Lena with four common noise types applied.

    Noise models shown:
        • Gaussian      – electronic sensor noise; Gaussian distribution.
        • Salt & Pepper – impulse noise; random pixels set to 0 or 1.
        • Rayleigh      – common in range/radar imaging.
        • Uniform       – digitisation rounding error model.

    PSNR and SSIM relative to the original are shown in each panel title and
    printed as full ImageComparator reports to the console.
    """
    _section("Part 1a — Noise Model Zoo")

    lena = _load_lena_gray()
    np.random.seed(0)

    noisy_variants = [
        (add_gaussian_noise(lena,  mean=0,      sigma=0.05), "Gaussian  (σ=0.05)"),
        (add_salt_and_pepper(lena, pepper=0.02, salt=0.02),  "Salt & Pepper  (2% each)"),
        (add_rayleigh_noise(lena,  a=-0.125,    b=0.01),     "Rayleigh"),
        (add_uniform_noise(lena,   a=-0.08,     b=0.08),     "Uniform  [−0.08, 0.08]"),
    ]

    # Console: full report for each noise type.
    for img, label in noisy_variants:
        _print_comparator(label, lena, img)

    # Figure: original + noisy variants with metric annotations in titles.
    panels = [(lena, "Original (grayscale)")] + [
        (img, f"{label}\n{_metrics_str(lena, img)}")
        for img, label in noisy_variants
    ]

    fig, axes = plt.subplots(1, 5, figsize=(22, 5))
    for ax, (img, label) in zip(axes, panels):
        _imshow(ax, img, label)
    _show("Showcase 1a — Noise Model Zoo")


# ──────────────────────────────────────────────────────────── #
# Part 1b — Frequency-domain low-pass filter family            #
# ──────────────────────────────────────────────────────────── #

def showcase_frequency_filters() -> None:
    """
    Compare three frequency-domain low-pass filter designs side-by-side.

    All filters share the same cut-off distance D₀ = 30 pixels (in the shifted spectrum):
        • Ideal       – perfect brick-wall; strong ringing (Gibbs effect).
        • Butterworth – smooth roll-off; little ringing.
        • Gaussian    – maximally smooth; no ringing at all.

    PSNR and SSIM show how much of the original signal each filter preserves.
    Higher PSNR / SSIM means less introduced distortion (less aggressive smoothing).
    """
    _section("Part 1b — Frequency-Domain Low-Pass Filter Family")

    lena   = _load_lena_gray()
    cutoff = 30

    filtered_variants = [
        (ideal_lowpass_filter(lena,       cutoff=cutoff,        normalization_method='unchanged'),
         f"Ideal LP  (D₀={cutoff})"),
        (butterworth_lowpass_filter(lena, cutoff=cutoff, order=2, normalization_method='unchanged'),
         f"Butterworth LP  (D₀={cutoff}, n=2)"),
        (gaussian_lowpass_filter(lena,    sigma=cutoff,         normalization_method='unchanged'),
         f"Gaussian LP  (σ={cutoff})"),
    ]

    # Console: full report for each filter.
    for img, label in filtered_variants:
        _print_comparator(label, lena, img)

    # Figure: original + filtered variants with metric annotations.
    panels = [(lena, "Original")] + [
        (img, f"{label}\n{_metrics_str(lena, img)}")
        for img, label in filtered_variants
    ]

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    for ax, (img, label) in zip(axes, panels):
        _imshow(ax, img, label)
    _show("Showcase 1b — Frequency-Domain Low-Pass Filter Family")


# ──────────────────────────────────────────────────────────── #
# Part 1c — Edge detector survey                               #
# ──────────────────────────────────────────────────────────── #

def showcase_edge_detectors() -> None:
    """
    Compare three classical edge / feature detectors on Lena.

        • Sobel         – first-order gradient; fast, noise-sensitive.
        • Marr-Hildreth – LoG zero-crossings; smooth but can produce thick edges.
        • Canny         – multi-stage optimal detector; thin, well-localised edges.

    Pixel-level quality metrics are not shown here: edge maps are binary or near-binary
    images that are not comparable to the grayscale original via MSE/PSNR/SSIM.

    A 256×256 downsample is used to keep the Python-loop operations manageable.
    """
    _section("Part 1c — Edge Detector Survey  (256×256; may take ~30 s)")

    lena = _load_lena_gray()[::2, ::2]   # downsample 512 → 256 for speed

    # Lightly smooth before detection to suppress sensor noise.
    smooth = blur_image(lena, filter_type='gaussian', filter_size=5, padding_type='zero',
                        sigma=1.0, normalization_method='unchanged')

    sobel_mag = sobel_filter(smooth, padding_type='zero', normalization_method='stretch')['Magnitude']
    marr      = marr_hildreth_edge_detection(smooth, filter_size=5, padding_type='zero',
                                             sigma=1.0, include_diagonal_terms=False, threshold=0.05)
    canny     = canny_edge_detection(smooth, filter_size=5, padding_type='zero',
                                     sigma=1.0, high_threshold=0.1, low_threshold=0.04)

    panels = [
        (lena,      "Lena (256×256)"),
        (sobel_mag, "Sobel magnitude"),
        (marr,      "Marr-Hildreth"),
        (canny,     "Canny"),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    for ax, (img, label) in zip(axes, panels):
        _imshow(ax, img, label)
    _show("Showcase 1c — Edge Detector Survey")


# ──────────────────────────────────────────────────────────── #
# Part 2a — Pipeline: impulse denoising → segmentation         #
# ──────────────────────────────────────────────────────────── #

def pipeline_impulse_denoising() -> None:
    """
    Full restoration pipeline for salt-and-pepper noise:

        grayscale  →  S&P corruption (5% + 5%)
                   →  3×3 median filter
                   →  Otsu automatic thresholding

    The median filter excels at impulse noise because it replaces each pixel with the
    median of its neighbourhood, making it immune to the extreme 0/1 outliers that
    salt-and-pepper noise introduces.  Otsu's method then automatically finds the
    optimal threshold to binarise the cleaned image.

    Metrics confirm the improvement: PSNR and SSIM both increase after the median
    filter is applied.

    A 256×256 downsample is used to keep the spatial-loop operations manageable.
    """
    _section("Part 2a — Impulse-Noise Restoration & Segmentation  (256×256; may take ~30 s)")

    np.random.seed(42)
    lena = _load_lena_gray()[::2, ::2]   # 256×256

    noisy    = add_salt_and_pepper(lena, pepper=0.05, salt=0.05)
    restored = order_statistic_filter(noisy, filter_type='median',
                                      padding_type='mirror', filter_size=3)
    segmented = otsu_global_thresholding(restored)

    # Console: before and after the median filter.
    _print_comparator("Noisy (S&P 5%+5%) vs. Original", lena, noisy)
    _print_comparator("Median-Restored vs. Original",   lena, restored)

    panels = [
        (lena,      "Grayscale Lena\n(reference)"),
        (noisy,     f"Salt & Pepper  (5%+5%)\n{_metrics_str(lena, noisy)}"),
        (restored,  f"After 3×3 Median Filter\n{_metrics_str(lena, restored)}"),
        (segmented, "Otsu Segmentation"),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(22, 5))
    for ax, (img, label) in zip(axes, panels):
        _imshow(ax, img, label)
    _show("Pipeline 2a — Impulse-Noise Restoration & Segmentation")


# ──────────────────────────────────────────────────────────── #
# Part 2b — Pipeline: blur + noise → Wiener deconvolution      #
# ──────────────────────────────────────────────────────────── #

def pipeline_blur_and_wiener() -> None:
    """
    Demonstrate Wiener frequency-domain deconvolution:

        grayscale  →  5×5 Gaussian blur (known PSF)
                   →  light additive Gaussian noise
                   →  Wiener filter with matching PSF (K = 0.005)

    The Sobel edge response before and after deconvolution illustrates recovered
    sharpness.  Metrics against the original cleanly quantify the improvement:
    the restored image should show higher PSNR and SSIM than the blurred input.
    """
    _section("Part 2b — Gaussian Blur & Wiener Deconvolution")

    np.random.seed(0)
    lena = _load_lena_gray()   # full 512×512 — all ops here are FFT-based, so fast

    # (1) Degrade: blur with a known Gaussian PSF, then add a small amount of noise.
    psf_size, psf_sigma = 5, 1.5
    blurred       = blur_image(lena, filter_type='gaussian', filter_size=psf_size,
                               padding_type='zero', sigma=psf_sigma, normalization_method='unchanged')
    noisy_blurred = add_gaussian_noise(blurred, mean=0, sigma=0.01)

    # (2) Recover: Wiener deconvolution with the same PSF used during degradation.
    psf      = generate_filter(filter_type='gaussian', filter_size=psf_size, sigma=psf_sigma)
    restored = wiener_filter(noisy_blurred, psf=psf, k=0.005, normalization_method='stretch')

    # (3) Measure edge sharpness with the Sobel operator.
    edges_blurred  = sobel_filter(blurred,  padding_type='zero', normalization_method='stretch')['Magnitude']
    edges_restored = sobel_filter(restored, padding_type='zero', normalization_method='stretch')['Magnitude']

    # Console: full quality reports.
    _print_comparator("Blurred + Noise vs. Original", lena, noisy_blurred)
    _print_comparator("Wiener Restored vs. Original", lena, restored)

    panels = [
        (lena,           "Original\n(reference)"),
        (noisy_blurred,  f"Blurred + noise  (σ=1.5)\n{_metrics_str(lena, noisy_blurred)}"),
        (restored,       f"Wiener restored  (K=0.005)\n{_metrics_str(lena, restored)}"),
        (edges_blurred,  "Sobel — blurred"),
        (edges_restored, "Sobel — restored"),
    ]

    fig, axes = plt.subplots(1, 5, figsize=(26, 5))
    for ax, (img, label) in zip(axes, panels):
        _imshow(ax, img, label)
    _show("Pipeline 2b — Gaussian Blur + Wiener Deconvolution")


# ──────────────────────────────────────────────────────────── #
# Part 2c — Pipeline: homomorphic illumination correction       #
# ──────────────────────────────────────────────────────────── #

def pipeline_homomorphic() -> None:
    """
    Demonstrate homomorphic filtering for illumination equalisation.

    Lena is artificially degraded with a left-dark / right-bright multiplicative
    illumination ramp (factor 0.3 → 1.0).  The homomorphic filter separates
    illumination (low frequency) from reflectance (high frequency) by working in
    the log domain:

        log(f) = log(illumination) + log(reflectance)

    Setting γ_L = 0.25 < 1 attenuates the slowly-varying illumination component while
    γ_H = 2.0 > 1 boosts the fast-varying reflectance detail, producing a more
    uniformly-lit result.

    Quality metrics are annotated on the histograms; SSIM in particular captures the
    structural recovery that PSNR may understate for illumination-type distortions.
    """
    _section("Part 2c — Homomorphic Illumination Correction")

    lena = _load_lena_gray()
    _height, width = lena.shape

    # Simulate a left-dark / right-bright illumination ramp (factor 0.3 → 1.0).
    illumination = 0.3 + 0.7 * np.linspace(0.0, 1.0, width)[np.newaxis, :]
    degraded     = np.clip(lena * illumination, 0.0, 1.0)

    # Homomorphic filter: suppress illumination, restore reflectance.
    corrected = homomorphic_filter(degraded, gamma_l=0.25, gamma_h=2.0,
                                   c=1.0, sigma=30.0, normalization_method='stretch')

    # Console: quality of degraded and corrected vs. original.
    _print_comparator("Gradient-Degraded vs. Original",    lena, degraded)
    _print_comparator("Homomorphic-Corrected vs. Original", lena, corrected)

    # ── 2-row figure: images (top) + metric-annotated histograms (bottom) ── #
    fig = plt.figure(figsize=(18, 8))

    image_panels = [
        (lena,      "Original Lena\n(reference)"),
        (degraded,  "Gradient illumination\n(0.3 × left  →  1.0 × right)"),
        (corrected, "Homomorphic corrected\n(γ_L=0.25, γ_H=2.0)"),
    ]
    for col, (img, title) in enumerate(image_panels, start=1):
        ax = fig.add_subplot(2, 3, col)
        ax.imshow(img, cmap='gray', vmin=0, vmax=1)
        ax.set_title(title, fontsize=10)
        ax.axis('off')

    bins   = np.linspace(0.0, 1.0, 65)
    colors = ['#4C72B0', '#DD8452', '#55A868']
    hist_images    = [lena,     degraded,  corrected]
    hist_labels    = ["Original", "Degraded", "Corrected"]
    hist_refs      = [lena,     lena,      lena]

    for col, (img, label, ref, color) in enumerate(
            zip(hist_images, hist_labels, hist_refs, colors), start=4):
        ax = fig.add_subplot(2, 3, col)
        ax.hist(img.ravel(), bins=bins, color=color, edgecolor='none', alpha=0.85)
        ax.set_title(f"Histogram — {label}", fontsize=10)
        ax.set_xlabel("Intensity")
        ax.set_ylabel("Count")
        ax.set_xlim(0, 1)

        # Annotate with PSNR and SSIM relative to original.
        p = psnr(ref, img)
        s = ssim(ref, img)
        psnr_fmt = "∞" if p == np.inf else f"{p:.1f} dB"
        annotation = f"PSNR: {psnr_fmt}\nSSIM: {s:.3f}"
        ax.text(0.97, 0.95, annotation,
                transform=ax.transAxes, ha='right', va='top', fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.75, edgecolor='gray'))

    _show("Pipeline 2c — Homomorphic Illumination Correction")


# ──────────────────────────────────────────────────────────── #
# Entry point                                                   #
# ──────────────────────────────────────────────────────────── #

if __name__ == '__main__':
    log.info("Image Processing Demo — Lena")
    log.info("Each figure must be closed to advance to the next showcase.")

    # ── Standalone showcases ──────────────────────────────────────────────── #
    showcase_noise_zoo()
    showcase_frequency_filters()
    showcase_edge_detectors()

    # ── Pipelines ─────────────────────────────────────────────────────────── #
    pipeline_impulse_denoising()
    pipeline_blur_and_wiener()
    pipeline_homomorphic()

    log.info("Demo complete.")
