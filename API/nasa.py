"""
Script Name - NASA_API.py

Purpose - Super class for smaller NASA API requests.

Created by Michael Samelsohn, 07/05/22
"""

# Imports #
import os
import subprocess
import time
import requests

from abc import abstractmethod, ABCMeta
from Settings import api_settings
from Settings.api_settings import MAX_RETRIES, RETRY_DELAY
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

        :param api_type: The API type used for the images.
        :param image_url_list: List with all image URLs.
        :param image_suffix: The suffix for the image name.

        :return: True if download is successful, otherwise False.
        """

        log.debug("Check if the image URL list is empty")
        if len(image_url_list) == 0:
            log.error("Cannot download the images since there are none")
            return False

        image_index = 1
        for url in image_url_list:
            # Preparing image path.
            image_path = os.path.join(self.image_directory,
                                      f"{api_type}{image_suffix}.{api_settings.API_IMAGE_DOWNLOAD_FORMATS[api_type]}")

            # Trying to download the image(s) with retries.
            for attempt in range(MAX_RETRIES):
                log.debug(f"{image_index}) Attempting to download image from URL: "
                          f"{url} (Attempt {attempt + 1}/{MAX_RETRIES})")

                # Running the curl command to download the image.
                output = subprocess.run(f"curl -o {image_path} {url}", capture_output=True, text=True)

                # Checking if the download was successful (curl return code is 0).
                if output.returncode == 0:
                    # Verifying the image was downloaded (check if the file exists).
                    if os.path.exists(image_path):
                        log.info(f"Image downloaded successfully: {image_path}")
                        break
                    else:
                        log.error(f"Image download failed: {image_path} (file not found after download)")
                else:
                    # If curl failed, logging the error and retrying.
                    log.error(f"Error downloading image. curl returned {output.returncode}: {output.stderr}")
                    if attempt < MAX_RETRIES - 1:
                        log.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)  # Buffer time before retrying.
                    else:
                        log.error(f"Failed to download image after {MAX_RETRIES} attempts. Moving to next image.")

            image_index += 1  # Incrementing the index for the next image.
        return True
