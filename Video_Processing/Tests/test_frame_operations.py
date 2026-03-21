# Imports #
import numpy as np
import pytest

from Image_Processing.Source.Advanced.intensity_transformations import negative, gamma_correction
from Image_Processing.Source.Advanced.spatial_filtering import blur_image
from Image_Processing.Source.Basic.common import convert_to_grayscale
from Video_Processing.Source.Advanced.frame_operations import apply_per_frame, stack_frames, unstack_frames
from constants import *


# ──────────────────────────────────────────────────────────── #
#  apply_per_frame tests                                        #
# ──────────────────────────────────────────────────────────── #

def test_apply_per_frame_preserves_length():
    """
    Test purpose - apply_per_frame returns the same number of frames as the input.
    Criteria - Output list length equals input list length.

    Test steps:
    1) Apply negative to UNIFORM_VIDEO via apply_per_frame.
    2) Assert that the output has the same number of frames.
    """

    result = apply_per_frame(UNIFORM_VIDEO, negative)
    assert len(result) == len(UNIFORM_VIDEO)


def test_apply_per_frame_preserves_shape():
    """
    Test purpose - apply_per_frame preserves the spatial shape of every frame.
    Criteria - Every output frame has the same (H, W) shape as the input frames.

    Test steps:
    1) Apply negative to UNIFORM_VIDEO.
    2) Assert every output frame shape matches (FRAME_H, FRAME_W).
    """

    result = apply_per_frame(UNIFORM_VIDEO, negative)
    for frame in result:
        assert frame.shape == (FRAME_H, FRAME_W)


def test_apply_per_frame_negative_correctness():
    """
    Test purpose - Applying negative per-frame produces 1 - frame for each frame.
    Criteria - Each output frame equals (1 - corresponding input frame) element-wise.

    Test steps:
    1) Apply negative to KNOWN_VIDEO_2F via apply_per_frame.
    2) For each frame, assert result equals 1 - original.
    """

    result = apply_per_frame(KNOWN_VIDEO_2F, negative)
    for original, processed in zip(KNOWN_VIDEO_2F, result):
        np.testing.assert_array_almost_equal(processed, 1 - original)


def test_apply_per_frame_gamma_correction():
    """
    Test purpose - gamma_correction applied per-frame raises every pixel to the given power.
    Criteria - Each output pixel equals input_pixel ** gamma.

    Test steps:
    1) Apply gamma_correction with gamma=2.0 to UNIFORM_VIDEO (all pixels = 0.5).
    2) Assert every output pixel ≈ 0.25 (0.5 ** 2).
    """

    gamma = 2.0
    result = apply_per_frame(UNIFORM_VIDEO, gamma_correction, gamma=gamma)
    for frame in result:
        np.testing.assert_array_almost_equal(frame, np.full((FRAME_H, FRAME_W), 0.5 ** gamma))


def test_apply_per_frame_color_video_convert_to_grayscale():
    """
    Test purpose - convert_to_grayscale applied per-frame reduces channel dimension.
    Criteria - Each output frame has shape (H, W) when input frames are (H, W, 3).

    Test steps:
    1) Apply convert_to_grayscale to COLOR_UNIFORM_VIDEO.
    2) Assert every output frame has shape (FRAME_H, FRAME_W).
    """

    result = apply_per_frame(COLOR_UNIFORM_VIDEO, convert_to_grayscale)
    for frame in result:
        assert frame.ndim == 2
        assert frame.shape == (FRAME_H, FRAME_W)


def test_apply_per_frame_does_not_mutate_input():
    """
    Test purpose - apply_per_frame does not modify the original frame list in place.
    Criteria - Input frames are unchanged after the call.

    Test steps:
    1) Record a deep copy of UNIFORM_VIDEO.
    2) Apply negative via apply_per_frame.
    3) Assert the original frames are unchanged.
    """

    import copy
    original_copy = copy.deepcopy(UNIFORM_VIDEO)
    apply_per_frame(UNIFORM_VIDEO, negative)
    for orig, after in zip(original_copy, UNIFORM_VIDEO):
        np.testing.assert_array_equal(orig, after)


# ──────────────────────────────────────────────────────────── #
#  stack_frames / unstack_frames tests                          #
# ──────────────────────────────────────────────────────────── #

def test_stack_frames_shape():
    """
    Test purpose - stack_frames produces a (T, H, W) array for a grayscale frame list.
    Criteria - Stacked shape is (N_FRAMES, FRAME_H, FRAME_W).

    Test steps:
    1) Stack UNIFORM_VIDEO.
    2) Assert the result shape is (N_FRAMES, FRAME_H, FRAME_W).
    """

    stacked = stack_frames(UNIFORM_VIDEO)
    assert stacked.shape == (N_FRAMES, FRAME_H, FRAME_W)


def test_unstack_restores_list():
    """
    Test purpose - unstack_frames(stack_frames(frames)) recovers the original list.
    Criteria - Round-tripped frames are element-wise equal to the originals.

    Test steps:
    1) Stack then unstack KNOWN_VIDEO_2F.
    2) Assert each recovered frame equals the original.
    """

    recovered = unstack_frames(stack_frames(KNOWN_VIDEO_2F))
    assert len(recovered) == len(KNOWN_VIDEO_2F)
    for orig, rec in zip(KNOWN_VIDEO_2F, recovered):
        np.testing.assert_array_equal(orig, rec)
