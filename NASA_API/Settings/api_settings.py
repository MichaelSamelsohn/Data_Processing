"""
Script Name - api_settings.py

Purpose - Centralize all the constants and settings of the API directory.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import os
from Utilities.logger import Logger

# Logger settings #
verbosity_level = 2  # Setting the verbosity level.
log = Logger()       # Initiating the logger.

# Adding custom levels.
log.add_custom_log_level("success", 25, "\x1b[32;1m")       # Bright Green.
log.add_custom_log_level("apod", 11, "\x1b[38;5;208m")      # Orange.
log.add_custom_log_level("epic", 12, "\x1b[38;5;5m")        # Magenta.

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
CONNECTION_CHECK_URL = "https://www.google.com/"
CONNECTION_CHECK_TIMEOUT = 5
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
APOD_DEFAULT_DATE = "1996-04-27"
APOD_DEFAULT_HD = False

# EPIC (Earth Polychromatic Imaging Camera) #
EPIC_URL_PREFIX = "https://epic.gsfc.nasa.gov/"
EPIC_URL_SUFFIX = "api/images.php"
EPIC_DEFAULT_NUMBER_OF_PHOTOS_TO_COLLECT = 2

# Mars Rovers #
MARS_URL_PREFIX = "https://api.nasa.gov/mars-photos/api/v1/"
MARS_DEFAULT_NUMBER_OF_PHOTOS_TO_COLLECT = 4
MARS_DEFAULT_ROVER = "Curiosity"
MARS_ROVERS = ["Curiosity", "Opportunity", "Spirit"]
MARS_DEFAULT_DATE = "2021-04-27"

# NIL (NASA Imaging Library) #
NIL_URL_PREFIX = "https://images-api.nasa.gov/search?"
NIL_MEDIA_TYPES = ["image", "audio"]
NIL_DEFAULT_MEDIA_TYPE = "image"
NIL_DEFAULT_SEARCH_YEARS = [1960, 2022]
