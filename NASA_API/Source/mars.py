"""
Script Name - mars.py

Purpose - Download Mars rover image(s) from the NASA Mars Rover Photos API.
For full API documentation - https://api.nasa.gov/

Created by Michael Samelsohn, 08/05/22
"""

# Imports #
import re

from datetime import datetime
from NASA_API.Settings.api_settings import (
    log, MARS_URL_PREFIX, API_KEY, MARS_ROVERS, MARS_ROVER_DATE_RANGES, DEFAULT_IMAGE_DIRECTORY
)
from NASA_API.Source.api_utilities import get_request, download_image_url


class MARS:
    def __init__(self, image_directory=DEFAULT_IMAGE_DIRECTORY):
        log.mars("Initializing the MARS class")

        self.image_directory = image_directory
        self._rover = None
        self._date = None
        self._mars_image = None

    @property
    def rover(self):
        """Get the selected Mars rover name."""
        return self._rover

    @rover.setter
    def rover(self, new_rover: str):
        """
        Set the rover name. Must be one of the supported rover names.

        :param new_rover: Rover name (e.g., 'Curiosity', 'Opportunity', 'Spirit').
        """

        log.mars(f"Setting rover - {new_rover}")
        if new_rover not in MARS_ROVERS:
            log.error(f"Unknown rover '{new_rover}' - available options: {MARS_ROVERS}")
        else:
            log.success(f"Rover set to '{new_rover}'")
            self._rover = new_rover

    @staticmethod
    def validate_date(date: str, rover: str) -> bool:
        """
        Validate whether the provided date string is in the correct format and within the rover's mission range.

        The date must:
        - Be in the 'YYYY-MM-DD' format.
        - Represent a valid calendar date (e.g., not February 30).
        - Fall within the selected rover's Earth-date mission range.

        Mission date ranges:
        - Curiosity:   2012-08-06 to today (mission ongoing).
        - Opportunity: 2004-01-25 to 2018-06-11 (mission ended).
        - Spirit:      2004-01-04 to 2010-03-21 (mission ended).

        :param date: The date string to validate.
        :param rover: The rover name. Must be one of MARS_ROVERS.

        :return: True if the date is valid and within the rover's mission range, False otherwise.
        """

        log.debug(f"Validating Mars date '{date}' for rover '{rover}'")

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

        # Step (3) - Look up the rover's mission date range.
        if rover not in MARS_ROVER_DATE_RANGES:
            log.error(f"Unknown rover '{rover}' - cannot determine mission date range")
            return False

        date_range = MARS_ROVER_DATE_RANGES[rover]
        start = datetime.strptime(date_range["start"], "%Y-%m-%d")
        # A None end date means the rover is still active; use today as the upper bound.
        end = datetime.today() if date_range["end"] is None else datetime.strptime(date_range["end"], "%Y-%m-%d")

        if not (start <= parsed_date <= end):
            end_label = "today" if date_range["end"] is None else date_range["end"]
            log.error(f"Date is outside the '{rover}' mission range ({date_range['start']} to {end_label})")
            return False

        return True

    @property
    def date(self):
        """Get the configured query Earth date."""
        return self._date

    @date.setter
    def date(self, new_date: str):
        """
        Set the query Earth date after validation against the selected rover's mission range.
        A rover must be set before a date can be set.

        :param new_date: Date string in 'YYYY-MM-DD' format.
        """

        # A rover must be set before a date can be validated against its mission range.
        if self._rover is None:
            log.error(f"No rover set - select a rover before setting a date (options: {MARS_ROVERS})")
            return

        log.mars(f"Validating date - {new_date}")
        if self.validate_date(date=new_date, rover=self._rover):
            log.success("Date validated successfully")
            self._date = new_date
        else:
            log.error("Date validation failed - retrieving rover manifest for reference")
            self.mars_rover_manifest()

    @property
    def mars_image(self):
        """Get the path of the most recently downloaded Mars rover image."""
        return self._mars_image

    def mars(self, max_photos: int = 1) -> bool:
        """
        Download Mars rover image(s) for the configured rover and date.

        :param max_photos: Maximum number of photos to download (default is 1). Pass -1 to download all
                           available photos for the given date.

        Notes:
        - Images are saved in JPEG format.
        - When multiple photos are downloaded, filenames are suffixed with a numeric index.

        :return: True if at least one image was downloaded successfully, False otherwise.
        """

        log.mars("Retrieving Mars rover image(s)")

        # Step (1) - Verify a rover and a date have been configured.
        log.mars("Checking if a rover is set")
        if self._rover is None:
            log.error("No rover set - use the 'rover' property before calling this method")
            return False

        log.mars("Checking if a date is set")
        if self._date is None:
            log.error("No date set - use the 'date' property before calling this method")
            return False

        # Step (2) - Perform the API request.
        json_object = get_request(
            url=f"{MARS_URL_PREFIX}rovers/{self._rover}/photos?earth_date={self._date}&{API_KEY}"
        )
        if json_object is None:
            log.error("API request failed - check logs for details")
            return False

        # Step (3) - Verify photos are available for the requested date.
        photos = json_object.get("photos", [])
        if not photos:
            log.warning(f"No photos available for rover '{self._rover}' on {self._date}")
            return False

        log.mars(f"Found {len(photos)} photo(s) for rover '{self._rover}' on {self._date}")

        # Step (4) - Select the subset of photos to download.
        if max_photos != -1:
            photos = photos[:max_photos]

        image_urls = [photo["img_src"] for photo in photos]
        log.mars(f"Downloading {len(image_urls)} photo(s)")

        # Step (5) - Download and save the image(s).
        self._mars_image = download_image_url(
            image_directory=self.image_directory,
            api_type="MARS",
            image_url_list=image_urls,
            image_suffix=f"_{self._rover}_{self._date}"
        )

        return self._mars_image is not None

    def mars_rover_manifest(self) -> dict | None:
        """
        Retrieve and log the mission manifest for the selected rover.

        The manifest includes the rover's landing date, last active date, total photo count, and
        mission status. Useful for determining valid date ranges when date validation fails.

        :return: Dictionary with key rover manifest fields, or None if no rover is set or the request fails.
        """

        if self._rover is None:
            log.error("No rover set - cannot retrieve manifest")
            return None

        log.mars(f"Retrieving mission manifest for rover '{self._rover}'")

        # Perform the API request to retrieve the manifest.
        response = get_request(url=f"{MARS_URL_PREFIX}manifests/{self._rover}?{API_KEY}")
        if response is None:
            log.error("API request failed - check logs for details")
            return None

        manifest = response.get("photo_manifest", {})
        rover_information = {
            "landing_date": manifest.get("landing_date"),
            "max_date":     manifest.get("max_date"),
            "max_sol":      manifest.get("max_sol"),
            "status":       manifest.get("status"),
            "total_photos": manifest.get("total_photos"),
        }

        log.mars("ROVER MANIFEST:")
        log.mars(f"Rover - {self._rover}")
        log.print_data(data=rover_information, log_level="mars")

        return rover_information