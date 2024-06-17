"""
Script Name - NASA_API.py

Purpose - Super class for smaller NASA API requests.

Created by Michael Samelsohn, 07/05/22
"""

# Imports #
import os
import subprocess
import requests

from abc import abstractmethod, ABCMeta
from Settings import api_settings
from Settings.settings import log


class NasaApi(metaclass=ABCMeta):
    def __init__(self, image_directory=api_settings.DEFAULT_IMAGE_DIRECTORY):
        """
        This class is used as a super class for usage of the NASA API. It includes basic operations such as the GET API
        request and image download using URL.

        :param image_directory: The directory where the image is to be saved at.
        """

        self._image_directory = self.__check_directory_exists(directory=image_directory)

    @property
    def image_directory(self):
        """
        Get the image directory.
        :return: The directory where the image is to be saved at.
        """
        return self._image_directory

    @image_directory.setter
    def image_directory(self, new_image_directory):
        """
        Set the image directory.
        :param new_image_directory: The new directory where the image is to be saved at.
        """
        self._image_directory = self.__check_directory_exists(directory=new_image_directory)

    @staticmethod
    def __check_directory_exists(directory: str) -> str:
        """
        Assert that the provided path exists. If not, a default value will be used.

        :param directory: The directory path.

        :return: The provided directory path if it exists, default directory path otherwise.
        """

        if os.path.exists(path=directory):
            log.debug("Changing image directory")
            return directory
        else:
            log.warning("New directory doesn't exist, will use default")
            return api_settings.DEFAULT_IMAGE_DIRECTORY

    @abstractmethod
    def _debug(self):
        """Log the class parameters (mainly for debugging purposes)."""
        log.info("Class parameters:")
        log.debug(f"The image directory is - {self._image_directory}")

    @staticmethod
    def get_request(url: str) -> dict | None:
        """
        Use API GET request with the specified URL.

        :param url: The URL used for the API GET request.
        :return: The response JSON in form of a dictionary.
        """

        log.debug(f"Requesting a GET API with the following URL - {url}")

        request = requests.get(url)
        if request.status_code != 200:
            log.error(f"Request failed with status code - {request.status_code}")
            return None
        log.info("Request is successful (status code - 200)")

        return request.json()

    def download_image_url(self, api_type: str, image_url_list: list, image_suffix="") -> bool:
        """
        Download the images based on the compiled URLs list and the API type.
        TODO: Need to add better image naming.

        :param api_type: The API type used for the images.
        :param image_url_list: List with all image URLs.
        :param image_suffix: The suffix for the image name.

        :return: True if download is successful, otherwise False.
        """

        match len(image_url_list):
            case 0:  # Empty list.
                log.error("Cannot download the images since there are none")
                return False
            case 1:  # Single image, no indexing required.
                log.debug(f"Image URL is - {image_url_list[0]}")
                image_path = os.path.join(self.image_directory,
                                          f"{api_type}{image_suffix}.{api_settings.API_IMAGE_DOWNLOAD_FORMATS[api_type]}")
                output = subprocess.run(f"curl -o {image_path} {image_url_list[0]}",
                                        capture_output=True, text=True).stderr
                log.print_data(data=output)
                log.info("Image downloaded successfully")
            case _:  # Multiple images, indexing required.
                image_index = 1
                for url in image_url_list:
                    log.debug(f"{image_index}) Image URL is - {url} ")
                    image_path = os.path.join(
                        self.image_directory,
                        f"{api_type}{image_suffix}.{api_settings.API_IMAGE_DOWNLOAD_FORMATS[api_type]}")
                    output = subprocess.run(f"curl -o {image_path} {url}",
                                            capture_output=True, text=True).stderr
                    log.print_data(data=output)
                    log.info("Image downloaded successfully")
                    image_index += 1

        # If we got to this point, the download was successful.
        return True
