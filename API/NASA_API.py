# Imports #
import os
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
