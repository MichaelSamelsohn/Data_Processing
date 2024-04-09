"""
Script Name - apod.py

Purpose - Download the APOD (Astronomy Picture Of the Day) image.
For full API documentation - https://api.nasa.gov/.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import os

from API.nasa import NasaApi
from Utilities import Settings
from Utilities.decorators import check_connection
from Utilities.logger import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


class APOD(NasaApi):
    def __init__(self, image_directory: str, date=Settings.APOD_DEFAULT_DATE, hd=Settings.APOD_DEFAULT_HD):
        """
        :param image_directory: The directory where the image is to be saved at.
        :param date: Date of the image. Acceptable format is - "YYYY-MM-DD".
        :param hd: Boolean indicating the quality of the image.
        """

        super().__init__(image_directory)

        self.__image_url_list = []

        self._date = date
        self.__check_date_format()

        self._hd = hd
        self.__check_hd_value()

    @property  # Read only.
    def image_url_list(self) -> list:
        """
        Get the image URL list.
        :return: List with all the image URLs.
        """
        return self.__image_url_list

    def __check_date_format(self):
        """
        Check for date format correctness. Acceptable format is - "YYYY-MM-DD".
        """

        log.debug(f"Selected date is - {self._date}")
        split_date = self._date.split("-")

        if len(split_date) != 3:
            log.error("Date is not a three part string separated by a '-'. Will reset to default")
            self._date = Settings.APOD_DEFAULT_DATE
            return False
        if len(split_date[0]) != 4 or len(split_date[1]) != 2 or len(split_date[2]) != 2:
            log.error("Year does not consist of 4 digits, or, month and day does not consist of 2 digits each. "
                      "Will reset to default")
            self._date = Settings.APOD_DEFAULT_DATE
            return False

        log.info("Selected date is of correct format")
        return True

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
        self._date = new_date
        self.__check_date_format()

    def __check_hd_value(self):
        """
        Check that hd value is of a boolean instance.
        If not, set to default.
        """

        log.debug(f"HD version of the image - {self._hd}")
        if type(self._hd) != bool:
            log.error("hd must be a boolean value, will reset to default value")
            self._hd = Settings.APOD_DEFAULT_HD
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

    def log_class_parameters(self):
        super().log_class_parameters()
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
        json_object = self.get_request(url=f"{Settings.APOD_URL_PREFIX}date={self._date}&{Settings.API_KEY}")
        if json_object is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return False

        # Log the image information.
        log.debug("IMAGE INFORMATION:")
        log.print_data(data=json_object)

        # Process the response information.
        self.__image_url_list = [json_object["hdurl"] if self._hd else json_object["url"]]

        # Download and save the image to the relevant directory.
        self.download_image_url(api_type="APOD", image_url_list=self.__image_url_list, image_suffix=f"_{self._date}")
