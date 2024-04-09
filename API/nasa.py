"""
Script Name - NASA_API.py

Purpose - Super class for smaller NASA API requests.

Created by Michael Samelsohn, 07/05/22
"""

# Imports #
import os
import subprocess
import requests

from abc import abstractmethod
from Utilities import Settings
from Utilities.logger import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


class NasaApi:
    def __init__(self, image_directory):
        """
        :param image_directory: The directory where the image is to be saved at.
        """

        self._image_directory = image_directory
        self.__check_directory_existence()

    def __check_directory_existence(self):
        """
        Change the path to the specified directory (relevant for later when the images are being saved).
        If specified path does not exist, default to 'Images' directory.
        """

        log.debug(f"The selected directory is - {self._image_directory}")
        try:
            log.debug("Changing working directory to given one")
            os.chdir(self._image_directory)
        except (FileNotFoundError, OSError, TypeError):
            log.error(f"The specified directory, {self._image_directory}, doesn't exist")
            log.debug("Saving the image to the images directory")
            self._image_directory = Settings.DEFAULT_IMAGE_DIRECTORY
            os.chdir(path=self._image_directory)

    @property
    def image_directory(self):
        """
        Get the image directory.
        :return: The directory where the image is to be saved at.
        """
        return self._image_directory

    @image_directory.setter
    def image_directory(self, new_directory):
        """
        Set the image directory.
        :param new_directory: The new directory where the image is to be saved at.
        """
        self._image_directory = new_directory
        self.__check_directory_existence()

    @abstractmethod
    def log_class_parameters(self):
        """
        Log the class parameters (mainly for debugging purposes).
        """
        log.info("Class parameters:")
        log.debug(f"The image directory is - {self._image_directory}")

    @staticmethod
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

    @staticmethod
    def download_image_url(api_type, image_url_list, image_suffix=""):
        """
        Download the images based on the compiled URLs list and the API type.
        TODO: Need to add better image naming.

        :param api_type: The API type used for the images.
        :param image_url_list: List with all image URLs.
        :param image_suffix: The suffix for the image name.
        """

        match len(image_url_list):
            case 0:  # Empty list.
                log.error("Cannot download the images since there are none")
                return False
            case 1:  # Single image, no indexing required.
                log.debug(f"Image URL is - {image_url_list[0]}")
                output = subprocess.run(
                    f"curl -o "
                    f"{api_type}{image_suffix}.{Settings.API_IMAGE_DOWNLOAD_FORMATS[api_type]} {image_url_list[0]}",
                    shell=True, check=True, capture_output=True)
                log.print_data(data=output.stderr.decode("utf-8").split("\n"))
                log.info("Image downloaded successfully")
            case _:  # Multiple images, indexing required.
                image_index = 1
                for url in image_url_list:
                    log.debug(f"{image_index}) Image URL is - {url} ")
                    output = subprocess.run(
                        f"curl -o "
                        f"{api_type}{image_suffix}_{image_index}.{Settings.API_IMAGE_DOWNLOAD_FORMATS[api_type]} {url}",
                        shell=True, check=True, capture_output=True)
                    log.print_data(data=output.stderr.decode("utf-8").split("\n"))
                    log.info("Image downloaded successfully")
                    image_index += 1

        log.info("Finished downloading image(s) successfully")
        return True
