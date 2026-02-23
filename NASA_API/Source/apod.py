"""
Script Name - apod.py

Purpose - Download the APOD (Astronomy Picture Of the Day) image.
For full API documentation - https://api.nasa.gov/.

Created by Michael Samelsohn, 05/05/22.
"""

# Imports #
import re

from datetime import datetime
from NASA_API.Settings.api_settings import (
    log, APOD_URL_PREFIX, API_KEY, APOD_FIRST_DATE, DEFAULT_IMAGE_DIRECTORY
)
from NASA_API.Source.api_utilities import get_request, download_image_url


class APOD:
    def __init__(self, image_directory=DEFAULT_IMAGE_DIRECTORY, date: str = None, hd: bool = False) -> None:
        log.apod("Initializing the APOD class")

        self.image_directory = image_directory
        self.date = date
        self.hd = hd
        self._apod_image = None

    @staticmethod
    def validate_date(date: str) -> bool:
        """
        Validate whether the provided date string is in the correct format and within the APOD archive range.

        The date must:
        - Be in the 'YYYY-MM-DD' format.
        - Represent a valid calendar date (e.g., not February 30).
        - Fall within the APOD archive range: June 16, 1995 (first APOD entry) to today (inclusive).

        :param date: The date string to validate.

        :return: True if the date is valid and within the APOD range, False otherwise.
        """

        log.debug(f"Validating date format - {date}")

        # Step (1) - Verify the string matches the YYYY-MM-DD pattern.
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            log.error("Incorrect date format (expected - YYYY-MM-DD)")
            return False

        # Step (2) - Verify the date represents a real calendar date.
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            log.error("Invalid calendar date (e.g., February 30 does not exist)")
            return False

        # Step (3) - Verify the date falls within the APOD archive range.
        start = datetime.strptime(APOD_FIRST_DATE, "%Y-%m-%d")
        end = datetime.today()

        if not (start <= parsed_date <= end):
            log.error(f"Date is outside the APOD archive range ({APOD_FIRST_DATE} to today)")
            return False

        return True

    @property
    def apod_image(self):
        """Get the path of the most recently downloaded APOD image."""
        return self._apod_image

    def astronomy_picture_of_the_day(self) -> bool:
        """
        Download the APOD image for the configured date and save it to the image directory.

        Notes:
        - Images are saved in JPEG format.
        - If the APOD entry for the selected date is a video (not an image), the download is skipped.
        - If HD is requested but an HD version is unavailable, the standard resolution image is used instead.

        :return: True if the image was downloaded successfully, False otherwise.
        """

        log.apod("Retrieving APOD (Astronomy Picture Of the Day) image")

        # Step (1) - Verify a date has been configured.
        log.apod("Checking if a date is set and valid")
        if not self.validate_date(date=self.date):
            log.error("No date set - use the 'date' property before calling this method")
            return False

        # Step (2) - Perform the API request.
        json_object = get_request(url=f"{APOD_URL_PREFIX}date={self.date}&{API_KEY}")
        if json_object is None:
            log.error("API request failed - check logs for details")
            return False

        # Step (3) - Log image metadata.
        log.apod("APOD INFORMATION:")
        log.print_data(data={k: str(v).replace('\n', '') for k, v in json_object.items()}, log_level="apod")

        # Step (4) - Skip download if the APOD entry for this date is a video.
        media_type = json_object.get("media_type", "image")
        if media_type != "image":
            log.warning(f"APOD for {self.date} is a '{media_type}', not an image - download skipped")
            return False

        # Step (5) - Resolve the image URL (HD with automatic fallback to standard resolution).
        if self.hd:
            image_url = json_object.get("hdurl") or json_object.get("url")
            if not json_object.get("hdurl"):
                log.warning("HD image not available for this date - falling back to standard resolution")
        else:
            image_url = json_object.get("url")

        if not image_url:
            log.error("No valid image URL found in the API response")
            return False

        # Step (6) - Download and save the image.
        self._apod_image = download_image_url(
            image_directory=self.image_directory,
            api_type="APOD",
            image_url_list=[image_url],
            image_suffix=f"_{self.date}"
        )

        return self._apod_image is not None