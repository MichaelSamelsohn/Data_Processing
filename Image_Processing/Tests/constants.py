# Imports #
import numpy as np
from Image_Processing.Settings.image_settings import log

log.stream_handler = False  # Suppress console logging during tests.

RANDOM_TESTS = 1

# ── Grayscale test images ─────────────────────────────────────────────────── #

# 3x3 image with known distinct values in [0, 1].
KNOWN_3x3 = np.array([
    [0.1, 0.5, 0.9],
    [0.3, 0.7, 0.2],
    [0.8, 0.4, 0.6],
], dtype=float)

# 5x5 uniform image (all pixels equal to 0.5).
UNIFORM_5x5 = np.full((5, 5), 0.5)

# 5x5 image with values ramping column-wise from 0.0 to 1.0.
RAMP_5x5 = np.array([
    [0.0, 0.25, 0.5, 0.75, 1.0],
    [0.0, 0.25, 0.5, 0.75, 1.0],
    [0.0, 0.25, 0.5, 0.75, 1.0],
    [0.0, 0.25, 0.5, 0.75, 1.0],
    [0.0, 0.25, 0.5, 0.75, 1.0],
], dtype=float)

# ── Color test images ─────────────────────────────────────────────────────── #

# 3-pixel color image: one pixel per primary color (shape = 3×1×3).
COLOR_3x1 = np.array([
    [[1.0, 0.0, 0.0]],  # Pure red.
    [[0.0, 1.0, 0.0]],  # Pure green.
    [[0.0, 0.0, 1.0]],  # Pure blue.
], dtype=float)

# Expected grayscale for COLOR_3x1 (NTSC: 0.2989*R + 0.5870*G + 0.1140*B).
GRAY_3x1 = np.array([
    [0.2989],  # Red only.
    [0.5870],  # Green only.
    [0.1140],  # Blue only.
], dtype=float)

# ── Binary test images ────────────────────────────────────────────────────── #

# 5x5 all-ones binary image.
BINARY_ONES_5x5 = np.ones((5, 5))

# 5x5 all-zeros binary image.
BINARY_ZEROS_5x5 = np.zeros((5, 5))

# 5x5 binary image with a single foreground pixel at center (row=2, col=2).
BINARY_SINGLE_PIXEL_5x5 = np.zeros((5, 5))
BINARY_SINGLE_PIXEL_5x5[2, 2] = 1

# 5x5 binary image with a 3x3 filled square at center (rows/cols 1-3 inclusive).
BINARY_SQUARE_5x5 = np.zeros((5, 5))
BINARY_SQUARE_5x5[1:4, 1:4] = 1

# 7x7 binary image with a filled 5x5 rectangle at center (rows/cols 1-5 inclusive).
BINARY_RECT_7x7 = np.zeros((7, 7))
BINARY_RECT_7x7[1:6, 1:6] = 1

# ── Structuring elements ──────────────────────────────────────────────────── #

# Standard 3x3 all-ones structuring element.
SE_3x3 = np.ones((3, 3))

# Asymmetric 3x3 structuring element (non-zero top-left and center only).
SE_ASYMMETRIC = np.array([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 0],
], dtype=float)