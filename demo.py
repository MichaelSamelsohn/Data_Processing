"""
Script Name - demo.py

Purpose - Demo showcasing of the project.

Created by Michael Samelsohn, 22/03/24
"""

# Imports #

from apod import APOD
from epic import EPIC
from image import Image
from mars_rovers import MARS
from nil import NIL
from intensity_transformations import *

# Demo constants #
IMAGE_DIRECTORY_PATH = "C:\\Users\\Michael\\PycharmProjects\\Data_Processing\\Images"
LENA_IMAGE_PATH = "C:\\Users\\Michael\\PycharmProjects\\Data_Processing\\Images\\Lena.png"


def nasa_api_demo():
    """
    NASA API demo, which includes the following:
        1) APOD (Astronomy Picture Of the Day) with an option to select the date (APOD_DATE).
        2) EPIC (Earth Polychromatic Imaging Camera).
        3) Mars rover images with an option to select the rover and date (MARS_ROVER and MARS_ROVER_DATE respectively).
        4) NIL (NASA Imaging Library) with an option to select the query (NIL_QUERY).
    """

    log.info("Demo showcasing the NASA API")

    # APOD (Astronomy Picture Of the Day) demo.
    apod_date = input("Enter APOD date (acceptable format is - YYYY-MM-DD): ")
    apod = APOD(image_directory=IMAGE_DIRECTORY_PATH, date=apod_date)
    apod.astronomy_picture_of_the_day()
    apod._debug()
    image = Image(image_path=os.path.join(IMAGE_DIRECTORY_PATH, f"APOD_{apod_date}.JPG"))
    image.display_original_image()

    # EPIC (Earth Polychromatic Imaging Camera) demo.
    epic = EPIC(image_directory=IMAGE_DIRECTORY_PATH, number_of_images=1)
    epic.earth_polychromatic_imaging_camera()
    epic._debug()
    image = Image(image_path=os.path.join(IMAGE_DIRECTORY_PATH, "EPIC.png"))
    image.display_original_image()

    # Mars rovers images demo.
    mars_rover = input("Enter rover name (options are - Spirit/Curiosity/Opportunity): ")
    mars_date = input("Enter rover date (acceptable format is - YYYY-MM-DD): ")
    mars = MARS(image_directory=IMAGE_DIRECTORY_PATH, rover=mars_rover, date=mars_date,  number_of_images=1)
    mars.mars_rover_images()
    mars._debug()
    image = Image(image_path=os.path.join(IMAGE_DIRECTORY_PATH, "MARS.JPG"))
    image.display_image()

    # NIL (NASA Imaging Library) demo.
    nil_query = input("Enter query: ")
    nil = NIL(image_directory=IMAGE_DIRECTORY_PATH, query=nil_query)
    nil.nasa_image_library_query()
    nil._debug()
    image = Image(image_path=os.path.join(IMAGE_DIRECTORY_PATH, f"NIL_{nil_query.replace(' ', '_')}.JPG"))
    image.display_image()


def intensity_transformations_demo():
    log.debug("Demo showcasing the image processing capabilities")

    # Conversion to greyscale and histogram display.
    lena = Image(image_path=LENA_IMAGE_PATH)
    lena.transform_image(transformation_type="convert_to_grayscale", image=lena.image)

    # Showcase different transforms.
    log.debug("Available transformation types are:")
    log.debug("Intensity transformations category - Changes made on a single pixel basis, as opposed to pixel "
              "neighbourhood based operations")
    log.debug("\tthresholding - Transforming the image to its binary version using the provided threshold")
    log.debug("\tnegative - Perform image negative")
    log.debug("\tgamma_correction - Perform Gamma correction on an image")
    log.debug("\tbit_plane_reconstruction - Bit plane reconstruction. The degree of reduction indicates how many bit "
              "planes we dismiss from the LSB")
    log.debug("\tbit_plane_slicing - Bit plane slicing, shows the contribution of each bit plane")
    log.debug("")

    log.debug("Spatial filtering category - Perform spatial (pixel neighbourhood based) filtering on an image")
    log.debug("\tblur_image - Apply a low pass filter (blur) on an image")
    log.debug("\tlaplacian_image_sharpening - Perform image sharpening using the laplacian operator")
    log.debug("\thigh_boost_filter - Use a high boost filter (un-sharp masking) to sharpen the image")
    log.debug("")

    log.debug("Segmentation - ??")
    log.debug("\tglobal_thresholding - Same as regular thresholding, only the threshold is calculated depending on the "
              "image and the seed")
    log.debug("\tlaplacian_gradient - Second derivative of the image")
    log.debug("\tisolated_point_detection - Detect and highlight isolated points in the image")
    log.debug("\tline_detection - Detect and highlight lines in the image")
    log.debug("\tkirsch_edge_detection - Edge detection and highlighting for all 8 compass directions")
    log.debug("")

    transformation_type = input("Transformation type - ")
    lena.transform_image(transformation_type=transformation_type, image=lena.image)
    lena.display_all_images()


if __name__ == '__main__':
    # NASA API demo.
    nasa_api_demo()

    # Image processing demo.
    intensity_transformations_demo()


