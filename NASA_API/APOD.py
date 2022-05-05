"""
Script Name - APOD.py

Purpose - Download the APOD (Astronomy Picture Of the Day) image.
For full API documentation - https://api.nasa.gov/.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import subprocess
import requests
import os

from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


class APOD:
    def __init__(self, image_directory, date, hd=False):
        """
        :param image_directory: The directory where the image is to be saved at.
        :param date: Date of the image. Acceptable format is - "YYYY-MM-DD".
        :param hd: Boolean indicating the quality of the image.
        """

        self.__image_directory = image_directory
        self.__date = date
        self.__hd = hd

        self.__run_basic_diagnostics()

    def __run_basic_diagnostics(self):
        self.__check_directory_existence()
        self.__check_date_format()
        self.__check_hd_value()

    def __check_directory_existence(self):
        log.debug(f"The selected directory is - {self.__image_directory}")
        try:
            log.debug("Changing working directory to given one")
            os.chdir(self.__image_directory)
        except FileNotFoundError:
            log.error(f"The specified directory, {self.__image_directory}, doesn't exist")
            log.debug("Saving the image to the images directory")
            os.chdir(path=os.path.abspath("../Images"))

    def __check_date_format(self):
        log.debug(f"Selected date is - {self.__date}")
        split_date = self.__date.split("-")
        if len(split_date) != 3:
            log.critical("Date should be a three part string separated by '-'")
            exit(10)
        if len(split_date[0]) != 4 or len(split_date[1]) != 2 or len(split_date[2]) != 2:
            log.critical("Year should consist of 4 digits, month and day should consist of 2 digits each")
            exit(11)

    def __check_hd_value(self):
        log.debug(f"HD version of the image - {self.__hd}")
        if not isinstance(self.__hd, bool):
            log.error("hd must be a boolean value, defaulting to 'False'")
            self.__hd = False

    @property
    def image_directory(self):
        return self.__image_directory

    @property
    def date(self):
        return self.__date

    @property
    def hd(self):
        return self.__hd

    def astronomy_picture_of_the_day(self):
        """
        Save APOD image in the selected directory.
        Note - The images are saved as .JPG files.
        """

        log.debug("Retrieving APOD (Astronomy Picture Of the Day) image")

        url_suffix = f"date={self.__date}&{Settings.API_KEY}"
        full_url = Settings.APOD_URL_PREFIX + url_suffix
        log.debug(f"The API request is - {full_url}")
        request = requests.get(full_url)
        log.debug(f"Request status code is - {request.status_code}")
        if request.status_code == 400:
            log.error("Bad date or non-existing one given")
            exit(12)
        assert request.status_code == 200, f"Status code is - {request.status_code}"
        log.info("request is successful")

        json_object = request.json()
        log.debug("IMAGE INFORMATION:")
        log.print_data(data=json_object)

        image_url = json_object["hdurl"] if self.__hd else json_object["url"]

        log.debug(f"Image URL is - {image_url}")
        output = subprocess.run(f"wget -O APOD_{self.__date}.JPG {image_url}",
                                shell=True, check=True, capture_output=True)
        log.print_data(data=output.stderr.decode("utf-8").split("\n"))
        log.info("Image downloaded successfully")
