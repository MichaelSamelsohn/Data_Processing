"""
Script Name - video_metrics.py

Purpose - Video quality metrics for evaluating the fidelity of a processed video relative
          to a clean reference, extending the single-image metrics in
          Image_Processing.Source.Basic.metrics to the temporal domain.

          Metrics provided:
              Per-frame    – MSE, PSNR, SSIM computed independently on each frame pair.
              Aggregated   – mean MSE, mean PSNR, mean SSIM across all frames.
              Temporal     – Temporal SSIM (T-SSIM): SSIM between consecutive output frames,
                             measuring inter-frame consistency and quantifying flickering.

Created by Michael Samelsohn, 21/03/26.
"""

# Imports #
import numpy as np
from numpy import ndarray

from Image_Processing.Source.Basic.metrics import psnr, ssim
from Video_Processing.Settings.video_settings import *


class VideoComparator:
    """
    Compute and display full-reference quality metrics for an original / distorted video pair.

    Three classes of metrics are evaluated on construction and cached:

    Per-frame metrics (list, one value per frame pair):
        MSE   – mean squared pixel error between each original/distorted frame pair.
        PSNR  – peak signal-to-noise ratio (dB) for each frame pair.
        SSIM  – structural similarity for each frame pair.

    Aggregated metrics (scalar, averaged across all frames):
        mean_mse    – arithmetic mean of per-frame MSE values.
        mean_psnr   – arithmetic mean of finite per-frame PSNR values.
        mean_ssim   – arithmetic mean of per-frame SSIM values.

    Temporal consistency metric:
        temporal_ssim – mean SSIM between consecutive frames of the *distorted* video.
                        A value close to 1 indicates smooth, flicker-free output; lower
                        values reveal temporal instability introduced by frame-wise processing.

    Usage:
        cmp = VideoComparator(original=clean_frames, distorted=processed_frames)
        cmp.print()

        ┌──────────────────────────────────────────────┐
        │  Frames    : 30                              │
        │  Mean MSE  : 0.001234                        │
        │  Mean PSNR : 29.08 dB                        │
        │  Mean SSIM : 0.8741                          │
        │  T-SSIM    : 0.9563  (temporal consistency)  │
        └──────────────────────────────────────────────┘
    """

    def __init__(self, original: list[ndarray], distorted: list[ndarray]) -> None:
        """
        :param original:  List of clean reference frames, pixel values in [0, 1].
        :param distorted: List of processed/degraded frames; must be the same length and
                          shape as original.
        """

        log.info(f"VideoComparator: evaluating {len(original)} frame pair(s)")

        if len(original) != len(distorted):
            log.raise_exception(
                message=f"Frame-list lengths differ: original={len(original)}, "
                        f"distorted={len(distorted)}.",
                exception=ValueError)

        if original[0].shape != distorted[0].shape:
            log.raise_exception(
                message=f"Frame shapes differ: original={original[0].shape}, "
                        f"distorted={distorted[0].shape}.",
                exception=ValueError)

        # ── Per-frame metrics ────────────────────────────────────────────────── #
        log.debug("Computing per-frame MSE and PSNR")
        per_frame_psnr = [psnr(o, d) for o, d in zip(original, distorted)]
        self.mse_values: list[float] = [m for m, _ in per_frame_psnr]
        self.psnr_values: list[float] = [p for _, p in per_frame_psnr]

        log.debug("Computing per-frame SSIM")
        self.ssim_values: list[float] = [ssim(o, d) for o, d in zip(original, distorted)]

        # ── Aggregated metrics ───────────────────────────────────────────────── #
        self.mean_mse: float = float(np.mean(self.mse_values))

        finite_psnr = [p for p in self.psnr_values if p != np.inf]
        self.mean_psnr: float = float(np.mean(finite_psnr)) if finite_psnr else np.inf

        self.mean_ssim: float = float(np.mean(self.ssim_values))

        # ── Temporal consistency (T-SSIM) ────────────────────────────────────── #
        log.debug("Computing temporal SSIM (T-SSIM) on distorted sequence")
        if len(distorted) >= 2:
            self.temporal_ssim: float = float(np.mean([
                ssim(distorted[i], distorted[i + 1])
                for i in range(len(distorted) - 1)
            ]))
        else:
            log.warning("Only one frame — T-SSIM set to 1.0 (no consecutive pairs)")
            self.temporal_ssim = 1.0

        log.info(f"VideoComparator: mean PSNR={self.mean_psnr:.2f} dB, "
                 f"mean SSIM={self.mean_ssim:.4f}, T-SSIM={self.temporal_ssim:.4f}")

    # ── Formatted output ──────────────────────────────────────────────────── #

    def report(self) -> str:
        """
        Build and return the formatted quality report as a multi-line string.

        The box width adapts to the longest row so that values are never truncated.
        """

        psnr_str = "∞ dB" if self.mean_psnr == np.inf else f"{self.mean_psnr:.2f} dB"

        rows = [
            f"  {'Frames':<10}: {len(self.mse_values)}",
            f"  {'Mean MSE':<10}: {self.mean_mse:.6f}",
            f"  {'Mean PSNR':<10}: {psnr_str}",
            f"  {'Mean SSIM':<10}: {self.mean_ssim:.4f}",
            f"  {'T-SSIM':<10}: {self.temporal_ssim:.4f}  (temporal consistency)",
        ]

        inner_width = max(46, max(len(r) for r in rows) + 2)
        top    = "┌" + "─" * inner_width + "┐"
        bottom = "└" + "─" * inner_width + "┘"
        body   = "\n".join(f"│{row:<{inner_width}}│" for row in rows)

        return "\n".join([top, body, bottom])

    def print(self) -> None:
        """Print the formatted quality report to stdout."""
        log.print_data(data=self.report(), log_level="info")

    # ── Data access ───────────────────────────────────────────────────────── #

    def as_dict(self) -> dict:
        """Return the aggregated metric values as a plain dictionary."""
        return {
            "mean_MSE":      self.mean_mse,
            "mean_PSNR":     self.mean_psnr,
            "mean_SSIM":     self.mean_ssim,
            "temporal_SSIM": self.temporal_ssim,
        }

    def __repr__(self) -> str:
        psnr_str = "inf" if self.mean_psnr == np.inf else f"{self.mean_psnr:.2f}"
        return (f"VideoComparator("
                f"frames={len(self.mse_values)}, "
                f"mean_MSE={self.mean_mse:.6f}, "
                f"mean_PSNR={psnr_str} dB, "
                f"mean_SSIM={self.mean_ssim:.4f}, "
                f"T-SSIM={self.temporal_ssim:.4f})")
