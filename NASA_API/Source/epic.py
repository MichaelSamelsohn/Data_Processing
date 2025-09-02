"""
Script Name - epic.py

Purpose - Download the EPIC (Earth Polychromatic Imaging Camera) image(s).
For full API documentation - https://epic.gsfc.nasa.gov/about/api.

Created by Michael Samelsohn, 07/05/22.
"""


# Imports #
from NASA_API.Source.api_utilities import *


class EPIC:
    def __init__(self, image_directory=DEFAULT_IMAGE_DIRECTORY):
        """
        :param image_directory: The directory where the image is to be saved at.
        """

        log.epic("Initializing the EPIC class")

        self.image_directory = image_directory
        self._epic_image = None

    @property
    def epic_image(self):
        return self._epic_image

    def earth_polychromatic_imaging_camera(self):
        """
        Save EPIC image(s) in the selected directory.
        Note - The images are saved as .png files.
        """

        log.epic("Retrieving EPIC (Earth Polychromatic Imaging Camera) image")

        # Perform the API request.
        json_object = get_request(url=f"{EPIC_URL_PREFIX}{EPIC_URL_SUFFIX}")
        if json_object is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return False

        log.epic("Processing the response information")
        image = json_object[0]  # Take the first image.
        year, month, day = self.reformat_images_url(image["date"])
        image_url = (EPIC_URL_PREFIX +
                     "archive/natural/" + year + "/" + month + "/" + day + "/png/" + image["image"] + ".png")

        # Download and save the image to the relevant directory.
        self._epic_image = download_image_url(image_directory=self.image_directory, api_type="EPIC",
                                              image_url_list=[image_url])

        return True

    @staticmethod
    def reformat_images_url(image_date: str) -> tuple[str, str, str]:
        """
        Extract the date and time to later form the correct image URL.

        :param image_date: The date of the image (from the request response dictionary).

        :return: Tuple of year, month and date of the image.
        """

        log.epic("Extracting date and time information for image URL")

        date_and_time = image_date.split(" ")
        date_only = date_and_time[0].split("-")
        year = date_only[0]
        month = date_only[1]
        day = date_only[2]
        return year, month, day
