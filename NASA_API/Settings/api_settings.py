"""
Script Name - api_settings.py

Purpose - Centralize all the constants and settings of the NASA API module.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import os
from Utilities.logger import Logger

# Logger settings #
verbosity_level = 3  # Setting the verbosity level.
log = Logger()       # Initiating the logger.

# Adding custom log levels.
log.add_custom_log_level("success", 25, "\x1b[32;1m")       # Bright Green.
log.add_custom_log_level("apod", 11, "\x1b[38;5;208m")      # Orange.
log.add_custom_log_level("epic", 12, "\x1b[38;5;5m")        # Magenta.
log.add_custom_log_level("mars", 13, "\x1b[38;5;160m")      # Red (Mars is red).
log.add_custom_log_level("nil", 14, "\x1b[38;5;33m")        # Blue.

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
RETRY_DELAY = 5      # Delay in seconds before retrying a failed download.
REQUEST_TIMEOUT = 30  # Timeout in seconds for all HTTP requests.
# Read the API key from the environment; fall back to a hard-coded demo key if the variable is absent.
API_KEY = f"api_key={os.environ.get('NASA_API_KEY', 'fymalkzvEUpMBhhBIpi39IQu0zqsjMy7K2AYhiwJ')}"
# Resolve the Images/ sibling directory relative to this settings file regardless of the working directory.
DEFAULT_IMAGE_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Images")
API_IMAGE_DOWNLOAD_FORMATS = {
    "APOD":  "JPG",
    "EPIC":  "png",
    "MARS":  "JPG",
    "NIL":   "JPG",
    "EARTH": "PNG",
}

# APOD (Astronomy Picture Of the Day) #
APOD_URL_PREFIX = "https://api.nasa.gov/planetary/apod?"
APOD_FIRST_DATE = "1995-06-16"  # Date of the first ever APOD entry.

# EPIC (Earth Polychromatic Imaging Camera) #
EPIC_URL_PREFIX = "https://epic.gsfc.nasa.gov/"
EPIC_URL_SUFFIX = "api/images.php"

# Mars Rovers #
MARS_URL_PREFIX = "https://api.nasa.gov/mars-photos/api/v1/"
MARS_ROVERS = ["Curiosity", "Opportunity", "Spirit"]
MARS_ROVER_DATE_RANGES = {
    # None end date means the mission is still active (use today's date as the upper bound).
    "Curiosity":   {"start": "2012-08-06", "end": None},
    "Opportunity": {"start": "2004-01-25", "end": "2018-06-11"},
    "Spirit":      {"start": "2004-01-04", "end": "2010-03-21"},
}

# NIL (NASA Image and Video Library) #
NIL_URL_PREFIX = "https://images-api.nasa.gov/search?"
NIL_MEDIA_TYPES = ["image", "audio"]
NIL_FIRST_YEAR = 1960  # Earliest valid year for NIL queries.