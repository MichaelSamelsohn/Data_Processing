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
    def __init__(self, image_directory=DEFAULT_IMAGE_DIRECTORY, media_type: str = None, query: str = None,
                 search_years: list = None):
        log.nil("Initializing the NIL class")

        self.image_directory = image_directory
        self.media_type = media_type
        try:
            self.query = query.replace(' ', '%20')
        except AttributeError:
            self.query = None
        self.search_years = search_years
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
        if self.query is None:
            log.error("No search query set - use the 'query' property before calling this method")
            return False

        if self.media_type not in NIL_MEDIA_TYPES:
            log.error(f"Unsupported media type '{self.media_type}' - valid options: {NIL_MEDIA_TYPES}")
            return False

        if not self.validate_year_range(year_range=self.search_years):
            log.error(f"Unsupported search years '{self.search_years}'")
            return False

        # Step (2) - Build the request URL (year range is optional).
        url = f"{NIL_URL_PREFIX}q={self.query}&media_type={self.media_type}"
        if self.search_years is not None:
            url += f"&year_start={self.search_years[0]}&year_end={self.search_years[1]}"
            log.nil(f"Filtering results to years {self.search_years[0]}–{self.search_years[1]}")

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
        readable_query = self.query.replace('%20', '_')
        self._nil_image = download_image_url(
            image_directory=self.image_directory,
            api_type="NIL",
            image_url_list=[image_url],
            image_suffix=f"_{readable_query}"
        )

        return self._nil_image is not None