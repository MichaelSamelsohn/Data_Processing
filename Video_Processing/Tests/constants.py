# Imports #
import numpy as np
from Image_Processing.Settings.image_settings import log

log.stream_handler = False  # Suppress console logging during tests.

# ── Synthetic video parameters ─────────────────────────────────────────────── #

N_FRAMES = 6    # Number of frames in most test videos.
FRAME_H  = 8    # Frame height (pixels).
FRAME_W  = 8    # Frame width (pixels).

# ── Grayscale test videos ──────────────────────────────────────────────────── #

# Uniform video: all frames identical, all pixels = 0.5.
UNIFORM_VIDEO = [np.full((FRAME_H, FRAME_W), 0.5, dtype=float) for _ in range(N_FRAMES)]

# Static video: all frames identical, all pixels = 0.3.
STATIC_VIDEO = [np.full((FRAME_H, FRAME_W), 0.3, dtype=float) for _ in range(N_FRAMES)]

# Ramp video: intensity increases linearly from 0 to 1 across frames.
RAMP_VIDEO = [
    np.full((FRAME_H, FRAME_W), i / max(N_FRAMES - 1, 1), dtype=float)
    for i in range(N_FRAMES)
]

# Binary video: alternating all-zeros and all-ones frames (maximum motion signal).
BINARY_ALT_VIDEO = [
    np.zeros((FRAME_H, FRAME_W), dtype=float) if i % 2 == 0
    else np.ones((FRAME_H, FRAME_W), dtype=float)
    for i in range(N_FRAMES)
]

# Zero video: all frames are all-zero (black).
ZERO_VIDEO = [np.zeros((FRAME_H, FRAME_W), dtype=float) for _ in range(N_FRAMES)]

# ── Color test videos ──────────────────────────────────────────────────────── #

# Uniform color video: all frames are a uniform mid-gray RGB image.
COLOR_UNIFORM_VIDEO = [
    np.full((FRAME_H, FRAME_W, 3), 0.5, dtype=float) for _ in range(N_FRAMES)
]

# ── Known single frames ────────────────────────────────────────────────────── #

# 4×4 grayscale frame with known distinct values.
KNOWN_4x4 = np.array([
    [0.1, 0.5, 0.9, 0.2],
    [0.3, 0.7, 0.4, 0.6],
    [0.8, 0.0, 1.0, 0.3],
    [0.4, 0.6, 0.2, 0.8],
], dtype=float)

# Two-frame video built from KNOWN_4x4 for per-frame operation tests.
KNOWN_VIDEO_2F = [KNOWN_4x4, 1 - KNOWN_4x4]
