"""
Script Name - nil.py

Purpose - Download images from NIL (NASA Images Library).
For full API documentation - https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf

Created by Michael Samelsohn, 09/05/22.
"""

# Imports #
from NASA_API.Source.api_utilities import *
from datetime import datetime


class NIL:
    def __init__(self, image_directory=DEFAULT_IMAGE_DIRECTORY):
        log.nil("Initializing the NIL class")

        self.image_directory = image_directory
        self.media_type = None
        self._query = None
        self._search_years = None

        self._nil_image = None

    @staticmethod
    def validate_year_range(year_range):
        # Check if input is a tuple or list.
        if not isinstance(year_range, (tuple, list)):
            log.error("Not a tuple/list")
            return False

        # Check if it has exactly two elements.
        if len(year_range) != 2:
            log.error("More than two elements")
            return False

        start_year, end_year = year_range

        # Check if both elements are integers.
        if not (isinstance(start_year, int) and isinstance(end_year, int)):
            log.error("One or more element is not an integer")
            return False

        # Get the current year.
        current_year = datetime.now().year

        # Validate year range.
        if 1960 <= start_year <= end_year <= current_year:
            return True

        return False

    @property
    def search_years(self):
        """Get the image date."""
        return self._search_years

    @search_years.setter
    def search_years(self, year_range: str):
        """
        Set the image date, only if validated.
        """

        log.nil(f"Validating the date - {year_range}")
        if self.validate_year_range(year_range=year_range):
            log.success("Year range validated")
            self._search_years = year_range
        else:
            log.error("Date not valid")

    @property
    def query(self):
        """Get the image date."""
        return self._query

    @query.setter
    def query(self, new_query: str):
        self._query = new_query.replace(' ', '%20')

    @property
    def nil_image(self):
        return self._nil_image

    def nasa_image_library_query(self):
        """
        Save queried image in the selected directory.
        Note - The images are saved as .JPG files.
        """

        log.nil("Retrieving queried image form the NASA imaging library")

        # Perform the API request.
        json_object = get_request(
            url=f"{NIL_URL_PREFIX}q={self._query}&media_type={self.media_type}"
                f"&year_start={self._search_years[0]}&year_end={self._search_years[1]}")
        if json_object is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return False

        # Process the response information.
        if len(json_object["collection"]["items"]) != 0:
            image_url = json_object["collection"]["items"][0]["links"][0]["href"]
        else:
            log.warning("No images found for the selected search query. "
                        "Try to extend the search years or change the query")
            return False

        # Download and save the image to the relevant directory.
        self._nil_image = download_image_url(image_directory=self.image_directory, api_type="NIL",
                                             image_url_list=[image_url],
                                             image_suffix=f"_{self._query.replace('%20', '_')}")

        return True