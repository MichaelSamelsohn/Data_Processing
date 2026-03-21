"""
Script Name - temporal.py

Purpose - Video-specific temporal processing algorithms that operate across the time axis of a
          frame sequence. These operations have no single-image equivalent and complement the
          per-frame wrappers in frame_operations.py.

          Algorithms provided:
              * frame_difference       – absolute first-order temporal derivative.
              * background_subtraction – running-average foreground separation.
              * temporal_average       – sliding-window temporal smoothing.
              * motion_detection       – binary motion masks from frame differences.

Created by Michael Samelsohn, 21/03/26.
"""

# Imports #
import numpy as np
from numpy import ndarray

from Video_Processing.Settings.video_settings import *


def frame_difference(frames: list[ndarray]) -> list[ndarray]:
    """
    Compute the absolute pixel-wise difference between consecutive frames.

    The result is the discrete temporal first derivative of the frame sequence.  A bright
    pixel in the output indicates a large change at that spatial location between the two
    surrounding frames, making this operation useful for quickly identifying motion.

    Note: Returns N-1 frames for an input of N frames.  The caller should be aware that the
    output video is one frame shorter than the input.

    :param frames: List of N frames in [0, 1].

    :return: List of N-1 difference frames, each normalised to [0, 1].
    """

    log.info(f"Computing frame differences for {len(frames)} frame(s)")

    if len(frames) < 2:
        log.warning("frame_difference requires at least 2 frames; returning empty list")
        return []

    result = []
    for i in range(len(frames) - 1):
        diff = np.abs(frames[i + 1].astype(float) - frames[i].astype(float))
        result.append(diff)
        log.debug(f"Frame diff {i} → {i + 1}: max={diff.max():.4f}, mean={diff.mean():.4f}")

    return result


def background_subtraction(frames: list[ndarray],
                            learning_rate: float = DEFAULT_BG_LEARNING_RATE) -> list[ndarray]:
    """
    Separate foreground from a slowly-varying background using a running-average model.

    The background estimate is initialised with the first frame and updated after each
    frame via an exponential moving average:

        bg_new = (1 − α) · bg_old + α · frame

    The foreground mask for each frame is the absolute difference between the frame and
    the current background estimate.  High pixel values in the mask indicate pixels that
    deviate significantly from the learned background.

    :param frames:        List of N frames in [0, 1].
    :param learning_rate: Background update rate α ∈ (0, 1].  Smaller values make the
                          background more stable (slower adaptation); larger values allow
                          the background to track gradual scene changes.

    :return: List of N foreground-mask frames in [0, 1].
    """

    log.info(f"Running background subtraction on {len(frames)} frame(s) (α={learning_rate})")

    if not frames:
        log.warning("background_subtraction received an empty frame list")
        return []

    bg = frames[0].astype(float)
    result = []

    for i, frame in enumerate(frames):
        f = frame.astype(float)
        foreground = np.abs(f - bg)
        result.append(foreground)
        bg = (1.0 - learning_rate) * bg + learning_rate * f
        log.debug(f"Frame {i}: foreground max={foreground.max():.4f}, bg updated")

    return result


def temporal_average(frames: list[ndarray],
                     window_size: int = DEFAULT_TEMPORAL_WINDOW) -> list[ndarray]:
    """
    Smooth the frame sequence by replacing each frame with the mean of a sliding temporal window.

    For frame i, the window spans [i − ⌊w/2⌋, i + ⌊w/2⌋] (inclusive), clamped to the
    sequence boundaries — no zero-padding is applied at the edges.  This effectively acts
    as a low-pass filter along the time axis, attenuating high-frequency temporal noise
    (e.g., camera sensor noise or compression artefacts) while preserving slowly-changing
    content.

    :param frames:      List of N frames in [0, 1].
    :param window_size: Number of frames in the averaging window (odd value recommended).

    :return: List of N smoothed frames in [0, 1].
    """

    log.info(f"Applying temporal averaging to {len(frames)} frame(s) (window={window_size})")

    if not frames:
        log.warning("temporal_average received an empty frame list")
        return []

    n = len(frames)
    half = window_size // 2
    result = []

    for i in range(n):
        start = max(0, i - half)
        end = min(n, i + half + 1)
        window = frames[start:end]
        averaged = np.mean(np.stack(window, axis=0), axis=0)
        result.append(averaged)
        log.debug(f"Frame {i}: averaged over frames [{start}, {end - 1}]")

    return result


def motion_detection(frames: list[ndarray],
                     threshold: float = DEFAULT_DIFF_THRESHOLD) -> list[ndarray]:
    """
    Produce binary motion masks by thresholding frame-to-frame differences.

    A pixel is marked as motion (value 1) when the absolute change between consecutive
    frames exceeds the threshold; static pixels are set to 0.  The result is useful for
    downstream tasks such as region-of-interest extraction, event detection, or activity
    classification.

    Note: Returns N-1 binary frames for an input of N frames.

    :param frames:    List of N frames in [0, 1].
    :param threshold: Minimum pixel change (in [0, 1]) required to be classified as motion.

    :return: List of N-1 binary frames (values 0 or 1).
    """

    log.info(f"Detecting motion in {len(frames)} frame(s) (threshold={threshold})")

    diffs = frame_difference(frames)
    masks = [(diff > threshold).astype(float) for diff in diffs]

    for i, mask in enumerate(masks):
        motion_ratio = mask.mean()
        log.debug(f"Motion mask {i}: {motion_ratio * 100:.1f}% of pixels in motion")

    return masks
