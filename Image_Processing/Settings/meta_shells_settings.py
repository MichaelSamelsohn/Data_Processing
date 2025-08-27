"""
Script Name - image_settings.py

Purpose - Centralize all the constants and settings of the Image_Processing directory.

Created by Michael Samelsohn, 06/05/25
"""

DEBUG_MODE = True
DISPLAY_TIME = 5

NUMBER_OF_COEFFICIENTS = 100
SCALING_FACTOR = 15
MULTIFOIL_PARAMETERS = {
    'a': 6,
    'b': 0.25,
    'lobes': 3
}
PROCESSING_PARAMETERS = {
    'high_threshold': 0.75,
    'low_threshold': 0.75,
    'filter_size': 45,
    'global_threshold': 0.1,
    'thinning_method': 'GH1'
}
