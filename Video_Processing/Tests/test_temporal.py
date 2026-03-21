# Imports #
import numpy as np
import pytest

from Video_Processing.Source.Advanced.temporal import (
    frame_difference, background_subtraction, temporal_average, motion_detection,
)
from constants import *


# ──────────────────────────────────────────────────────────── #
#  frame_difference tests                                       #
# ──────────────────────────────────────────────────────────── #

def test_frame_difference_output_length():
    """
    Test purpose - frame_difference returns N-1 frames for an N-frame input.
    Criteria - len(output) == len(input) - 1.

    Test steps:
    1) Apply frame_difference to RAMP_VIDEO (N_FRAMES frames).
    2) Assert length of result is N_FRAMES - 1.
    """

    result = frame_difference(RAMP_VIDEO)
    assert len(result) == N_FRAMES - 1


def test_frame_difference_static_video_is_zero():
    """
    Test purpose - Differencing a static (constant) video yields all-zero frames.
    Criteria - Every pixel in every difference frame equals 0.

    Test steps:
    1) Apply frame_difference to STATIC_VIDEO (all frames identical).
    2) Assert every difference frame is all zeros.
    """

    result = frame_difference(STATIC_VIDEO)
    for diff in result:
        np.testing.assert_array_equal(diff, np.zeros((FRAME_H, FRAME_W)))


def test_frame_difference_known_values():
    """
    Test purpose - frame_difference computes |frame[i+1] - frame[i]| correctly.
    Criteria - Difference between the two frames of KNOWN_VIDEO_2F equals |KNOWN_4x4 - (1 - KNOWN_4x4)|
               = |2*KNOWN_4x4 - 1|.

    Test steps:
    1) Apply frame_difference to KNOWN_VIDEO_2F.
    2) Assert the single difference frame equals the expected absolute difference.
    """

    result = frame_difference(KNOWN_VIDEO_2F)
    assert len(result) == 1
    expected = np.abs(KNOWN_VIDEO_2F[1] - KNOWN_VIDEO_2F[0])
    np.testing.assert_array_almost_equal(result[0], expected)


def test_frame_difference_non_negative():
    """
    Test purpose - All pixels in all difference frames are non-negative (absolute values).
    Criteria - min(diff) >= 0 for every difference frame.

    Test steps:
    1) Apply frame_difference to BINARY_ALT_VIDEO.
    2) Assert all pixel values are >= 0.
    """

    result = frame_difference(BINARY_ALT_VIDEO)
    for diff in result:
        assert diff.min() >= 0.0


def test_frame_difference_single_frame_returns_empty():
    """
    Test purpose - frame_difference on a single-frame input returns an empty list.
    Criteria - result == [].

    Test steps:
    1) Apply frame_difference to a one-frame list.
    2) Assert the result is an empty list.
    """

    result = frame_difference([KNOWN_4x4])
    assert result == []


# ──────────────────────────────────────────────────────────── #
#  background_subtraction tests                                 #
# ──────────────────────────────────────────────────────────── #

def test_background_subtraction_output_length():
    """
    Test purpose - background_subtraction returns the same number of frames as the input.
    Criteria - len(output) == len(input).

    Test steps:
    1) Apply background_subtraction to UNIFORM_VIDEO.
    2) Assert length of result equals N_FRAMES.
    """

    result = background_subtraction(UNIFORM_VIDEO)
    assert len(result) == N_FRAMES


def test_background_subtraction_static_video_first_frame_zero():
    """
    Test purpose - For a static video the first foreground frame is always zero
                   (the background is initialised with frame 0, so diff = 0).
    Criteria - result[0] is all zeros.

    Test steps:
    1) Apply background_subtraction to STATIC_VIDEO.
    2) Assert the first result frame is all zeros.
    """

    result = background_subtraction(STATIC_VIDEO)
    np.testing.assert_array_equal(result[0], np.zeros((FRAME_H, FRAME_W)))


def test_background_subtraction_non_negative():
    """
    Test purpose - All foreground mask pixels are non-negative (absolute differences).
    Criteria - min pixel value >= 0 for every output frame.

    Test steps:
    1) Apply background_subtraction to RAMP_VIDEO.
    2) Assert all values are >= 0.
    """

    result = background_subtraction(RAMP_VIDEO)
    for frame in result:
        assert frame.min() >= 0.0


def test_background_subtraction_learning_rate_zero_gives_constant_bg():
    """
    Test purpose - A learning rate of 0 freezes the background at the first frame;
                   the foreground mask for each frame equals |frame - frame[0]|.
    Criteria - result[i] ≈ |RAMP_VIDEO[i] - RAMP_VIDEO[0]| for all i.

    Test steps:
    1) Apply background_subtraction to RAMP_VIDEO with learning_rate=0.
    2) For each frame, assert result matches |frame - first_frame|.
    """

    result = background_subtraction(RAMP_VIDEO, learning_rate=0.0)
    first = RAMP_VIDEO[0]
    for i, (res_frame, orig_frame) in enumerate(zip(result, RAMP_VIDEO)):
        expected = np.abs(orig_frame - first)
        np.testing.assert_array_almost_equal(res_frame, expected,
                                             err_msg=f"Mismatch at frame {i}")


# ──────────────────────────────────────────────────────────── #
#  temporal_average tests                                       #
# ──────────────────────────────────────────────────────────── #

def test_temporal_average_output_length():
    """
    Test purpose - temporal_average returns the same number of frames as the input.
    Criteria - len(output) == len(input).

    Test steps:
    1) Apply temporal_average to RAMP_VIDEO.
    2) Assert output length equals N_FRAMES.
    """

    result = temporal_average(RAMP_VIDEO)
    assert len(result) == N_FRAMES


def test_temporal_average_uniform_video_unchanged():
    """
    Test purpose - Temporal averaging of a uniform video leaves every frame unchanged.
    Criteria - Each output frame equals the original (all 0.5) element-wise.

    Test steps:
    1) Apply temporal_average to UNIFORM_VIDEO.
    2) Assert every output frame equals UNIFORM_VIDEO[0].
    """

    result = temporal_average(UNIFORM_VIDEO)
    for frame in result:
        np.testing.assert_array_almost_equal(frame, UNIFORM_VIDEO[0])


def test_temporal_average_window_one_is_identity():
    """
    Test purpose - A window size of 1 is equivalent to the identity operation.
    Criteria - Every output frame equals the corresponding input frame.

    Test steps:
    1) Apply temporal_average to RAMP_VIDEO with window_size=1.
    2) Assert every output frame equals the original.
    """

    result = temporal_average(RAMP_VIDEO, window_size=1)
    for orig, res in zip(RAMP_VIDEO, result):
        np.testing.assert_array_almost_equal(res, orig)


def test_temporal_average_shape_preserved():
    """
    Test purpose - temporal_average preserves the spatial shape of every frame.
    Criteria - Each output frame has shape (FRAME_H, FRAME_W).

    Test steps:
    1) Apply temporal_average to RAMP_VIDEO.
    2) Assert every output frame has the expected shape.
    """

    result = temporal_average(RAMP_VIDEO)
    for frame in result:
        assert frame.shape == (FRAME_H, FRAME_W)


# ──────────────────────────────────────────────────────────── #
#  motion_detection tests                                       #
# ──────────────────────────────────────────────────────────── #

def test_motion_detection_output_length():
    """
    Test purpose - motion_detection returns N-1 binary frames for an N-frame input.
    Criteria - len(output) == len(input) - 1.

    Test steps:
    1) Apply motion_detection to RAMP_VIDEO.
    2) Assert length of result is N_FRAMES - 1.
    """

    result = motion_detection(RAMP_VIDEO)
    assert len(result) == N_FRAMES - 1


def test_motion_detection_binary_output():
    """
    Test purpose - Every pixel in a motion mask is either 0 or 1.
    Criteria - All values are in {0, 1}.

    Test steps:
    1) Apply motion_detection to BINARY_ALT_VIDEO.
    2) Assert all pixel values are 0 or 1.
    """

    result = motion_detection(BINARY_ALT_VIDEO)
    for mask in result:
        unique = np.unique(mask)
        for v in unique:
            assert v in (0.0, 1.0), f"Unexpected pixel value: {v}"


def test_motion_detection_static_video_no_motion():
    """
    Test purpose - A static video produces all-zero (no-motion) masks below any threshold.
    Criteria - All pixels in every mask are 0.

    Test steps:
    1) Apply motion_detection to STATIC_VIDEO with a threshold of 0.01.
    2) Assert every mask is all zeros.
    """

    result = motion_detection(STATIC_VIDEO, threshold=0.01)
    for mask in result:
        np.testing.assert_array_equal(mask, np.zeros((FRAME_H, FRAME_W)))


def test_motion_detection_alternating_video_full_motion():
    """
    Test purpose - An alternating (0/1) video produces all-ones motion masks.
    Criteria - Every pixel in every mask equals 1 when the threshold is 0.5.

    Test steps:
    1) Apply motion_detection to BINARY_ALT_VIDEO with threshold=0.5.
    2) Assert every mask is all ones.
    """

    result = motion_detection(BINARY_ALT_VIDEO, threshold=0.5)
    for mask in result:
        np.testing.assert_array_equal(mask, np.ones((FRAME_H, FRAME_W)))
