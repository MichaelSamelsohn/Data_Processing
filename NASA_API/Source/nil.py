"""
Script Name - nil.py

Purpose - Download images from NIL (NASA Images Library).
For full API documentation - https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf

Created by Michael Samelsohn, 09/05/22
"""

# Imports #
from NASA_API.Source.nasa import NasaApi
from NASA_API.Settings import api_settings
from Utilities.decorators import check_connection
from Settings.settings import log


class NIL(NasaApi):
    def __init__(self, image_directory: str, query: str, media_type=api_settings.NIL_DEFAULT_MEDIA_TYPE,
                 search_years=api_settings.NIL_DEFAULT_SEARCH_YEARS):
        """
        :param image_directory: The directory where the image is to be saved at.
        :param query: The rover to inspect for images.
        :param media_type: The type of media used for the search.
        :param search_years: Start and end years for the query search.
        """

        super().__init__(image_directory)

        self.__image_url_list = []

        self.query = query

        self._media_type = media_type
        self.__check_media_type_availability()

        self._search_years = search_years
        self.__check_search_years_correctness()

    def __check_media_type_availability(self):
        """
        Check that selected media type is available. If not, set to default value.
        """

        log.debug(f"Selected media type is - {self._media_type}")
        if self._media_type not in api_settings.NIL_MEDIA_TYPES:
            log.error(f"The selected media type, {self._media_type}, is not available, setting default value")
            self._media_type = api_settings.NIL_DEFAULT_MEDIA_TYPE
            return False

        log.info("Selected media type is available")
        return True

    @property
    def media_type(self):
        """
        Get the media type.
        :return: The media type.
        """
        return self._media_type

    @media_type.setter
    def media_type(self, new_media_type: str):
        """
        Set the rover name.
        :param new_media_type: The new rover name.
        """
        self._media_type = new_media_type
        self.__check_media_type_availability()

    def __check_search_years_correctness(self):
        """
        Check that query search years are of positive integer type and in correct order.
        If not, set to default value.
        TODO: Check if search years have non-integer values and handle such cases.
        """

        log.debug(f"Selected search years - {self._search_years[0]}-{self._search_years[1]}")
        if not isinstance(self._search_years, list):
            log.error("Search years is not of type list, will reset to default")
            self._search_years = api_settings.NIL_DEFAULT_SEARCH_YEARS
            return False
        if self._search_years[0] > self._search_years[1]:
            log.error("The search years are in reversed order, therefore, switching them")
            self._search_years[0], self._search_years[1] = self._search_years[1], self._search_years[0]
            return False

        log.info("Selected search years are in order")
        return True

    @property
    def search_years(self):
        """
        Get the query search years.
        :return: The query search years.
        """
        return self._search_years

    @search_years.setter
    def search_years(self, new_search_years: list):
        """
        Set the query search years.
        :param new_search_years: The new query search years.
        """
        self._search_years = new_search_years
        self.__check_search_years_correctness()

    def _debug(self):
        super()._debug()
        log.debug(f"The selected Mars rover is - {self.query}")
        log.debug(f"The selected media type is - {self._media_type}")
        log.debug(f"The selected search years are - {self._search_years[0]}-{self._search_years[1]}")

    @check_connection
    def nasa_image_library_query(self):
        """
        Save queried image in the selected directory.
        Note - The images are saved as .JPG files.
        """

        log.debug("Retrieving queried image form the NASA imaging library")

        # Perform the API request.
        json_object = self.get_request(
            url=f"{api_settings.NIL_URL_PREFIX}q={self.query.replace(' ', '%20')}&media_type={self._media_type}"
                f"&year_start={self._search_years[0]}&year_end={self._search_years[1]}")
        if json_object is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return False

        # Process the response information.
        if len(json_object["collection"]["items"]) != 0:
            self.__image_url_list = [json_object["collection"]["items"][0]["links"][0]["href"]]
        else:
            log.warning("No images found for the selected search query. "
                        "Try to extend the search years or change the query")
            return False

        # Download and save the image to the relevant directory.
        self.download_image_url(api_type="NIL", image_url_list=self.__image_url_list,
                                image_suffix=f"_{self.query.replace(' ', '_')}")
