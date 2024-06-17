"""
Script Name - apod.py

Purpose - Download the APOD (Astronomy Picture Of the Day) image.
For full API documentation - https://api.nasa.gov/.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import re
from API.nasa import NasaApi
from Settings import api_settings
from Utilities.decorators import check_connection
from Settings.settings import log


class APOD(NasaApi):
    def __init__(self, image_directory: str, date=api_settings.APOD_DEFAULT_DATE, hd=api_settings.APOD_DEFAULT_HD):
        """
        Subclass for downloading APOD (Astronomy Picture Of the Day) images.

        :param image_directory: The directory where the image is to be saved at.
        :param date: Date of the image. Acceptable format is - "YYYY-MM-DD".
        :param hd: Boolean indicating the quality of the image.
        """

        super().__init__(image_directory)

        self._date = self.__check_date_format(date=date)
        self._hd = hd
        self.__check_hd_value()

    @staticmethod
    def __check_date_format(date: str) -> str:
        """
        Check for date format correctness. Acceptable format is - "YYYY-MM-DD". The following regular expression is used
        for the check - Year between [1900-2099], no leap year check, month 02 is limited to 29 days.
        """

        log.debug(f"Selected date is - {date}")
        # For an explanation of the regex, see the docstring of this function.
        if re.search(
                pattern=r"^((19\d{2})|(20\d{2}))-(((02)-(0[1-9]|[1-2][0-9]))|(((0(1|[3-9]))|(1[0-2]))-(0[1-9]|[1-2][0-9"
                        r"]|30))|((01|03|05|07|08|10|12)-(31)))$",
                string=date):
            return date
        else:
            log.warning("Selected date doesn't match the expected pattern - YYYY-MM-DD")
            return api_settings.APOD_DEFAULT_DATE

    @property
    def date(self):
        """
        Get the image date.
        :return: The image date.
        """
        return self._date

    @date.setter
    def date(self, new_date: str):
        """
        Set the image date.
        :param new_date: The new image date.
        """
        self._date = self.__check_date_format(new_date)

    def __check_hd_value(self):
        """
        Check that hd value is of a boolean instance.
        If not, set to default.
        """

        log.debug(f"HD version of the image - {self._hd}")
        # if type(self._hd) != bool:
        if not isinstance(self._hd, bool):
            log.error("hd must be a boolean value, will reset to default value")
            self._hd = api_settings.APOD_DEFAULT_HD
            return False

        log.info("HD status is acceptable")
        return True

    @property
    def hd(self):
        """
        Get the image HD status.
        :return: The HD status of the image
        """
        return self._hd

    @hd.setter
    def hd(self, new_hd: bool):
        """
        Set the image HD status.
        :param new_hd: The new HD status of the image.
        """
        self._hd = new_hd
        self.__check_hd_value()

    def _debug(self):
        super()._debug()
        log.debug(f"The selected image date is - {self._date}")
        log.debug(f"The selected image HD status is - {self._hd}")

    @check_connection
    def astronomy_picture_of_the_day(self):
        """
        Save APOD image in the selected directory.
        Note - The images are saved as .JPG files.
        """

        log.debug("Retrieving APOD (Astronomy Picture Of the Day) image")

        # Perform the API request.
        json_object = self.get_request(url=f"{api_settings.APOD_URL_PREFIX}date={self._date}&{api_settings.API_KEY}")
        if json_object is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return False

        # Log the image information.
        log.debug("IMAGE INFORMATION:")
        log.print_data(data=json_object)

        # Download and save the image to the relevant directory.
        self.download_image_url(api_type="APOD",
                                image_url_list=[json_object["hdurl"] if self._hd else json_object["url"]],
                                image_suffix=f"_{self._date}")
