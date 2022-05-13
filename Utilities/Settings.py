"""
Script Name - Settings.py

Purpose - Centralize all the constants and settings of the project.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import os

# API Related #
CONNECTION_CHECK_URL = "https://www.google.com/"
CONNECTION_CHECK_TIMEOUT = 5
API_KEY = "api_key=fymalkzvEUpMBhhBIpi39IQu0zqsjMy7K2AYhiwJ"
DEFAULT_IMAGE_DIRECTORY = os.path.abspath('../Images')
IMAGE_DOWNLOAD_SETTINGS = {
    "APOD": {"DOWNLOAD_METHOD": "wget -O", "IMAGE_FORMAT": "JPG"},
    "EPIC": {"DOWNLOAD_METHOD": "curl -o", "IMAGE_FORMAT": "png"},
    "MARS": {"DOWNLOAD_METHOD": "wget -O", "IMAGE_FORMAT": "JPG"},
    "NIL": {"DOWNLOAD_METHOD": "wget -O", "IMAGE_FORMAT": "JPG"},
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

# Image Class #
DEFAULT_IMAGE_LENA = os.path.abspath('../Images/Lena.png')
