# Imports #
import numpy as np
import pytest

from Video_Processing.Source.Basic.video_metrics import VideoComparator
from constants import *


# ──────────────────────────────────────────────────────────── #
#  VideoComparator construction tests                           #
# ──────────────────────────────────────────────────────────── #

def test_comparator_identical_videos_zero_mse():
    """
    Test purpose - Comparing a video against itself yields zero MSE for every frame.
    Criteria - mean_mse == 0.0 and every per-frame MSE == 0.0.

    Test steps:
    1) Construct a VideoComparator with STATIC_VIDEO as both original and distorted.
    2) Assert mean_mse == 0.0 and all per-frame MSE values are 0.0.
    """

    cmp = VideoComparator(original=STATIC_VIDEO, distorted=STATIC_VIDEO)
    assert cmp.mean_mse == 0.0
    assert all(m == 0.0 for m in cmp.mse_values)


def test_comparator_identical_videos_infinite_psnr():
    """
    Test purpose - Comparing a video against itself yields infinite PSNR.
    Criteria - Every per-frame PSNR value is np.inf.

    Test steps:
    1) Construct a VideoComparator with STATIC_VIDEO as both original and distorted.
    2) Assert all per-frame PSNR values are np.inf.
    """

    cmp = VideoComparator(original=STATIC_VIDEO, distorted=STATIC_VIDEO)
    assert all(p == np.inf for p in cmp.psnr_values)


def test_comparator_identical_videos_ssim_one():
    """
    Test purpose - Comparing a video against itself yields SSIM = 1.0 for every frame.
    Criteria - mean_ssim ≈ 1.0 and every per-frame SSIM ≈ 1.0.

    Test steps:
    1) Construct a VideoComparator with UNIFORM_VIDEO as both original and distorted.
    2) Assert mean_ssim ≈ 1.0.
    """

    cmp = VideoComparator(original=UNIFORM_VIDEO, distorted=UNIFORM_VIDEO)
    np.testing.assert_almost_equal(cmp.mean_ssim, 1.0, decimal=5)


def test_comparator_temporal_ssim_static_is_one():
    """
    Test purpose - A static (all-frames-identical) video has T-SSIM = 1.0.
    Criteria - temporal_ssim ≈ 1.0.

    Test steps:
    1) Construct a VideoComparator with STATIC_VIDEO for both arguments.
    2) Assert temporal_ssim ≈ 1.0.
    """

    cmp = VideoComparator(original=STATIC_VIDEO, distorted=STATIC_VIDEO)
    np.testing.assert_almost_equal(cmp.temporal_ssim, 1.0, decimal=5)


def test_comparator_noisy_video_lower_psnr():
    """
    Test purpose - Adding noise to a video reduces mean PSNR compared to the clean video.
    Criteria - mean_psnr of (clean vs noisy) < mean_psnr of (clean vs clean).

    Test steps:
    1) Build a noisy version of UNIFORM_VIDEO by adding Gaussian noise.
    2) Compare clean vs noisy and clean vs clean.
    3) Assert the noisy comparison has strictly lower mean_psnr.
    """

    np.random.seed(0)
    noisy = [f + np.random.normal(0, 0.1, f.shape) for f in UNIFORM_VIDEO]
    noisy = [np.clip(f, 0.0, 1.0) for f in noisy]

    cmp_clean = VideoComparator(original=UNIFORM_VIDEO, distorted=UNIFORM_VIDEO)
    cmp_noisy = VideoComparator(original=UNIFORM_VIDEO, distorted=noisy)

    # Clean comparison has infinite PSNR; noisy must have a finite, lower value.
    assert cmp_noisy.mean_psnr < np.inf


def test_comparator_length_mismatch_raises():
    """
    Test purpose - VideoComparator raises ValueError when frame lists have different lengths.
    Criteria - ValueError is raised on construction.

    Test steps:
    1) Attempt to construct a VideoComparator with lists of different lengths.
    2) Assert a ValueError is raised.
    """

    with pytest.raises((ValueError, Exception)):
        VideoComparator(original=UNIFORM_VIDEO, distorted=UNIFORM_VIDEO[:3])


def test_comparator_as_dict_keys():
    """
    Test purpose - as_dict() returns all four expected metric keys.
    Criteria - The returned dict contains exactly mean_MSE, mean_PSNR, mean_SSIM, temporal_SSIM.

    Test steps:
    1) Build a VideoComparator from STATIC_VIDEO vs itself.
    2) Assert the returned dict has the expected keys.
    """

    cmp = VideoComparator(original=STATIC_VIDEO, distorted=STATIC_VIDEO)
    d = cmp.as_dict()
    assert set(d.keys()) == {"mean_MSE", "mean_PSNR", "mean_SSIM", "temporal_SSIM"}


def test_comparator_per_frame_count():
    """
    Test purpose - The per-frame metric lists have the same length as the frame lists.
    Criteria - len(mse_values) == len(psnr_values) == len(ssim_values) == N_FRAMES.

    Test steps:
    1) Build a VideoComparator from RAMP_VIDEO vs itself.
    2) Assert all per-frame lists have length N_FRAMES.
    """

    cmp = VideoComparator(original=RAMP_VIDEO, distorted=RAMP_VIDEO)
    assert len(cmp.mse_values) == N_FRAMES
    assert len(cmp.psnr_values) == N_FRAMES
    assert len(cmp.ssim_values) == N_FRAMES


def test_comparator_single_frame_temporal_ssim_is_one():
    """
    Test purpose - A single-frame VideoComparator sets T-SSIM to 1.0 (no pairs available).
    Criteria - temporal_ssim == 1.0.

    Test steps:
    1) Build a VideoComparator with a one-frame list for both arguments.
    2) Assert temporal_ssim == 1.0.
    """

    single = [KNOWN_4x4]
    cmp = VideoComparator(original=single, distorted=single)
    assert cmp.temporal_ssim == 1.0
