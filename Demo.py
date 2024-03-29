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
from Intensity_Transformations import *

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

    # APOD (Astronomy Picture Of the Day) demo.
    apod_date = input("Enter APOD date (acceptable format is - YYYY-MM-DD): ")
    apod = APOD(image_directory=IMAGE_DIRECTORY_PATH, date=apod_date)
    apod.astronomy_picture_of_the_day()
    apod.log_class_parameters()
    image = Image(image_path=os.path.join(IMAGE_DIRECTORY_PATH, f"APOD_{apod_date}.JPG"))
    image.display_original_image()

    # EPIC (Earth Polychromatic Imaging Camera) demo.
    epic = EPIC(image_directory=IMAGE_DIRECTORY_PATH, number_of_images=1)
    epic.earth_polychromatic_imaging_camera()
    epic.log_class_parameters()
    image = Image(image_path=os.path.join(IMAGE_DIRECTORY_PATH, "EPIC.png"))
    image.display_original_image()

    # Mars rovers images demo.
    mars_rover = input("Enter rover name (options are - Spirit/Curiosity/Opportunity): ")
    mars_date = input("Enter rover date (acceptable format is - YYYY-MM-DD): ")
    mars = MARS(image_directory=IMAGE_DIRECTORY_PATH, rover=mars_rover, date=mars_date,  number_of_images=1)
    mars.mars_rover_images()
    mars.log_class_parameters()
    image = Image(image_path=os.path.join(IMAGE_DIRECTORY_PATH, "MARS.JPG"))
    image.display_image()

    # NIL (NASA Imaging Library) demo.
    nil_query = input("Enter query: ")
    nil = NIL(image_directory=IMAGE_DIRECTORY_PATH, query=nil_query)
    nil.nasa_image_library_query()
    nil.log_class_parameters()
    image = Image(image_path=os.path.join(IMAGE_DIRECTORY_PATH, f"NIL_{nil_query.replace(' ', '_')}.JPG"))
    image.display_image()


def intensity_transformations_demo():
    # Conversion to greyscale and histogram display.
    lena = Image(image_path=LENA_IMAGE_PATH)
    lena.transform_image(transformation_type="convert_to_grayscale", image=lena.image)
    lena.compare_to_original()
    lena.display_histogram()

    # Showcase different transforms.
    log.info("Please specify the following rubric - <transformation_type> <additional parameters>")
    log.info("If no additional parameters are specified, default ones will be used")
    log.info("")

    log.info("Available transformation types are:")
    log.info("Intensity transformations category - Changes made on a single pixel basis, as opposed to pixel "
             "neighbourhood based operations")
    log.info("\tthresholding - Transforming the image to its binary version using the provided threshold")
    log.info("\tnegative - Perform image negative")
    log.info("\tgamma_correction - Perform Gamma correction on an image")
    log.info("\tbit_plane_reconstruction - Bit plane reconstruction. The degree of reduction indicates how many bit "
             "planes we dismiss from the LSB")
    log.info("\tbit_plane_slicing - Bit plane slicing, shows the contribution of each bit plane")
    log.info("")

    log.info("Spatial filtering category - Perform spatial (pixel neighbourhood based) filtering on an image")
    log.info("\tblur_image - Apply a low pass filter (blur) on an image")
    log.info("\tlaplacian_image_sharpening - Perform image sharpening using the laplacian operator")
    log.info("\thigh_boost_filter - Use a high boost filter (un-sharp masking) to sharpen the image")
    log.info("")

    log.info("Segmentation - ??")
    log.info("\tglobal_thresholding - ??")
    log.info("\tlaplacian_gradient - ??")
    log.info("\tisolated_point_detection - ??")
    log.info("\tline_detection - ??")
    log.info("\tkirsch_edge_detection - ??")
    log.info("")

    log.info("Morphological - Convolution with a custom structuring element")
    log.info("\tmorphological_erosion - ??")
    log.info("\tmorphological_dilation - ??")
    log.info("\tmorphological_opening - ??")
    log.info("\tmorphological_closing - ??")
    log.info("\tboundary_extraction - ??")
    log.info("\tmorphological_convolution - ??")
    log.info("\tmorphological_opening - ??")
    log.info("")

    transformation_type = input("Transformation type: ")
    log.info(f"Selected transformation type is - {transformation_type}")
    lena.transform_image(transformation_type=transformation_type, image=lena.image)
    lena.compare_to_original()


if __name__ == '__main__':
    # NASA API demo.
    nasa_api_demo()

    # Image processing demo.
    intensity_transformations_demo()
