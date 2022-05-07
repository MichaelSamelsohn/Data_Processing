"""
Script Name - Settings.py

Purpose - Centralize all the constants and settings of the project.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import os

# API Related #
API_KEY = "api_key=fymalkzvEUpMBhhBIpi39IQu0zqsjMy7K2AYhiwJ"
DEFAULT_IMAGE_DIRECTORY = os.path.abspath('../Images')

# APOD (Astronomy Picture Of the Day) #
APOD_URL_PREFIX = "https://api.nasa.gov/planetary/apod?"
APOD_DEFAULT_DATE = "1996-04-27"
APOD_DEFAULT_HD = False
APOD_DOWNLOAD_METHOD = "wget -O"
APOD_IMAGE_FORMAT = "JPG"

# EPIC (Earth Polychromatic Imaging Camera) #
EPIC_URL_PREFIX = "https://epic.gsfc.nasa.gov/"
EPIC_URL_SUFFIX = "api/images.php"
EPIC_NUMBER_OF_PHOTOS_TO_COLLECT = 2
EPIC_DOWNLOAD_METHOD = "curl -o"
EPIC_IMAGE_FORMAT = "png"
