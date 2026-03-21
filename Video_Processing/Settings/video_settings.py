"""
Script Name - video_settings.py

Purpose - Centralise all the constants and settings of the Video_Processing directory.

Created by Michael Samelsohn, 21/03/26.
"""

# Imports #
from settings import log

# Logger settings #
verbosity_level = 3  # Setting the verbosity level.

# Handling verbosity levels.
match verbosity_level:
    case 1:
        log.format_string = "%(asctime)s - %(levelname)s - %(message)s"
        log.log_level = 20
    case 2:
        log.format_string = "%(asctime)s - %(levelname)s - %(message)s"
        log.log_level = 11
    case 3:
        log.format_string = "%(asctime)s - %(levelname)s (%(module)s:%(funcName)s:%(lineno)d) - %(message)s"
        log.log_level = 10

# Video I/O #
DEFAULT_CODEC = 'mp4v'
DEFAULT_FPS = 30.0
DEFAULT_VIDEO_EXTENSION = '.mp4'

# Temporal operations #
DEFAULT_DIFF_THRESHOLD = 0.05      # pixel-wise threshold for motion detection
DEFAULT_TEMPORAL_WINDOW = 5        # number of frames averaged in temporal_average
DEFAULT_BG_LEARNING_RATE = 0.05   # running-average update rate for background subtraction

# Metrics #
DEFAULT_PSNR_MAX_VALUE = 1.0  # maximum pixel value for normalised [0, 1] frames
DEFAULT_SSIM_SIGMA = 1.5      # Gaussian window σ for local SSIM statistics
DEFAULT_SSIM_K1 = 0.01        # stability constant for the luminance term
DEFAULT_SSIM_K2 = 0.03        # stability constant for the contrast/structure term
