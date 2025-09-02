"""
Script Name - epic.py

Purpose - Download the Mars rovers image(s).
For full API documentation - https://api.nasa.gov/

Created by Michael Samelsohn, 08/05/22
"""

# Imports #
import re

from datetime import datetime
from NASA_API.Source.api_utilities import *


class MARS:
    def __init__(self, image_directory=DEFAULT_IMAGE_DIRECTORY):
        """
        :param image_directory: The directory where the image is to be saved at.
        """

        log.mars("Initializing the MARS class")

        self.image_directory = image_directory
        self._rover = None
        self._date = None

        self._mars_image = None

    @property
    def rover(self):
        """
        Get the rover name.
        """
        return self._rover

    @rover.setter
    def rover(self, new_rover: str):
        """
        Set the rover name.
        :param new_rover: The new rover name.
        """

        log.mars(f"Selected rover is - {new_rover}")
        if new_rover not in MARS_ROVERS:
            log.error(f"The selected rover, {new_rover}, is not available (options are - {MARS_ROVERS})")
        else:
            self._rover = new_rover

    @staticmethod
    def validate_date(date: str, rover: str) -> bool:
        """
        Validates whether the provided date string is in the correct format and within an acceptable range.

        The date must:
        - Be in the 'YYYY-MM-DD' format.
        - Represent a valid calendar date (e.g., not February 30).
        - Fall within the range from June 16, 1995 to September 1, 2025 (inclusive).

        :param date: The date string to validate.
        :param rover: The rover.

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

        start, end = None, None
        match rover:
            case "Opportunity":
                start = datetime(2004, 1, 25)
                end = datetime(2018, 6, 11)
            case "Spirit":
                start = datetime(2004, 1, 4)
                end = datetime(2010, 3, 21)
            case "Curiosity":
                start = datetime(2012, 8, 6)
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

        if not self._rover:
            log.error(f"No rover provided (options are - {MARS_ROVERS})")

        log.mars(f"Validating the date - {new_date}")
        if self.validate_date(date=new_date, rover=self._rover):
            log.success("Date validated")
            self._date = new_date
        else:
            log.error("Date not valid, providing rover manifest")
            self.mars_rover_manifest()

    @property
    def mars_image(self):
        return self._mars_image

    def mars(self):
        """
        Save Mars rover image(s) in the selected directory.
        Note - The images are saved as .JPG files.
        """

        log.mars("Retrieving Mars rover image")

        log.mars("Checking if a date is set")
        if self._date is None:
            log.error("No date set")
            return False

        # Perform the API request.
        json_object = get_request(url=f"{MARS_URL_PREFIX}rovers/{self._rover}/photos?earth_date={self._date}&{API_KEY}")
        if json_object is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return False

        # Download and save the image to the relevant directory.
        self._mars_image = download_image_url(image_directory=self.image_directory, api_type="MARS",
                                              image_url_list=[json_object["photos"][0]["img_src"]],
                                              image_suffix=f"_{self._rover}_{self._date}")

        return True

    def mars_rover_manifest(self):
        """
        Get the Mars rover manifest, mainly for debugging purposes.

        :return: Dictionary with the rover manifest.
        """

        # Perform the API request to get the rover manifest.
        rover_manifest = get_request(url=f"{MARS_URL_PREFIX}manifests/{self._rover}?{API_KEY}")
        if rover_manifest is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return False

        rover_information = {
            "landing_date": rover_manifest["photo_manifest"]["landing_date"],
            "max_date": rover_manifest["photo_manifest"]["max_date"],
            "max_sol": rover_manifest["photo_manifest"]["max_sol"],
            "status": rover_manifest["photo_manifest"]["status"],
            "total_photos": rover_manifest["photo_manifest"]["total_photos"]
        }

        # Log the rover information.
        log.mars("ROVER INFORMATION:")
        log.mars(f"rover - {self._rover}")
        log.print_data(data=rover_information, log_level="mars")

        return rover_information
