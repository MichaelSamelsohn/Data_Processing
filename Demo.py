"""
Script Name - Demo.py

Purpose - Demo showcasing of the project.

Created by Michael Samelsohn, 22/03/24
"""

# Imports #
import os

from APOD import APOD
from EPIC import EPIC
from Image import Image
from MARS import MARS
from NIL import NIL

# Demo constants #
IMAGE_DIRECTORY_PATH = "C:\\Users\\Michael\\PycharmProjects\\Data_Processing\\Images"


def nasa_api_demo():
    """
    NASA API demo, which includes the following:
        1) APOD (Astronomy Picture Of the Day) with an option to select the date (APOD_DATE).
        2) EPIC (Earth Polychromatic Imaging Camera).
        3) Mars rover images with an option to select the rover and date (MARS_ROVER and MARS_ROVER_DATE respectively).
        4) NIL (NASA Imaging Library) with an option to select the query (NIL_QUERY).
    """

    # APOD (Astronomy Picture Of the Day) demo.
    apod_date = input("Enter APOD date (acceptable format is - YYYY-MM-DD): ")
    apod = APOD(image_directory=IMAGE_DIRECTORY_PATH, date=apod_date)
    apod.astronomy_picture_of_the_day()
    image = Image(os.path.join(IMAGE_DIRECTORY_PATH, f"APOD_{apod_date}.JPG"))
    image.display_original_image()

    # EPIC (Earth Polychromatic Imaging Camera) demo.
    epic = EPIC(image_directory=IMAGE_DIRECTORY_PATH, number_of_images=1)
    epic.earth_polychromatic_imaging_camera()
    image = Image(os.path.join(IMAGE_DIRECTORY_PATH, "EPIC.png"))
    image.display_original_image()

    # Mars rovers images demo.
    mars_rover = input("Enter rover name (options are - Spirit/Curiosity/Opportunity): ")
    mars_date = input("Enter rover date (acceptable format is - YYYY-MM-DD): ")
    mars = MARS(image_directory=IMAGE_DIRECTORY_PATH, rover=mars_rover, date=mars_date,  number_of_images=1)
    mars.mars_rover_images()
    image = Image(os.path.join(IMAGE_DIRECTORY_PATH, "MARS.JPG"))
    image.display_image()

    # NIL (NASA Imaging Library) demo.
    nil_query = input("Enter query: ")
    nil = NIL(image_directory=IMAGE_DIRECTORY_PATH, query=nil_query)
    nil.nasa_image_library_query()
    image = Image(os.path.join(IMAGE_DIRECTORY_PATH, f"NIL_{nil_query.replace(' ', '_')}.JPG"))
    image.display_image()


if __name__ == '__main__':
    nasa_api_demo()
