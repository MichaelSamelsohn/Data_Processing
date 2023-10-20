"""
Script Name - CLI.py

Purpose - ??.

Created by Michael Samelsohn, 20/12/23
"""

# Imports #
import os
import argparse

from API.EPIC import EPIC
from API.MARS import MARS
from API.NIL import NIL
from API.APOD import APOD
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Command line interface to interact with the NASA API')

    parser.add_argument('-d', metavar='IMAGE_DIRECTORY', dest='image_directory',
                        help='The directory where the image(s) is stored.')
    parser.add_argument('-a', metavar='DATE', dest='apod',
                        help='Astronomy Picture Of the Day')
    parser.add_argument('-hd', dest='apod_hd', action='store_true',
                        help='Option to have the APOD image in HD')
    parser.add_argument('-e', metavar='NUMBER_OF_IMAGES', dest='epic', type=int,
                        help='Earth Polychromatic Imaging Camera')
    parser.add_argument('-m', metavar='NUMBER_OF_IMAGES', dest='mars', type=int,
                        help='MARS rover images')
    parser.add_argument('-n', metavar='QUERY', dest='nil',
                        help='NASA Image Library')

    arguments = parser.parse_args()
    log.debug(arguments)
    image_directory = arguments.image_directory

    if arguments.apod is not None:
        obj = APOD(image_directory=image_directory, date=arguments.apod, hd=arguments.apod_hd)
        obj.log_class_parameters()
        obj.astronomy_picture_of_the_day()

    if arguments.epic is not None:
        obj = EPIC(image_directory=image_directory, number_of_images=arguments.epic)
        obj.log_class_parameters()
        obj.earth_polychromatic_imaging_camera()

    if arguments.mars is not None:
        obj = MARS(image_directory=image_directory, number_of_images=arguments.mars)
        obj.log_class_parameters()
        obj.mars_rover_images()

    if arguments.nil is not None:
        obj = NIL(image_directory=image_directory, query=arguments.nil)
        obj.log_class_parameters()
        obj.nasa_image_library_query()

    log.debug("Program end")
