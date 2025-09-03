"""
Script Name - apod.py

Purpose - Download the APOD (Astronomy Picture Of the Day) image.
For full API documentation - https://api.nasa.gov/.

Created by Michael Samelsohn, 05/05/22.
"""

# Imports #
import re

from datetime import datetime
from NASA_API.Source.api_utilities import *


class APOD:
    def __init__(self, image_directory=DEFAULT_IMAGE_DIRECTORY):
        log.apod("Initializing the APOD class")

        self.image_directory = image_directory
        self.hd = False
        self._date = None

        self._apod_image = None

    @staticmethod
    def validate_date(date: str) -> bool:
        """
        Validates whether the provided date string is in the correct format and within an acceptable range.

        The date must:
        - Be in the 'YYYY-MM-DD' format.
        - Represent a valid calendar date (e.g., not February 30).
        - Fall within the range from June 16, 1995 to September 1, 2025 (inclusive).

        :param date: The date string to validate.

        :return: True if the date is valid and within the specified range, False otherwise.
        """

        # Match YYYY-MM-DD format.
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date):
            log.error("Incorrect date pattern (acceptable - YYYY-MM-DD)")
            return False

        try:
            date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            log.error("Invalid date")
            return False

        start = datetime(1995, 6, 16)
        end = datetime.today()

        return start <= date <= end

    @property
    def date(self):
        """Get the image date."""
        return self._date

    @date.setter
    def date(self, new_date: str):
        """
        Set the image date, only if validated.

        :param new_date: The new image date.
        """

        log.apod(f"Validating the date - {new_date}")
        if self.validate_date(date=new_date):
            log.success("Date validated")
            self._date = new_date
        else:
            log.error("Date not valid")

    @property
    def apod_image(self):
        return self._apod_image

    def astronomy_picture_of_the_day(self) -> bool:
        """
        Save APOD image in the selected directory.
        Note - The images are saved as .JPG files.
        """

        log.apod("Retrieving APOD (Astronomy Picture Of the Day) image")

        log.apod("Checking if a date is set")
        if self._date is None:
            log.error("No date set")
            return False

        # Perform the API request.
        json_object = get_request(url=f"{APOD_URL_PREFIX}date={self._date}&{API_KEY}")
        if json_object is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return False

        log.apod("IMAGE INFORMATION:")
        # Cleaning the dictionary values from unnecessary \n characters.
        log.print_data(data={k: v.replace('\n', '') for k, v in json_object.items()}, log_level="apod")

        # Download and save the image to the relevant directory.
        self._apod_image = download_image_url(
            image_directory=self.image_directory, api_type="APOD",
            image_url_list=[json_object["hdurl"] if self.hd else json_object["url"]], image_suffix=f"_{self._date}")

        return True

