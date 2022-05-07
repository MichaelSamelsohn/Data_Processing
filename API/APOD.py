"""
Script Name - APOD.py

Purpose - Download the APOD (Astronomy Picture Of the Day) image.
For full API documentation - https://api.nasa.gov/.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import subprocess
import os

from NASA_API import NASA_API, get_request
from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


class APOD(NASA_API):
    def __init__(self, image_directory, date=Settings.DEFAULT_DATE, hd=Settings.DEFAULT_HD):
        """
        :param image_directory: The directory where the image is to be saved at.
        :param date: Date of the image. Acceptable format is - "YYYY-MM-DD".
        :param hd: Boolean indicating the quality of the image.
        """

        super().__init__(image_directory)

        self.__date = date
        self.__check_date_format()

        self.__hd = hd
        self.__check_hd_value()

    def __check_date_format(self):
        """
        Check for date format correctness. Acceptable format is - "YYYY-MM-DD".
        """

        log.debug(f"Selected date is - {self.__date}")
        split_date = self.__date.split("-")

        if len(split_date) != 3:
            log.error("Date is not a three part string separated by a '-'")
            self.__date = Settings.DEFAULT_DATE
            log.warning("Date has been changed to default one")
            return
        if len(split_date[0]) != 4 or len(split_date[1]) != 2 or len(split_date[2]) != 2:
            log.error("Year does not consist of 4 digits, or, month and day does not consist of 2 digits each")
            self.__date = Settings.DEFAULT_DATE
            log.warning("Date has been changed to default one")
            return

    @property
    def date(self):
        """
        Get the image date.
        :return: The image date.
        """
        return self.__date

    @date.setter
    def date(self, new_date):
        """
        Set the image date.
        :param new_date: The new image date.
        """
        self.__date = new_date
        self.__check_date_format()

    def __check_hd_value(self):
        """
        Check that hd value is of a boolean instance.
        If not, default to 'False'.
        """

        log.debug(f"HD version of the image - {self.__hd}")
        if not isinstance(self.__hd, bool):
            log.error("hd must be a boolean value, defaulting to 'False'")
            self.__hd = Settings.DEFAULT_HD

    @property
    def hd(self):
        """
        Get the image HD status.
        :return: The HD status of the image
        """
        return self.__date

    @hd.setter
    def hd(self, new_hd):
        """
        Set the image HD status.
        :param new_hd: The new HD status of the image.
        """
        self.__date = new_hd
        self.__check_hd_value()

    def log_class_parameters(self):
        super().log_class_parameters()
        log.debug(f"The selected image date is - {self.__date}")
        log.debug(f"The selected image HD status is - {self.__hd}")

    def astronomy_picture_of_the_day(self):
        """
        Save APOD image in the selected directory.
        Note - The images are saved as .JPG files.
        """

        log.debug("Retrieving APOD (Astronomy Picture Of the Day) image")

        # Construct the URL suffix.
        url_suffix = f"date={self.__date}&{Settings.API_KEY}"

        # Perform the API request.
        json_object = get_request(url=f"{Settings.APOD_URL_PREFIX}{url_suffix}")
        if json_object is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return

        # Log the image information.
        log.debug("IMAGE INFORMATION:")
        log.print_data(data=json_object)

        # The image URL is retrieved based on the HD parameter (two different URLs).
        image_url = json_object["hdurl"] if self.__hd else json_object["url"]

        # Download and save the image to the relevant directory.
        log.debug(f"Image URL is - {image_url}")
        output = subprocess.run(f"wget -O APOD_{self.__date}.JPG {image_url}",
                                shell=True, check=True, capture_output=True)
        log.print_data(data=output.stderr.decode("utf-8").split("\n"))
        log.info("Image downloaded successfully")


if __name__ == "__main__":
    obj = APOD(image_directory="", date="", hd=5)
    obj.log_class_parameters()
    obj.astronomy_picture_of_the_day()
