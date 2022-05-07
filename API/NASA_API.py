"""
Script Name - NASA_API.py

Purpose - Super class for smaller NASA API requests.

Created by Michael Samelsohn, 07/05/22
"""

# Imports #
import os
import subprocess

import requests

from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


def get_request(url):
    """
    Use API GET request with the specified URL.

    :param url: The URL used for the API GET request.
    :return: The response JSON in form of a dictionary.
    """

    log.debug(f"The URL is - {url}")

    request = requests.get(url)

    if request.status_code != 200:
        log.error(f"Request failed with status code - {request.status_code}")
        return None
    log.info("request is successful (status code - 200)")

    return request.json()


def download_image_url(api_type, image_url, image_suffix=""):
    """
    Download and save the images to the specified directory.

    :param api_type: The API request type.
    :param image_url: The image(s) URL.
    :param image_suffix: The image suffix (Added to the name of the image).
    """

    match api_type:
        case "APOD":
            log.debug(f"Image URL is - {image_url}")
            output = subprocess.run(
                f"{Settings.APOD_DOWNLOAD_METHOD} {api_type}{image_suffix}.{Settings.APOD_IMAGE_FORMAT} {image_url}",
                shell=True, check=True, capture_output=True)
            log.print_data(data=output.stderr.decode("utf-8").split("\n"))
            log.info("Image downloaded successfully")
        case "EPIC":
            image_index = 1
            for url in image_url:
                log.debug(f"{image_index}) Image URL is - {url} ")
                output = subprocess.run(
                    f"{Settings.EPIC_DOWNLOAD_METHOD} EPIC_{image_index}.{Settings.EPIC_IMAGE_FORMAT} {url}",
                    shell=True, check=True, capture_output=True)
                log.print_data(data=output.stderr.decode("utf-8").split("\n"))
                log.info("Image downloaded successfully")
                image_index += 1


class NASA_API:
    def __init__(self, image_directory):
        """
        :param image_directory: The directory where the image is to be saved at.
        """
        self.__image_directory = image_directory
        self.__check_directory_existence()

    def __check_directory_existence(self):
        """
        Change the path to the specified directory (relevant for later when the images are being saved).
        If specified path does not exist, default to 'Images' directory.
        """

        log.debug(f"The selected directory is - {self.__image_directory}")
        try:
            log.debug("Changing working directory to given one")
            os.chdir(self.__image_directory)
        except FileNotFoundError:
            log.error(f"The specified directory, {self.__image_directory}, doesn't exist")
            log.debug("Saving the image to the images directory")
            self.__image_directory = Settings.DEFAULT_IMAGE_DIRECTORY
            os.chdir(path=self.__image_directory)

    @property
    def image_directory(self):
        """
        Get the image directory.
        :return: The directory where the image is to be saved at.
        """
        return self.__image_directory

    @image_directory.setter
    def image_directory(self, new_directory):
        """
        Set the image directory.
        :param new_directory: The new directory where the image is to be saved at.
        """
        self.__image_directory = new_directory
        self.__check_directory_existence()

    def log_class_parameters(self):
        """
        Log the class parameters (mainly for debugging purposes).
        """
        log.debug(f"The image directory is - {self.__image_directory}")
