"""
Script Name - frame_operations.py

Purpose - Per-frame application of image-processing functions to video frame sequences.
          All existing Image_Processing functions (intensity transformations, spatial filtering,
          segmentation, restoration, noise models, morphology, frequency domain) can be applied
          to every frame in a video by passing them to apply_per_frame.

Created by Michael Samelsohn, 21/03/26.
"""

# Imports #
from typing import Callable

import numpy as np
from numpy import ndarray

from Video_Processing.Settings.video_settings import *


def apply_per_frame(frames: list[ndarray], func: Callable, **kwargs) -> list[ndarray]:
    """
    Apply an image-processing function to every frame of a video independently.

    The supplied function must accept `image` as a keyword argument and return an ndarray —
    which is the convention for every function in Image_Processing.Source.

    :param frames: List of video frames, each an ndarray in [0, 1].
    :param func:   Image-processing function with signature func(image=..., **kwargs) -> ndarray.
    :param kwargs: Additional keyword arguments forwarded verbatim to func.

    :return: New list of processed frames, same length as the input.
    """

    log.info(f"Applying '{func.__name__}' per-frame to {len(frames)} frame(s)")
    return [func(image=frame, **kwargs) for frame in frames]


def stack_frames(frames: list[ndarray]) -> ndarray:
    """
    Stack a list of frames into a single 4-D array of shape (T, H, W) or (T, H, W, C).

    :param frames: List of T frames, each of shape (H, W) or (H, W, C).
    :return:       Stacked array of shape (T, H, W) or (T, H, W, C).
    """

    log.debug(f"Stacking {len(frames)} frame(s) into a single array")
    return np.stack(frames, axis=0)


def unstack_frames(array: ndarray) -> list[ndarray]:
    """
    Split a stacked (T, H, W[, C]) array back into a list of T individual frames.

    :param array: Stacked array of shape (T, H, W) or (T, H, W, C).
    :return:      List of T frames.
    """

    log.debug(f"Unstacking array of shape {array.shape} into individual frames")
    return [array[i] for i in range(array.shape[0])]
