"""
Script Name - api_settings.py

Purpose - Centralize all the constants and settings of the API directory.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import os
from Utilities.logger import Logger

# Logger settings #
verbosity_level = 3  # Setting the verbosity level.
log = Logger()       # Initiating the logger.

# Adding custom levels.
log.add_custom_log_level("success", 25, "\x1b[32;1m")       # Bright Green.
log.add_custom_log_level("apod", 11, "\x1b[38;5;208m")      # Orange.
log.add_custom_log_level("epic", 12, "\x1b[38;5;5m")        # Magenta.
log.add_custom_log_level("mars", 13, "\x1b[38;5;5m")        # Magenta.
log.add_custom_log_level("nil", 14, "\x1b[38;5;208m")       # Orange.

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

# API Related #
MAX_RETRIES = 3
RETRY_DELAY = 5  # Delay in seconds before retrying.
API_KEY = "api_key=fymalkzvEUpMBhhBIpi39IQu0zqsjMy7K2AYhiwJ"
DEFAULT_IMAGE_DIRECTORY = os.path.abspath('./Images')
API_IMAGE_DOWNLOAD_FORMATS = {
    "APOD": "JPG",
    "EPIC": "png",
    "MARS": "JPG",
    "NIL": "JPG",
}

# APOD (Astronomy Picture Of the Day) #
APOD_URL_PREFIX = "https://api.nasa.gov/planetary/apod?"
APOD_DEFAULT_HD = False

# EPIC (Earth Polychromatic Imaging Camera) #
EPIC_URL_PREFIX = "https://epic.gsfc.nasa.gov/"
EPIC_URL_SUFFIX = "api/images.php"

# Mars Rovers #
MARS_URL_PREFIX = "https://api.nasa.gov/mars-photos/api/v1/"
MARS_ROVERS = ["Curiosity", "Opportunity", "Spirit"]

# NIL (NASA Imaging Library) #
NIL_URL_PREFIX = "https://images-api.nasa.gov/search?"
NIL_MEDIA_TYPES = ["image", "audio"]
