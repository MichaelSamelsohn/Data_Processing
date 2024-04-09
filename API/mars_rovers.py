"""
Script Name - epic.py

Purpose - Download the Mars rovers image(s).
For full API documentation - https://api.nasa.gov/

Created by Michael Samelsohn, 08/05/22
"""

# Imports #
import os

from API.nasa import NasaApi
from Utilities import Settings
from Utilities.decorators import check_connection
from Utilities.logger import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


class MARS(NasaApi):
    def __init__(self, image_directory: str, rover=Settings.MARS_DEFAULT_ROVER, date=Settings.MARS_DEFAULT_DATE,
                 number_of_images=Settings.MARS_DEFAULT_NUMBER_OF_PHOTOS_TO_COLLECT):
        """
        :param image_directory: The directory where the image is to be saved at.
        :param rover: The rover to inspect for images.
        :param date: Date of the image. Acceptable format is - "YYYY-MM-DD".
        """

        super().__init__(image_directory)

        self.__image_url_list = []

        self._rover = rover
        self.__check_rover_availability()

        self._date = date
        self.__check_date_format()

        self._number_of_images = number_of_images
        self.__check_number_of_images_value()

    def __check_rover_availability(self):
        """
        Check that selected rover is available. If not, set to default value.
        """

        log.debug(f"Selected rover is - {self._rover}")
        if self._rover not in Settings.MARS_ROVERS:
            log.error(f"The selected rover, {self._rover}, is not available, setting default value")
            self._rover = Settings.MARS_DEFAULT_ROVER
            return False

        log.info("Selected rover is available")
        return True

    @property
    def rover(self):
        """
        Get the rover name.
        :return: The rover name.
        """
        return self._rover

    @rover.setter
    def rover(self, new_rover: str):
        """
        Set the rover name.
        :param new_rover: The new rover name.
        """
        self._rover = new_rover
        self.__check_rover_availability()

    def __check_date_format(self):
        """
        Check for date format correctness.
        Acceptable string format is - "YYYY-MM-DD".
        Acceptable integer format is - >=1.
        """

        log.debug(f"Selected date is - {self._date}")

        if type(self._date) == str:
            log.debug("Selected date is a string")
            split_date = self._date.split("-")

            if len(split_date) != 3:
                log.error("Date is not a three part string separated by a '-'")
                self._date = Settings.APOD_DEFAULT_DATE
                log.warning("Date has been changed to default one")
                return False
            if len(split_date[0]) != 4 or len(split_date[1]) != 2 or len(split_date[2]) != 2:
                log.error("Year does not consist of 4 digits, or, month and day does not consist of 2 digits each")
                self._date = Settings.APOD_DEFAULT_DATE
                log.warning("Date has been changed to default one")
                return False
        elif type(self._date) == int:
            log.debug("Selected date is an integer")
            if self._date < 1:  # TODO: Find out if sol count starts with 0/1.
                log.error("Integer date is not positive, setting it to 1")
                self._date = 1
                return False

        log.info("Selected date is of correct type/format")
        return True

    @property
    def date(self):
        """
        Get the image date.
        :return: The image date.
        """
        return self._date

    @date.setter
    def date(self, new_date: str | int):
        """
        Set the image date.
        :param new_date: The new image date.
        """
        self._date = new_date
        self.__check_date_format()

    def __check_number_of_images_value(self):
        """
        Check that number of images value is of an integer instance.
        If not, set to default value.
        """

        log.debug(f"Number of images is - {self._number_of_images}")
        if type(self._number_of_images) != int:
            log.error("Number of images must be an int value, will reset to default")
            self._number_of_images = Settings.MARS_DEFAULT_NUMBER_OF_PHOTOS_TO_COLLECT
            return False
        if self._number_of_images < 1:
            log.error("Number of images must be a positive integer value, will reset to default")
            self._number_of_images = Settings.MARS_DEFAULT_NUMBER_OF_PHOTOS_TO_COLLECT
            return False

        log.info("Selected number of images is within acceptable range")
        return True

    @property
    def number_of_images(self):
        """
        Get the number of images.
        :return: The number of images.
        """
        return self._number_of_images

    @number_of_images.setter
    def number_of_images(self, new_number_of_images: int):
        """
        Set the number of images.
        :param new_number_of_images: The new number of images.
        """
        self._number_of_images = new_number_of_images
        self.__check_number_of_images_value()

    def log_class_parameters(self):
        super().log_class_parameters()
        log.debug(f"The selected Mars rover is - {self._rover}")
        log.debug(f"The selected image date is - {self._date}")

    @check_connection
    def mars_rover_images(self):
        """
        Save Mars rover image(s) in the selected directory.
        Note - The images are saved as .JPG files.
        """

        log.debug("Retrieving Mars rover images")

        # Perform the API request.
        if type(self._date) == str:
            json_object = self.get_request(
                url=f"{Settings.MARS_URL_PREFIX}rovers/{self._rover}/photos?earth_date={self._date}&{Settings.API_KEY}")
        else:  # Date is of type integer.
            json_object = self.get_request(
                url=f"{Settings.MARS_URL_PREFIX}rovers/{self._rover}/photos?sol={self._date}&{Settings.API_KEY}")
        if json_object is None:  # API request failed.
            self.__mars_rover_manifest()  # For debugging purposes.
            log.error("Check logs for more information on the failed API request")
            return False

        # Process the response information.
        self.__image_url_list = self.__process_response_information(response_information=json_object)

        # Download and save the image to the relevant directory.
        self.download_image_url(api_type="MARS", image_url_list=self.__image_url_list)

    def __process_response_information(self, response_information: dict):
        """
        Process the response information to extract the image URLs.

        :param response_information: The response (containing the relevant information) from the API request.
        :return: List of the image URLs.
        """

        if self._number_of_images > len(response_information["photos"]):
            log.warning(f"Selected number of images, {self._number_of_images}, "
                        f"is more than the actual amount - {len(response_information)}")
        image_url_list = []
        for i in range(0, min(self._number_of_images, len(response_information["photos"]))):
            log.debug("Current image number is - {}".format(i + 1))
            image_url_list.append(response_information["photos"][i]["img_src"])

        return image_url_list

    def __mars_rover_manifest(self):
        """
        Get the Mars rover manifest, mainly for debugging purposes.

        :return: Dictionary with the rover manifest.
        """

        # Perform the API request to get the rover manifest.
        rover_manifest = self.get_request(url=f"{Settings.MARS_URL_PREFIX}manifests/{self._rover}?{Settings.API_KEY}")
        if rover_manifest is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return False

        rover_information = {
            "landing_date": rover_manifest["photo_manifest"]["landing_date"],
            "max_date": rover_manifest["photo_manifest"]["max_date"],
            "max_sol": rover_manifest["photo_manifest"]["max_sol"],
            "status": rover_manifest["photo_manifest"]["status"],
            "total_photos": rover_manifest["photo_manifest"]["total_photos"]
        }
        # Log the rover information.
        log.debug("ROVER INFORMATION:")
        log.print_data(data=rover_information)

        return rover_information
