"""
Script Name - image_settings.py

Purpose - Centralize all the constants and settings of the Image_Processing directory.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import os

# Image Class #
DEFAULT_IMAGE_LENA = os.path.abspath('../Images/Lena.png')
GONZALES_WOODS_BOOK = "Digital Image Processing (4th edition) - Gonzales & Woods"

# Intensity Transformations #
DEFAULT_THRESHOLD_VALUE = 0.5
DEFAULT_GAMMA_VALUE = 2
DEFAULT_DEGREE_OF_REDUCTION = 4
DEFAULT_BIT_PLANE = 4
DEFAULT_HISTOGRAM_NORMALIZATION = False

# Filter Types #
BOX_FILTER = "box"
GAUSSIAN_FILTER = "gaussian"

# Padding Types #
ZERO_PADDING = "zero_padding"

# Morphological Operations #
EROSION = "erosion"
DILATION = "dilation"
OPENING = "opening"
CLOSING = "closing"


# Common #
DEFAULT_SCALING_FACTOR = 255
DEFAULT_PADDING_SIZE = 1
DEFAULT_PADDING_TYPE = ZERO_PADDING
DEFAULT_FILTER_TYPE = BOX_FILTER
DEFAULT_FILTER_SIZE = 3
DEFAULT_INCLUDE_DIAGONAL_TERMS = False
DEFAULT_CONTRAST_STRETCHING = False
DEFAULT_DELTA_T = 0.01
DEFAULT_CONSTANT = -1
