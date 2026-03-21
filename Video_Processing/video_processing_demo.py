"""
Script Name - video_processing_demo.py

Purpose - Demonstrate the Video Processing module on synthetic video sequences.
          No external video file is required — every demo builds its own test footage
          from numpy arrays so the script runs stand-alone.

Structure
---------
Part 1 – Per-frame operations (showcase each image-processing category on video)
    1a. Intensity transformations  – negative, gamma correction
    1b. Spatial filtering          – Gaussian blur, Sobel edge detection
    1c. Noise & restoration        – S&P corruption → median filter (per frame)

Part 2 – Temporal operations (algorithms unique to video)
    2a. Frame difference           – temporal derivative of a moving ramp
    2b. Background subtraction     – isolate a foreground object
    2c. Motion detection           – binary masks from alternating content
    2d. Temporal averaging         – de-noising along the time axis

Part 3 – Video quality metrics
    3a. VideoComparator report     – MSE, PSNR, SSIM, T-SSIM on noisy video
    3b. T-SSIM degradation demo    – per-frame processing induces temporal inconsistency

Created by Michael Samelsohn, 21/03/26.
"""

# Imports #
import numpy as np
import matplotlib.pyplot as plt

from Image_Processing.Source.Advanced.noise_models import add_salt_and_pepper, add_gaussian_noise
from Image_Processing.Source.Advanced.restoration import order_statistic_filter
from Image_Processing.Source.Advanced.intensity_transformations import negative, gamma_correction
from Image_Processing.Source.Advanced.spatial_filtering import blur_image, sobel_filter

from Video_Processing.Source.Advanced.frame_operations import apply_per_frame
from Video_Processing.Source.Advanced.temporal import (
    frame_difference, background_subtraction, temporal_average, motion_detection,
)
from Video_Processing.Source.Basic.video_metrics import VideoComparator
from settings import log


# ──────────────────────────────────────────────────────────── #
# Synthetic video factories                                     #
# ──────────────────────────────────────────────────────────── #

def _make_ramp_video(n_frames: int = 10, h: int = 64, w: int = 64) -> list[np.ndarray]:
    """
    Generate a grayscale video whose mean intensity ramps linearly from 0 to 1.
    Each frame is a spatially uniform image at a different brightness level.
    """
    return [np.full((h, w), i / max(n_frames - 1, 1), dtype=float) for i in range(n_frames)]


def _make_moving_disc_video(n_frames: int = 12, h: int = 64, w: int = 64) -> list[np.ndarray]:
    """
    Generate a grayscale video with a bright disc moving horizontally across a dark background.
    """
    frames = []
    radius = 8
    center_y = h // 2
    x_positions = np.linspace(radius + 2, w - radius - 2, n_frames).astype(int)

    for cx in x_positions:
        frame = np.zeros((h, w), dtype=float)
        ys, xs = np.ogrid[:h, :w]
        mask = (xs - cx) ** 2 + (ys - center_y) ** 2 <= radius ** 2
        frame[mask] = 1.0
        frames.append(frame)

    return frames


def _make_static_bg_video(n_frames: int = 10, h: int = 64, w: int = 64) -> list[np.ndarray]:
    """
    Generate a video with a static textured background and a moving foreground patch.
    """
    np.random.seed(1)
    bg = np.random.uniform(0.3, 0.5, (h, w))
    frames = []
    patch_size = 10

    for i in range(n_frames):
        frame = bg.copy()
        x = int(5 + (w - patch_size - 10) * i / max(n_frames - 1, 1))
        y = h // 2 - patch_size // 2
        frame[y:y + patch_size, x:x + patch_size] = 0.9
        frames.append(frame)

    return frames


# ──────────────────────────────────────────────────────────── #
# Display helpers                                               #
# ──────────────────────────────────────────────────────────── #

def _show_strip(frames: list[np.ndarray], title: str,
                indices: list[int] = None, n_samples: int = 6) -> None:
    """Display a horizontal strip of evenly-sampled frames with a suptitle."""

    if indices is None:
        step = max(1, len(frames) // n_samples)
        indices = list(range(0, len(frames), step))[:n_samples]

    fig, axes = plt.subplots(1, len(indices), figsize=(2.5 * len(indices), 3))
    if len(indices) == 1:
        axes = [axes]

    for ax, i in zip(axes, indices):
        frame = frames[i]
        ax.imshow(frame, cmap='gray', vmin=0, vmax=1)
        ax.set_title(f"t={i}", fontsize=8)
        ax.axis('off')

    plt.suptitle(title, fontsize=11, fontweight='bold')
    plt.tight_layout()
    plt.show()


def _show_comparison_strip(frames_a: list[np.ndarray], label_a: str,
                            frames_b: list[np.ndarray], label_b: str,
                            title: str, n_samples: int = 5) -> None:
    """Display two rows of frames for before/after comparison."""

    step = max(1, len(frames_a) // n_samples)
    indices = list(range(0, len(frames_a), step))[:n_samples]
    # Clamp indices for frames_b which may be shorter (e.g. after frame_difference).
    indices_b = [min(i, len(frames_b) - 1) for i in indices]

    fig, axes = plt.subplots(2, len(indices), figsize=(2.5 * len(indices), 5))

    for col, (ia, ib) in enumerate(zip(indices, indices_b)):
        for row, (frames, lbl, idx) in enumerate([(frames_a, label_a, ia),
                                                   (frames_b, label_b, ib)]):
            ax = axes[row, col]
            ax.imshow(frames[idx], cmap='gray', vmin=0, vmax=1)
            ax.set_title(f"t={idx}", fontsize=7)
            ax.axis('off')
        axes[0, col].set_title(f"{label_a}  t={ia}", fontsize=7)
        axes[1, col].set_title(f"{label_b}  t={ib}", fontsize=7)

    plt.suptitle(title, fontsize=11, fontweight='bold')
    plt.tight_layout()
    plt.show()


def _section(label: str) -> None:
    log.info(f"{'─' * 60}")
    log.info(label)
    log.info(f"{'─' * 60}")


# ──────────────────────────────────────────────────────────── #
# Part 1a — Intensity transformations                          #
# ──────────────────────────────────────────────────────────── #

def showcase_intensity_transformations() -> None:
    """
    Apply negative and gamma correction to every frame of a ramp video.

    The ramp video increases brightness from 0 to 1 across frames, making the
    per-frame effect of each transformation clearly visible in the strip.
    """

    _section("Part 1a — Intensity Transformations (ramp video)")

    frames = _make_ramp_video(n_frames=10)

    negated = apply_per_frame(frames, negative)
    gamma_dark = apply_per_frame(frames, gamma_correction, gamma=2.0)
    gamma_bright = apply_per_frame(frames, gamma_correction, gamma=0.5)

    _show_strip(frames, "Original ramp video")
    _show_strip(negated, "Negative (per-frame)")
    _show_strip(gamma_dark, "Gamma correction γ=2.0 (per-frame, darkening)")
    _show_strip(gamma_bright, "Gamma correction γ=0.5 (per-frame, brightening)")


# ──────────────────────────────────────────────────────────── #
# Part 1b — Spatial filtering                                  #
# ──────────────────────────────────────────────────────────── #

def showcase_spatial_filtering() -> None:
    """
    Apply Gaussian blur and Sobel edge detection to every frame of the moving-disc video.

    Sobel returns a dict; the 'Magnitude' entry is extracted for display.
    """

    _section("Part 1b — Spatial Filtering (moving disc video)")

    frames = _make_moving_disc_video(n_frames=10)

    blurred = apply_per_frame(frames, blur_image,
                               filter_type='gaussian', filter_size=5,
                               padding_type='zero', sigma=1.5,
                               normalization_method='unchanged')

    sobel_results = apply_per_frame(frames, sobel_filter,
                                     padding_type='zero',
                                     normalization_method='stretch')
    # sobel_filter returns a dict; extract the magnitude map from each frame.
    sobel_mag = [r['Magnitude'] for r in sobel_results]

    _show_strip(frames,    "Moving disc — original")
    _show_strip(blurred,   "Moving disc — Gaussian blur (per-frame)")
    _show_strip(sobel_mag, "Moving disc — Sobel magnitude (per-frame)")


# ──────────────────────────────────────────────────────────── #
# Part 1c — Noise & restoration                                #
# ──────────────────────────────────────────────────────────── #

def showcase_noise_and_restoration() -> None:
    """
    Corrupt each frame with salt-and-pepper noise and restore with a per-frame median filter.
    Metrics before and after restoration are printed to the console.
    """

    _section("Part 1c — Noise & Restoration (moving disc video)")

    np.random.seed(42)
    frames = _make_moving_disc_video(n_frames=8)

    noisy = apply_per_frame(frames, add_salt_and_pepper, pepper=0.05, salt=0.05)
    restored = apply_per_frame(noisy, order_statistic_filter,
                                filter_type='median', padding_type='mirror', filter_size=3)

    cmp_noisy = VideoComparator(original=frames, distorted=noisy)
    cmp_restored = VideoComparator(original=frames, distorted=restored)

    log.info("Metrics — Noisy vs. Clean")
    cmp_noisy.print()
    log.info("Metrics — Median-Restored vs. Clean")
    cmp_restored.print()

    _show_comparison_strip(noisy, "Noisy (S&P 5%+5%)", restored, "Median restored",
                            title="Part 1c — Noise & Restoration", n_samples=5)


# ──────────────────────────────────────────────────────────── #
# Part 2a — Frame difference                                    #
# ──────────────────────────────────────────────────────────── #

def showcase_frame_difference() -> None:
    """
    Compute and display the temporal first derivative of the moving-disc video.

    Each difference frame shows where pixels changed between two consecutive frames.
    The bright ring traces the disc's trajectory.
    """

    _section("Part 2a — Frame Difference (moving disc video)")

    frames = _make_moving_disc_video(n_frames=10)
    diffs = frame_difference(frames)

    _show_strip(frames, "Moving disc — original")
    _show_strip(diffs,  "Frame differences  (N-1 frames)")


# ──────────────────────────────────────────────────────────── #
# Part 2b — Background subtraction                             #
# ──────────────────────────────────────────────────────────── #

def showcase_background_subtraction() -> None:
    """
    Separate the moving foreground patch from a static textured background.

    A running-average background model with a small learning rate suppresses the
    slowly-varying background while highlighting the moving patch.
    """

    _section("Part 2b — Background Subtraction")

    frames = _make_static_bg_video(n_frames=10)
    fg_masks = background_subtraction(frames, learning_rate=0.05)

    _show_comparison_strip(frames, "Input", fg_masks, "Foreground mask",
                            title="Part 2b — Background Subtraction", n_samples=5)


# ──────────────────────────────────────────────────────────── #
# Part 2c — Motion detection                                    #
# ──────────────────────────────────────────────────────────── #

def showcase_motion_detection() -> None:
    """
    Produce binary motion masks from the moving-disc video.

    Pixels that changed by more than the threshold between consecutive frames are
    marked 1 (motion); all others are 0 (static).
    """

    _section("Part 2c — Motion Detection (moving disc video)")

    frames = _make_moving_disc_video(n_frames=10)
    masks = motion_detection(frames, threshold=0.3)

    log.info(f"Motion detection: {len(masks)} binary mask(s) from {len(frames)} frame(s)")
    for i, mask in enumerate(masks):
        log.info(f"  Mask {i}: {mask.mean() * 100:.1f}% pixels in motion")

    _show_strip(frames, "Moving disc — original")
    _show_strip(masks,  "Motion masks  (threshold=0.3)")


# ──────────────────────────────────────────────────────────── #
# Part 2d — Temporal averaging                                  #
# ──────────────────────────────────────────────────────────── #

def showcase_temporal_averaging() -> None:
    """
    De-noise a video along the time axis using a sliding temporal window.

    Gaussian noise is added independently to each frame (simulating sensor noise).
    Temporal averaging across 5 frames suppresses the per-frame noise without a
    spatial blur, at the cost of slight temporal smearing.

    Metrics quantify the SNR improvement over the noisy baseline.
    """

    _section("Part 2d — Temporal Averaging (noisy ramp video)")

    np.random.seed(7)
    frames = _make_ramp_video(n_frames=20)
    noisy = apply_per_frame(frames, add_gaussian_noise, mean=0, sigma=0.1)
    smoothed = temporal_average(noisy, window_size=5)

    cmp_noisy = VideoComparator(original=frames, distorted=noisy)
    cmp_smoothed = VideoComparator(original=frames, distorted=smoothed)

    log.info("Metrics — Noisy vs. Clean")
    cmp_noisy.print()
    log.info("Metrics — Temporally Averaged vs. Clean")
    cmp_smoothed.print()

    _show_comparison_strip(noisy, "Noisy", smoothed, "Temporal average (w=5)",
                            title="Part 2d — Temporal Averaging", n_samples=6)


# ──────────────────────────────────────────────────────────── #
# Part 3a — VideoComparator full report                         #
# ──────────────────────────────────────────────────────────── #

def showcase_video_comparator() -> None:
    """
    Demonstrate VideoComparator on a clean vs. Gaussian-noisy moving-disc video.

    Prints the full MSE / PSNR / SSIM / T-SSIM report to the console and displays
    a bar chart of per-frame PSNR to visualise temporal quality variation.
    """

    _section("Part 3a — VideoComparator Quality Report")

    np.random.seed(0)
    frames = _make_moving_disc_video(n_frames=12)
    noisy = apply_per_frame(frames, add_gaussian_noise, mean=0, sigma=0.05)

    cmp = VideoComparator(original=frames, distorted=noisy)
    cmp.print()

    finite_psnr = [p if p != np.inf else 0.0 for p in cmp.psnr_values]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(range(len(finite_psnr)), finite_psnr, color='steelblue')
    ax.set_xlabel("Frame index")
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("Per-frame PSNR — clean vs. Gaussian noise (σ=0.05)")
    ax.axhline(cmp.mean_psnr, color='tomato', linestyle='--',
               label=f"Mean PSNR = {cmp.mean_psnr:.2f} dB")
    ax.legend()
    plt.tight_layout()
    plt.show()


# ──────────────────────────────────────────────────────────── #
# Part 3b — T-SSIM degradation demo                            #
# ──────────────────────────────────────────────────────────── #

def showcase_temporal_ssim() -> None:
    """
    Show how independent per-frame processing can reduce temporal consistency (T-SSIM).

    A static video has T-SSIM = 1.0.  After adding independent Gaussian noise to each
    frame, consecutive frames differ randomly and T-SSIM drops.  Temporal averaging
    partially recovers consistency.
    """

    _section("Part 3b — Temporal SSIM (T-SSIM) Degradation Demo")

    np.random.seed(3)
    clean = _make_static_bg_video(n_frames=15)

    noisy = apply_per_frame(clean, add_gaussian_noise, mean=0, sigma=0.1)
    smoothed = temporal_average(noisy, window_size=5)

    cmp_clean   = VideoComparator(original=clean, distorted=clean)
    cmp_noisy   = VideoComparator(original=clean, distorted=noisy)
    cmp_smoothed = VideoComparator(original=clean, distorted=smoothed)

    labels = ["Clean (reference)", "Noisy (σ=0.1)", "Temporally averaged (w=5)"]
    tssim_values = [cmp_clean.temporal_ssim,
                    cmp_noisy.temporal_ssim,
                    cmp_smoothed.temporal_ssim]

    log.info("T-SSIM comparison:")
    for label, val in zip(labels, tssim_values):
        log.info(f"  {label:<30}: T-SSIM = {val:.4f}")

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ['#55A868', '#DD8452', '#4C72B0']
    bars = ax.bar(labels, tssim_values, color=colors)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("T-SSIM (temporal consistency)")
    ax.set_title("Part 3b — Temporal SSIM: Effect of Noise & Averaging")
    for bar, val in zip(bars, tssim_values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.01,
                f"{val:.3f}", ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    plt.show()


# ──────────────────────────────────────────────────────────── #
# Entry point                                                   #
# ──────────────────────────────────────────────────────────── #

if __name__ == '__main__':
    log.info("Video Processing Demo")
    log.info("Each figure must be closed to advance to the next showcase.")

    # ── Part 1: Per-frame operations ──────────────────────────────────────── #
    showcase_intensity_transformations()
    showcase_spatial_filtering()
    showcase_noise_and_restoration()

    # ── Part 2: Temporal operations ───────────────────────────────────────── #
    showcase_frame_difference()
    showcase_background_subtraction()
    showcase_motion_detection()
    showcase_temporal_averaging()

    # ── Part 3: Quality metrics ───────────────────────────────────────────── #
    showcase_video_comparator()
    showcase_temporal_ssim()

    log.info("Demo complete.")
