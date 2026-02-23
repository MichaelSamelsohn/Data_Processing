"""
Script Name - nil.py

Purpose - Query and download images from the NASA Image and Video Library (NIL).
For full API documentation - https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf

Created by Michael Samelsohn, 09/05/22.
"""

# Imports #
from datetime import datetime
from NASA_API.Settings.api_settings import (
    log, NIL_URL_PREFIX, NIL_MEDIA_TYPES, NIL_FIRST_YEAR, DEFAULT_IMAGE_DIRECTORY
)
from NASA_API.Source.api_utilities import get_request, download_image_url


class NIL:
    def __init__(self, image_directory=DEFAULT_IMAGE_DIRECTORY):
        log.nil("Initializing the NIL class")

        self.image_directory = image_directory
        self._media_type = None
        self._query = None
        self._search_years = None
        self._nil_image = None

    @staticmethod
    def validate_year_range(year_range) -> bool:
        """
        Validate a year range for NIL search queries.

        The year range must be:
        - A tuple or list with exactly two integer elements [start_year, end_year].
        - start_year ≥ NIL_FIRST_YEAR (1960).
        - start_year ≤ end_year ≤ current year.

        :param year_range: A tuple or list of the form [start_year, end_year].

        :return: True if the year range is valid, False otherwise.
        """

        log.debug(f"Validating NIL year range - {year_range}")

        # Step (1) - Verify the input is a tuple or list.
        if not isinstance(year_range, (tuple, list)):
            log.error("Year range must be a tuple or list")
            return False

        # Step (2) - Verify exactly two elements are provided.
        if len(year_range) != 2:
            log.error(f"Year range must contain exactly 2 elements, got {len(year_range)}")
            return False

        start_year, end_year = year_range

        # Step (3) - Verify both elements are integers.
        if not (isinstance(start_year, int) and isinstance(end_year, int)):
            log.error("Both year range elements must be integers")
            return False

        # Step (4) - Verify the range is within the valid bounds.
        current_year = datetime.now().year
        if not (NIL_FIRST_YEAR <= start_year <= end_year <= current_year):
            log.error(
                f"Year range must satisfy {NIL_FIRST_YEAR} ≤ start ≤ end ≤ {current_year} "
                f"(got start={start_year}, end={end_year})"
            )
            return False

        return True

    @property
    def search_years(self):
        """Get the configured search year range."""
        return self._search_years

    @search_years.setter
    def search_years(self, year_range):
        """
        Set the search year range after validation.

        :param year_range: A tuple or list of the form [start_year, end_year].
        """

        log.nil(f"Validating year range - {year_range}")
        if self.validate_year_range(year_range=year_range):
            log.success("Year range validated successfully")
            self._search_years = year_range
        else:
            log.error("Year range validation failed - year range was not set")

    @property
    def query(self):
        """Get the configured search query string."""
        return self._query

    @query.setter
    def query(self, new_query: str):
        """
        Set the search query string. Spaces are automatically URL-encoded.

        :param new_query: The search query (e.g., 'Crab nebula').
        """

        log.nil(f"Setting search query - '{new_query}'")
        self._query = new_query.replace(' ', '%20')

    @property
    def media_type(self):
        """Get the configured media type filter."""
        return self._media_type

    @media_type.setter
    def media_type(self, new_media_type: str):
        """
        Set the media type filter. Must be one of the supported types.

        :param new_media_type: Media type ('image' or 'audio').
        """

        log.nil(f"Setting media type - '{new_media_type}'")
        if new_media_type not in NIL_MEDIA_TYPES:
            log.error(f"Unsupported media type '{new_media_type}' - valid options: {NIL_MEDIA_TYPES}")
        else:
            log.success(f"Media type set to '{new_media_type}'")
            self._media_type = new_media_type

    @property
    def nil_image(self):
        """Get the path of the most recently downloaded NIL image."""
        return self._nil_image

    def nasa_image_library_query(self) -> bool:
        """
        Query the NASA Image and Video Library and download the first matching result.

        Notes:
        - Images are saved in JPEG format.
        - Both a search query and a media type must be set before calling this method.
        - The search year range is optional; omitting it searches the entire NIL archive.

        :return: True if a matching image was found and downloaded successfully, False otherwise.
        """

        log.nil("Querying the NASA Image and Video Library")

        # Step (1) - Verify required parameters are configured.
        if self._query is None:
            log.error("No search query set - use the 'query' property before calling this method")
            return False

        if self._media_type is None:
            log.error("No media type set - use the 'media_type' property before calling this method")
            return False

        # Step (2) - Build the request URL (year range is optional).
        url = f"{NIL_URL_PREFIX}q={self._query}&media_type={self._media_type}"
        if self._search_years is not None:
            url += f"&year_start={self._search_years[0]}&year_end={self._search_years[1]}"
            log.nil(f"Filtering results to years {self._search_years[0]}–{self._search_years[1]}")

        # Step (3) - Perform the API request.
        json_object = get_request(url=url)
        if json_object is None:
            log.error("API request failed - check logs for details")
            return False

        # Step (4) - Verify results were returned.
        items = json_object.get("collection", {}).get("items", [])
        if not items:
            log.warning("No results found - try extending the year range or changing the search query")
            return False

        log.nil(f"Found {len(items)} result(s) - downloading the first match")
        image_url = items[0]["links"][0]["href"]

        # Step (5) - Download and save the image.
        readable_query = self._query.replace('%20', '_')
        self._nil_image = download_image_url(
            image_directory=self.image_directory,
            api_type="NIL",
            image_url_list=[image_url],
            image_suffix=f"_{readable_query}"
        )

        return self._nil_image is not None