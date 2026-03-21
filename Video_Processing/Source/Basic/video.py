"""
Script Name - video.py

Purpose - Class for video representation, processing, and display.
          Mirrors the Image class (Image_Processing.Source.Basic.image) but operates on a
          time-ordered sequence of frames.  Every image-processing function in
          Image_Processing.Source.Advanced is accessible via apply_per_frame; video-specific
          temporal algorithms are exposed as first-class methods.

Created by Michael Samelsohn, 21/03/26.
"""

# Imports #
import copy
import traceback

import cv2
import matplotlib.pyplot as plt
import numpy as np
from numpy import ndarray

from Image_Processing.Source.Advanced.intensity_transformations import (
    negative, gamma_correction, bit_plane_reconstruction, bit_plane_slicing,
)
from Image_Processing.Source.Advanced.spatial_filtering import (
    blur_image, laplacian_gradient, laplacian_image_sharpening, high_boost_filter, sobel_filter,
)
from Image_Processing.Source.Advanced.segmentation import (
    isolated_point_detection, harris_corner_detector, line_detection,
    marr_hildreth_edge_detection, canny_edge_detection,
    thresholding, global_thresholding, otsu_global_thresholding,
)
from Image_Processing.Source.Advanced.restoration import mean_filter, order_statistic_filter
from Image_Processing.Source.Advanced.noise_models import (
    add_gaussian_noise, add_rayleigh_noise, add_erlang_noise,
    add_exponential_noise, add_uniform_noise, add_salt_and_pepper,
)
from Image_Processing.Source.Advanced.morphology import (
    erosion, dilation, opening, closing, boundary_extraction,
)
from Image_Processing.Source.Basic.common import convert_to_grayscale
from Image_Processing.Settings.image_settings import (
    DEFAULT_GAMMA_VALUE, DEFAULT_DEGREE_OF_REDUCTION, DEFAULT_BIT_PLANE,
    DEFAULT_FILTER_TYPE, DEFAULT_FILTER_SIZE, DEFAULT_PADDING_TYPE, DEFAULT_SIGMA_VALUE,
    DEFAULT_NORMALIZATION_METHOD, DEFAULT_INCLUDE_DIAGONAL_TERMS, DEFAULT_K_VALUE,
    DEFAULT_HARRIS_K_VALUE, DEFAULT_HARRIS_RADIUS,
    DEFAULT_HIGH_THRESHOLD_CANNY, DEFAULT_LOW_THRESHOLD_CANNY,
    DEFAULT_THRESHOLD_VALUE, DEFAULT_DELTA_T,
    DEFAULT_MEAN_FILTER_TYPE, DEFAULT_ORDER_STATISTIC_FILTER_TYPE,
    DEFAULT_GAUSSIAN_MEAN, DEFAULT_GAUSSIAN_SIGMA,
    DEFAULT_RAYLEIGH_A, DEFAULT_RAYLEIGH_B,
    DEFAULT_ERLANG_A, DEFAULT_ERLANG_B,
    DEFAULT_EXPONENTIAL_DECAY, DEFAULT_UNIFORM_A, DEFAULT_UNIFORM_B,
    DEFAULT_PEPPER, DEFAULT_SALT,
    DEFAULT_STRUCTURING_ELEMENT, DEFAULT_COMPARE_MAX_VALUES,
    DEFAULT_COMPARE_MAX_VALUES,
)

from Video_Processing.Source.Advanced.frame_operations import apply_per_frame
from Video_Processing.Source.Advanced.temporal import (
    frame_difference, background_subtraction, temporal_average, motion_detection,
)
from Video_Processing.Source.Basic.video_metrics import VideoComparator
from Video_Processing.Settings.video_settings import *


# ──────────────────────────────────────────────────────────────────────────── #
# I/O helpers                                                                   #
# ──────────────────────────────────────────────────────────────────────────── #

def _load_video(video_path: str) -> tuple[list[ndarray], float]:
    """
    Load a video file into a list of float64 frames in [0, 1] (RGB channel order).

    :param video_path: Path to the video file.
    :return:           Tuple of (frames, fps).
    """

    log.info(f"Loading video from '{video_path}'")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        log.raise_exception(
            message=f"Cannot open video file: {video_path}",
            exception=IOError)

    fps = cap.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    log.debug(f"Video metadata: fps={fps:.2f}, total_frames={n_frames}")

    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame_rgb.astype(np.float64) / 255.0)

    cap.release()
    log.success(f"Loaded {len(frames)} frame(s) at {fps:.2f} fps")
    return frames, fps


def _save_video(frames: list[ndarray], output_path: str,
                fps: float = DEFAULT_FPS, codec: str = DEFAULT_CODEC) -> None:
    """
    Write a list of float64 [0, 1] frames to a video file.

    :param frames:      List of frames to write (grayscale or RGB, float64 in [0, 1]).
    :param output_path: Destination file path.
    :param fps:         Output frame rate.
    :param codec:       Four-character codec code (e.g. 'mp4v').
    """

    if not frames:
        log.warning("No frames to save")
        return

    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*codec)
    writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    log.info(f"Saving {len(frames)} frame(s) to '{output_path}' ({w}×{h} @ {fps} fps)")

    for frame in frames:
        uint8 = (np.clip(frame, 0.0, 1.0) * 255).astype(np.uint8)
        if uint8.ndim == 2:  # grayscale → BGR
            uint8 = cv2.cvtColor(uint8, cv2.COLOR_GRAY2BGR)
        else:
            uint8 = cv2.cvtColor(uint8, cv2.COLOR_RGB2BGR)
        writer.write(uint8)

    writer.release()
    log.success(f"Video saved to '{output_path}'")


# ──────────────────────────────────────────────────────────────────────────── #
# Video class                                                                   #
# ──────────────────────────────────────────────────────────────────────────── #

class Video:
    """
    Wrapper for a video (sequence of frames) that exposes image-processing operations
    frame-by-frame and temporal operations across the sequence.

    Initialisation:
        v = Video(video_path="clip.mp4")          # load from file
        v = Video(frames=[arr1, arr2, ...])        # from a pre-built list of ndarrays

    The class maintains a frame buffer (list of {"Name": str, "Frames": list[ndarray]}
    dicts) that accumulates every processing step, analogous to Image._image_buffer.
    """

    def __init__(self, video_path: str = None,
                 frames: list[ndarray] = None,
                 fps: float = DEFAULT_FPS,
                 display_time=None):
        """
        :param video_path:    Path to a video file.  Mutually exclusive with `frames`.
        :param frames:        Pre-built list of ndarray frames in [0, 1].
        :param fps:           Frame rate used when `frames` is supplied directly.
        :param display_time:  Seconds to auto-close matplotlib figures (None = manual close).
        """

        log.info("Initiating Video class")
        self.display_time = display_time

        if video_path is not None:
            log.debug(f"Loading video from path: {video_path}")
            try:
                self._original_frames, self._fps = _load_video(video_path)
            except Exception:
                log.error("Failed to load video")
                log.print_data(data=traceback.format_exc(), log_level='error')
                self._original_frames = []
                self._fps = fps
        elif frames is not None:
            log.debug(f"Initialising from {len(frames)} pre-built frame(s)")
            self._original_frames = frames
            self._fps = fps
        else:
            log.raise_exception(
                message="Provide either video_path or frames to initialise a Video",
                exception=ValueError)

        self._current_frames: list[ndarray] = copy.deepcopy(self._original_frames)
        self._frame_buffer: list[dict] = [
            {"Name": "Original", "Frames": self._original_frames}
        ]

    # ── Basic operations ──────────────────────────────────────────────────── #

    def reset_to_original(self) -> None:
        """Reset the current frame list to the original loaded frames."""

        log.info("Resetting current frames to original")
        self._current_frames = copy.deepcopy(self._original_frames)

    def save(self, output_path: str, codec: str = DEFAULT_CODEC) -> None:
        """
        Save the most recently processed frame sequence to a video file.

        :param output_path: Destination file path (e.g. 'output.mp4').
        :param codec:       Four-character codec string (default 'mp4v').
        """

        _save_video(
            frames=self._frame_buffer[-1]["Frames"],
            output_path=output_path,
            fps=self._fps,
            codec=codec,
        )

    # ── Display ───────────────────────────────────────────────────────────── #

    def display_frame(self, index: int = 0) -> None:
        """
        Display a single frame from the most recently processed sequence.

        :param index: Frame index to display (0-based).
        """

        last = self._frame_buffer[-1]
        frames = last["Frames"]

        if index >= len(frames):
            log.error(f"Frame index {index} out of range (only {len(frames)} frame(s))")
            return

        frame = frames[index]
        log.debug(f"Displaying frame {index} from '{last['Name']}'")

        plt.imshow(frame, cmap='gray') if frame.ndim == 2 else plt.imshow(frame)
        plt.title(f"{last['Name']}  [frame {index}]")
        self._plt_show()

    def display_original_frame(self, index: int = 0) -> None:
        """
        Display a single frame from the original (unprocessed) sequence.

        :param index: Frame index to display (0-based).
        """

        if index >= len(self._original_frames):
            log.error(f"Frame index {index} out of range")
            return

        frame = self._original_frames[index]
        plt.imshow(frame, cmap='gray') if frame.ndim == 2 else plt.imshow(frame)
        plt.title(f"Original  [frame {index}]")
        self._plt_show()

    def compare_frame_to_original(self, index: int = 0) -> None:
        """
        Show an original frame alongside the corresponding processed frame side-by-side.

        :param index: Frame index to compare (0-based).
        """

        last = self._frame_buffer[-1]
        processed_frames = last["Frames"]

        original_frame = self._original_frames[min(index, len(self._original_frames) - 1)]
        processed_frame = processed_frames[min(index, len(processed_frames) - 1)]

        log.debug(f"Comparing frame {index}: original vs '{last['Name']}'")

        plt.subplot(1, 2, 1)
        plt.title(f"Original  [frame {index}]")
        plt.imshow(original_frame, cmap='gray') if original_frame.ndim == 2 \
            else plt.imshow(original_frame)

        plt.subplot(1, 2, 2)
        plt.title(f"{last['Name']}  [frame {index}]")
        plt.imshow(processed_frame, cmap='gray') if processed_frame.ndim == 2 \
            else plt.imshow(processed_frame)

        self._plt_show()

    def display_frame_strip(self, step: int = 1, max_frames: int = 8) -> None:
        """
        Display a horizontal strip of evenly-sampled frames from the current sequence.

        :param step:       Sampling interval between displayed frames.
        :param max_frames: Maximum number of frames shown.
        """

        last = self._frame_buffer[-1]
        frames = last["Frames"]
        indices = list(range(0, len(frames), step))[:max_frames]

        log.debug(f"Displaying strip of {len(indices)} frame(s) from '{last['Name']}'")

        fig, axes = plt.subplots(1, len(indices), figsize=(3 * len(indices), 3))
        if len(indices) == 1:
            axes = [axes]

        for ax, i in zip(axes, indices):
            frame = frames[i]
            ax.imshow(frame, cmap='gray') if frame.ndim == 2 else ax.imshow(frame)
            ax.set_title(f"t={i}", fontsize=8)
            ax.axis('off')

        plt.suptitle(last['Name'], fontsize=10, fontweight='bold')
        plt.tight_layout()
        self._plt_show()

    def _plt_show(self) -> None:
        """Show the current matplotlib figure, auto-closing after display_time seconds if set."""

        if self.display_time:
            plt.show(block=False)
            plt.pause(self.display_time)
            plt.close()
        else:
            plt.show()

    # ── Per-frame: basic ──────────────────────────────────────────────────── #

    def convert_to_grayscale(self) -> None:
        self._current_frames = apply_per_frame(self._current_frames, convert_to_grayscale)
        self._frame_buffer.append({"Name": "Grayscale", "Frames": self._current_frames})

    # ── Per-frame: intensity transformations ──────────────────────────────── #

    def negative(self) -> None:
        self._current_frames = apply_per_frame(self._current_frames, negative)
        self._frame_buffer.append({"Name": "Negative", "Frames": self._current_frames})

    def gamma_correction(self, gamma: float = DEFAULT_GAMMA_VALUE) -> None:
        self._current_frames = apply_per_frame(self._current_frames, gamma_correction, gamma=gamma)
        self._frame_buffer.append(
            {"Name": f"Gamma correction (γ={gamma})", "Frames": self._current_frames})

    def bit_plane_reconstruction(self,
                                  degree_of_reduction: int = DEFAULT_DEGREE_OF_REDUCTION) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, bit_plane_reconstruction,
            degree_of_reduction=degree_of_reduction)
        self._frame_buffer.append(
            {"Name": f"Bit plane reconstruction (degree={degree_of_reduction})",
             "Frames": self._current_frames})

    def bit_plane_slicing(self, bit_plane: int = DEFAULT_BIT_PLANE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, bit_plane_slicing, bit_plane=bit_plane)
        self._frame_buffer.append(
            {"Name": f"Bit plane slicing (plane={bit_plane})", "Frames": self._current_frames})

    # ── Per-frame: spatial filtering ──────────────────────────────────────── #

    def blur(self, filter_type: str = DEFAULT_FILTER_TYPE,
             filter_size: int = DEFAULT_FILTER_SIZE,
             padding_type: str = DEFAULT_PADDING_TYPE,
             sigma: float = DEFAULT_SIGMA_VALUE,
             normalization_method: str = DEFAULT_NORMALIZATION_METHOD) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, blur_image,
            filter_type=filter_type, filter_size=filter_size,
            padding_type=padding_type, sigma=sigma,
            normalization_method=normalization_method)
        self._frame_buffer.append({"Name": "Blur", "Frames": self._current_frames})

    def laplacian_gradient(self, padding_type: str = DEFAULT_PADDING_TYPE,
                            include_diagonal_terms: bool = DEFAULT_INCLUDE_DIAGONAL_TERMS,
                            normalization_method: str = DEFAULT_NORMALIZATION_METHOD) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, laplacian_gradient,
            padding_type=padding_type, include_diagonal_terms=include_diagonal_terms,
            normalization_method=normalization_method)
        self._frame_buffer.append({"Name": "Laplacian gradient", "Frames": self._current_frames})

    def laplacian_image_sharpening(self,
                                    padding_type: str = DEFAULT_PADDING_TYPE,
                                    include_diagonal_terms: bool = DEFAULT_INCLUDE_DIAGONAL_TERMS
                                    ) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, laplacian_image_sharpening,
            padding_type=padding_type, include_diagonal_terms=include_diagonal_terms)
        self._frame_buffer.append(
            {"Name": "Laplacian image sharpening", "Frames": self._current_frames})

    def high_boost_filter(self, filter_type: str = DEFAULT_FILTER_TYPE,
                           filter_size: int = DEFAULT_FILTER_SIZE,
                           padding_type: str = DEFAULT_PADDING_TYPE,
                           k: float = DEFAULT_K_VALUE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, high_boost_filter,
            filter_type=filter_type, filter_size=filter_size,
            padding_type=padding_type, k=k)
        self._frame_buffer.append({"Name": "High boost filter", "Frames": self._current_frames})

    def sobel_filter(self, padding_type: str = DEFAULT_PADDING_TYPE,
                     normalization_method: str = DEFAULT_NORMALIZATION_METHOD) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, sobel_filter,
            padding_type=padding_type, normalization_method=normalization_method)
        self._frame_buffer.append({"Name": "Sobel filter", "Frames": self._current_frames})

    # ── Per-frame: segmentation ───────────────────────────────────────────── #

    def isolated_point_detection(self,
                                   padding_type: str = DEFAULT_PADDING_TYPE,
                                   normalization_method: str = DEFAULT_NORMALIZATION_METHOD,
                                   include_diagonal_terms: bool = DEFAULT_INCLUDE_DIAGONAL_TERMS,
                                   threshold_value: float = DEFAULT_THRESHOLD_VALUE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, isolated_point_detection,
            padding_type=padding_type, normalization_method=normalization_method,
            include_diagonal_terms=include_diagonal_terms, threshold_value=threshold_value)
        self._frame_buffer.append(
            {"Name": "Isolated point detection", "Frames": self._current_frames})

    def harris_corner_detector(self, padding_type: str = DEFAULT_PADDING_TYPE,
                                k: float = DEFAULT_HARRIS_K_VALUE,
                                sigma: float = DEFAULT_SIGMA_VALUE,
                                radius: int = DEFAULT_HARRIS_RADIUS) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, harris_corner_detector,
            padding_type=padding_type, sigma=sigma, k=k, radius=radius)
        self._frame_buffer.append(
            {"Name": "Harris corner detection", "Frames": self._current_frames})

    def line_detection(self, padding_type: str = DEFAULT_PADDING_TYPE,
                       normalization_method: str = DEFAULT_NORMALIZATION_METHOD,
                       threshold_value: float = DEFAULT_THRESHOLD_VALUE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, line_detection,
            padding_type=padding_type, normalization_method=normalization_method,
            threshold_value=threshold_value)
        self._frame_buffer.append({"Name": "Line detection", "Frames": self._current_frames})

    def marr_hildreth_edge_detection(self,
                                      filter_size: int = DEFAULT_FILTER_SIZE,
                                      padding_type: str = DEFAULT_PADDING_TYPE,
                                      sigma: float = DEFAULT_SIGMA_VALUE,
                                      include_diagonal_terms: bool = DEFAULT_INCLUDE_DIAGONAL_TERMS,
                                      threshold: float = DEFAULT_THRESHOLD_VALUE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, marr_hildreth_edge_detection,
            filter_size=filter_size, padding_type=padding_type, sigma=sigma,
            include_diagonal_terms=include_diagonal_terms, threshold=threshold)
        self._frame_buffer.append(
            {"Name": "Marr-Hildreth edge detection", "Frames": self._current_frames})

    def canny_edge_detection(self, filter_size: int = DEFAULT_FILTER_SIZE,
                              padding_type: str = DEFAULT_PADDING_TYPE,
                              sigma: float = DEFAULT_SIGMA_VALUE,
                              high_threshold: float = DEFAULT_HIGH_THRESHOLD_CANNY,
                              low_threshold: float = DEFAULT_LOW_THRESHOLD_CANNY) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, canny_edge_detection,
            filter_size=filter_size, padding_type=padding_type, sigma=sigma,
            high_threshold=high_threshold, low_threshold=low_threshold)
        self._frame_buffer.append(
            {"Name": "Canny edge detection", "Frames": self._current_frames})

    def thresholding(self, threshold_value: float = DEFAULT_THRESHOLD_VALUE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, thresholding, threshold_value=threshold_value)
        self._frame_buffer.append({"Name": "Thresholding", "Frames": self._current_frames})

    def global_thresholding(self, initial_threshold: float = DEFAULT_THRESHOLD_VALUE,
                             delta_t: float = DEFAULT_DELTA_T) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, global_thresholding,
            initial_threshold=initial_threshold, delta_t=delta_t)
        self._frame_buffer.append(
            {"Name": "Global thresholding", "Frames": self._current_frames})

    def otsu_global_thresholding(self) -> None:
        self._current_frames = apply_per_frame(self._current_frames, otsu_global_thresholding)
        self._frame_buffer.append(
            {"Name": "Otsu global thresholding", "Frames": self._current_frames})

    # ── Per-frame: restoration ────────────────────────────────────────────── #

    def mean_filter(self, filter_type: str = DEFAULT_MEAN_FILTER_TYPE,
                    padding_type: str = DEFAULT_PADDING_TYPE,
                    filter_size: int = DEFAULT_FILTER_SIZE, **kwargs) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, mean_filter,
            filter_type=filter_type, padding_type=padding_type,
            filter_size=filter_size, **kwargs)
        self._frame_buffer.append(
            {"Name": f"Mean filter ({filter_type})", "Frames": self._current_frames})

    def order_statistic_filter(self,
                                filter_type: str = DEFAULT_ORDER_STATISTIC_FILTER_TYPE,
                                padding_type: str = DEFAULT_PADDING_TYPE,
                                filter_size: int = DEFAULT_FILTER_SIZE, **kwargs) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, order_statistic_filter,
            filter_type=filter_type, padding_type=padding_type,
            filter_size=filter_size, **kwargs)
        self._frame_buffer.append(
            {"Name": f"Order statistic filter ({filter_type})", "Frames": self._current_frames})

    # ── Per-frame: noise models ───────────────────────────────────────────── #

    def add_gaussian_noise(self, mean: float = DEFAULT_GAUSSIAN_MEAN,
                            sigma: float = DEFAULT_GAUSSIAN_SIGMA) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, add_gaussian_noise, mean=mean, sigma=sigma)
        self._frame_buffer.append({"Name": "Gaussian noise", "Frames": self._current_frames})

    def add_rayleigh_noise(self, a: float = DEFAULT_RAYLEIGH_A,
                            b: float = DEFAULT_RAYLEIGH_B) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, add_rayleigh_noise, a=a, b=b)
        self._frame_buffer.append({"Name": "Rayleigh noise", "Frames": self._current_frames})

    def add_erlang_noise(self, a: float = DEFAULT_ERLANG_A,
                          b: float = DEFAULT_ERLANG_B) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, add_erlang_noise, a=a, b=b)
        self._frame_buffer.append({"Name": "Erlang noise", "Frames": self._current_frames})

    def add_exponential_noise(self, a: float = DEFAULT_EXPONENTIAL_DECAY) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, add_exponential_noise, a=a)
        self._frame_buffer.append({"Name": "Exponential noise", "Frames": self._current_frames})

    def add_uniform_noise(self, a: float = DEFAULT_UNIFORM_A,
                           b: float = DEFAULT_UNIFORM_B) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, add_uniform_noise, a=a, b=b)
        self._frame_buffer.append({"Name": "Uniform noise", "Frames": self._current_frames})

    def add_salt_and_pepper(self, pepper: float = DEFAULT_PEPPER,
                             salt: float = DEFAULT_SALT) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, add_salt_and_pepper, pepper=pepper, salt=salt)
        self._frame_buffer.append({"Name": "Salt & Pepper noise", "Frames": self._current_frames})

    # ── Per-frame: morphology ─────────────────────────────────────────────── #

    def erosion(self, structuring_element: ndarray = DEFAULT_STRUCTURING_ELEMENT,
                padding_type: str = DEFAULT_PADDING_TYPE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, erosion,
            structuring_element=structuring_element, padding_type=padding_type)
        self._frame_buffer.append({"Name": "Erosion", "Frames": self._current_frames})

    def dilation(self, structuring_element: ndarray = DEFAULT_STRUCTURING_ELEMENT,
                 padding_type: str = DEFAULT_PADDING_TYPE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, dilation,
            structuring_element=structuring_element, padding_type=padding_type)
        self._frame_buffer.append({"Name": "Dilation", "Frames": self._current_frames})

    def opening(self, structuring_element: ndarray = DEFAULT_STRUCTURING_ELEMENT,
                padding_type: str = DEFAULT_PADDING_TYPE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, opening,
            structuring_element=structuring_element, padding_type=padding_type)
        self._frame_buffer.append({"Name": "Opening", "Frames": self._current_frames})

    def closing(self, structuring_element: ndarray = DEFAULT_STRUCTURING_ELEMENT,
                padding_type: str = DEFAULT_PADDING_TYPE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, closing,
            structuring_element=structuring_element, padding_type=padding_type)
        self._frame_buffer.append({"Name": "Closing", "Frames": self._current_frames})

    def boundary_extraction(self, structuring_element: ndarray = DEFAULT_STRUCTURING_ELEMENT,
                             padding_type: str = DEFAULT_PADDING_TYPE) -> None:
        self._current_frames = apply_per_frame(
            self._current_frames, boundary_extraction,
            structuring_element=structuring_element, padding_type=padding_type)
        self._frame_buffer.append(
            {"Name": "Boundary extraction", "Frames": self._current_frames})

    # ── Temporal operations ───────────────────────────────────────────────── #

    def frame_difference(self) -> None:
        """
        Replace the current frame sequence with absolute consecutive frame differences.

        The output has N-1 frames for an input of N frames.
        """

        result = frame_difference(self._current_frames)
        self._current_frames = result
        self._frame_buffer.append({"Name": "Frame difference", "Frames": self._current_frames})

    def background_subtraction(self,
                                 learning_rate: float = DEFAULT_BG_LEARNING_RATE) -> None:
        """
        Separate foreground from background using a running-average background model.

        :param learning_rate: Background update rate α ∈ (0, 1].
        """

        result = background_subtraction(self._current_frames, learning_rate=learning_rate)
        self._current_frames = result
        self._frame_buffer.append(
            {"Name": f"Background subtraction (α={learning_rate})",
             "Frames": self._current_frames})

    def temporal_average(self, window_size: int = DEFAULT_TEMPORAL_WINDOW) -> None:
        """
        Smooth the frame sequence by averaging within a sliding temporal window.

        :param window_size: Number of frames in the averaging window.
        """

        result = temporal_average(self._current_frames, window_size=window_size)
        self._current_frames = result
        self._frame_buffer.append(
            {"Name": f"Temporal average (window={window_size})",
             "Frames": self._current_frames})

    def motion_detection(self, threshold: float = DEFAULT_DIFF_THRESHOLD) -> None:
        """
        Produce binary motion masks by thresholding frame-to-frame differences.

        The output has N-1 frames for an input of N frames.

        :param threshold: Pixel-change threshold in [0, 1].
        """

        result = motion_detection(self._current_frames, threshold=threshold)
        self._current_frames = result
        self._frame_buffer.append(
            {"Name": f"Motion detection (threshold={threshold})",
             "Frames": self._current_frames})

    # ── Metrics ───────────────────────────────────────────────────────────── #

    def compare(self, original: list[ndarray]) -> VideoComparator:
        """
        Return a VideoComparator for the current frame sequence against a reference.

        :param original: Clean reference frame list; must match the current frame count and shape.
        :return:         Populated VideoComparator instance.
        """

        return VideoComparator(original=original, distorted=self._current_frames)
