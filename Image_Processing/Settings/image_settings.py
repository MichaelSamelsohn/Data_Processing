"""
Script Name - image_settings.py

Purpose - Centralize all the constants and settings of the Image_Processing directory.

Created by Michael Samelsohn, 05/05/22.
"""

# Imports #
import os

import numpy as np
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

# Image Class #
DEFAULT_IMAGE_LENA = os.path.abspath('../Image_Processing/Images/Lena.png')
GONZALES_WOODS_BOOK = "Digital Image Processing (4th edition) - Gonzales & Woods"

# Intensity Transformations #
DEFAULT_THRESHOLD_VALUE = 0.5
DEFAULT_GAMMA_VALUE = 1
DEFAULT_DEGREE_OF_REDUCTION = 4
DEFAULT_BIT_PLANE = 4
DEFAULT_HISTOGRAM_NORMALIZATION = False

# Common #
DEFAULT_SCALING_FACTOR = 255
DEFAULT_PADDING_SIZE = 1
DEFAULT_PADDING_TYPE = "zero"
DEFAULT_FILTER_TYPE = "box"
DEFAULT_MEAN_FILTER_TYPE = "arithmetic"
DEFAULT_ORDER_STATISTIC_FILTER_TYPE = "median"
DEFAULT_FILTER_SIZE = 3
DEFAULT_SIGMA_VALUE = 1
DEFAULT_K_VALUE = 1
DEFAULT_INCLUDE_DIAGONAL_TERMS = False
DEFAULT_COMPARE_MAX_VALUES = True
DEFAULT_NORMALIZATION_METHOD = 'unchanged'
DEFAULT_DELTA_T = 0.01

DEFAULT_HARRIS_K_VALUE = 0.05  # Empirically recommended k ∈ [0.04, 0.06] from Harris & Stephens (1988).
DEFAULT_HARRIS_RADIUS = 3
DEFAULT_LOW_THRESHOLD_CANNY = 0.04
DEFAULT_HIGH_THRESHOLD_CANNY = 0.1

# Noise #
DEFAULT_GAUSSIAN_MEAN = 0
DEFAULT_GAUSSIAN_SIGMA = 0.01
DEFAULT_RAYLEIGH_A = -0.125
DEFAULT_RAYLEIGH_B = 0.01
DEFAULT_ERLANG_A = 75
DEFAULT_ERLANG_B = 3
DEFAULT_EXPONENTIAL_DECAY = 50
DEFAULT_UNIFORM_A = -0.1
DEFAULT_UNIFORM_B = 0.1
DEFAULT_PEPPER = 0.001
DEFAULT_SALT = 0.001

# Thinning #
DEFAULT_THINNING_METHOD = "ZS"
DEFAULT_PRE_THINNING = True

# Morphology #
DEFAULT_STRUCTURING_ELEMENT = np.ones((3, 3), dtype=int)

# Frequency Domain #
DEFAULT_CUTOFF_FREQUENCY = 30       # pixels from DC in the shifted spectrum
DEFAULT_BUTTERWORTH_ORDER = 2       # filter order for Butterworth filters
DEFAULT_NOTCH_RADIUS = 10.0         # notch rejection radius in pixels of the spectrum
DEFAULT_HOMOMORPHIC_GAMMA_L = 0.25  # low-frequency gain  (illumination attenuation, < 1)
DEFAULT_HOMOMORPHIC_GAMMA_H = 2.0   # high-frequency gain (reflectance boost, > 1)
DEFAULT_HOMOMORPHIC_C = 1.0         # transition steepness constant
DEFAULT_HOMOMORPHIC_SIGMA = 30.0    # Gaussian σ for homomorphic filter (pixels of spectrum)