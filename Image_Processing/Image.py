"""
Script Name - Image.py

Purpose - Class for image representation.

Created by Michael Samelsohn, 12/05/22
"""

# Imports #
import matplotlib.image as im
import numpy as np
import os

from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


class Image:
    def __init__(self, image_path=Settings.DEFAULT_IMAGE_LENA):
        # TODO: Add support for initialization using image array.

        self.__image_path = image_path
        self.__check_image_existence()

        self.__original_image = im.imread(fname=self.__image_path)
        self.__image = im.imread(fname=self.__image_path)

    def __check_image_existence(self):
        """
        Change the path to the specified directory (relevant for later when the images are being saved).
        If specified path does not exist, default to 'Images' directory.
        """

        log.debug(f"The selected directory is - {self.__image_path}")
        if os.path.exists(path=self.__image_path):
            log.info(f"Image, {self.__image_path}, exists")
            return True
        else:
            log.error(f"Image, {self.__image_path}, doesn't exist, will use Lena image")
            self.__image_path = Settings.DEFAULT_IMAGE_LENA
            return False


if __name__ == "__main__":
    obj = Image("/Users/michaelsamelsohn/PycharmProjects/Data_Processing/Images/Lena.png")
