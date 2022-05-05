"""
Script Name - APOD.py

Purpose - Download the APOD (Astronomy Picture Of the Day) image.
For full API documentation - https://api.nasa.gov/.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import requests
import os

from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


def astronomy_picture_of_the_day(image_directory, date, hd=False):
    """
    Save APOD image in the selected directory.
    Note - The images are saved as .JPG files.

    :param image_directory: The directory where the image is to be saved at.
    :param date: Date of the image. Acceptable format is - "YYYY-MM-DD".
    :param hd: Boolean indicating the quality of the image.
    """

    log.debug("Retrieving APOD (Astronomy Picture Of the Day) image")
    log.debug(f"The selected directory is - {image_directory}")
    log.debug(f"Selected date is - {date}")
    log.debug("Date format has to be YYYY-MM-DD of an existing date")
    log.debug(f"HD version of the image - {hd}")

    image_url = get_apod_url(date=date, hd=hd)
    log.debug("Changing working directory to given one")
    try:
        os.chdir(image_directory)
    except FileNotFoundError:
        log.error(f"The specified directory, {image_directory}, doesn't exist")
        log.debug("Saving the image to the images directory")
        os.chdir(path=os.path.abspath("../Images"))
    log.debug(f"Image URL is - {image_url}")
    output = os.popen(f"wget -O APOD_{date}.JPG {image_url}").readlines()
    log.print_data(data=output)


def get_apod_url(date, hd):
    """
    Get APOD image URL using API request.

    :param date: Date of the image. Acceptable format is - "YYYY-MM-DD".
    :param hd: Boolean indicating the quality of the image.

    :return: APOD image URL.
    """

    log.debug("Using API GET request to receive the JSON with the relevant information")

    url_suffix = f"date={date}&{Settings.API_KEY}"
    full_url = Settings.APOD_URL_PREFIX + url_suffix
    log.debug(f"The API request is - {full_url}")
    request = requests.get(full_url)
    log.debug(f"Request status code is - {request.status_code}")
    if request.status_code == 400:
        log.error("Bad date format or non-existing date given")
        exit(10)
    assert request.status_code == 200, f"Status code is - {request.status_code}"
    log.info("request is successful")

    json_object = request.json()
    log.debug("IMAGE INFORMATION:")
    log.print_data(data=json_object)

    return json_object["hdurl"] if hd else json_object["url"]
