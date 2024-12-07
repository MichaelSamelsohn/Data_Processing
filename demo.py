"""
Script Name - demo.py

Purpose - Demo showcasing of the project.

Created by Michael Samelsohn, 22/03/24
"""

# Imports #
import os
from apod import APOD
from epic import EPIC
from Basic.image import Image
from mars_rovers import MARS
from nil import NIL
from spatial_filtering import *

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
    lena = Image(image_path="C:\\Users\\micha\\PycharmProjects\\Data_Processing\\Images\\Lena.png")
    lena.transform_image(transformation_type="convert_to_grayscale", image=lena.image)

    # Intensity transformations:
    # Negative.
    # lena.transform_image(transformation_type="negative", image=lena.image)
    # Gamma correction.
    # lena.transform_image(transformation_type="gamma_correction", image=lena.image, gamma=0.5)
    # lena.transform_image(transformation_type="gamma_correction", image=lena.image, gamma=2)
    # Bit-plane reconstruction.
    # lena.transform_image(transformation_type="bit_plane_reconstruction", image=lena.image, degree_of_reduction=2)
    # lena.transform_image(transformation_type="bit_plane_reconstruction", image=lena.image, degree_of_reduction=5)
    # lena.transform_image(transformation_type="bit_plane_reconstruction", image=lena.image, degree_of_reduction=7)
    # Bit-plane slicing.
    # lena.transform_image(transformation_type="bit_plane_slicing", image=lena.image, bit_plane=2)
    # lena.transform_image(transformation_type="bit_plane_slicing", image=lena.image, bit_plane=5)
    # lena.transform_image(transformation_type="bit_plane_slicing", image=lena.image, bit_plane=7)

    # Spatial filtering:
    # Blur image.
    # lena.transform_image(transformation_type="blur_image", image=lena.image, filter_type='box', filter_size=3)
    # lena.transform_image(transformation_type="blur_image", image=lena.image, filter_type='box', filter_size=13)
    # lena.transform_image(transformation_type="blur_image", image=lena.image, filter_type='gaussian', filter_size=3)
    # lena.transform_image(transformation_type="blur_image", image=lena.image, filter_type='gaussian', filter_size=23, sigma=4)
    # Laplacian gradient.
    # lena.transform_image(transformation_type="laplacian_gradient", image=lena.image, include_diagonal_terms=True, normalization_method='unchanged')
    # lena.transform_image(transformation_type="laplacian_gradient", image=lena.image, include_diagonal_terms=False, normalization_method='unchanged')
    # lena.transform_image(transformation_type="laplacian_gradient", image=lena.image, include_diagonal_terms=True, normalization_method='stretch')
    # lena.transform_image(transformation_type="laplacian_gradient", image=lena.image, include_diagonal_terms=False, normalization_method='stretch')
    # lena.transform_image(transformation_type="laplacian_gradient", image=lena.image, include_diagonal_terms=True, normalization_method='cutoff')
    # lena.transform_image(transformation_type="laplacian_gradient", image=lena.image, include_diagonal_terms=False, normalization_method='cutoff')
    # Laplacian image sharpening.
    # lena.transform_image(transformation_type="laplacian_image_sharpening", image=lena.image, include_diagonal_terms=True)
    # lena.transform_image(transformation_type="laplacian_image_sharpening", image=lena.image, include_diagonal_terms=False)
    # High boost filter.
    # lena.transform_image(transformation_type="high_boost_filter", image=lena.image, filter_type='box', filter_size=3, k=1)
    # lena.transform_image(transformation_type="high_boost_filter", image=lena.image, filter_type='box', filter_size=13, k=1)
    # lena.transform_image(transformation_type="high_boost_filter", image=lena.image, filter_type='box', filter_size=13, k=3)
    # lena.transform_image(transformation_type="high_boost_filter", image=lena.image, filter_type='box', filter_size=13, k=0.3)
    # Sobel filter.
    # lena.transform_image(transformation_type="sobel_filter", image=lena.image, normalization_method='unchanged')
    # lena.transform_image(transformation_type="sobel_filter", image=lena.image, normalization_method='stretch')
    # lena.transform_image(transformation_type="sobel_filter", image=lena.image, normalization_method='cutoff')

    # Segmentation:
    # Isolated point detection.
    # lena.transform_image(transformation_type="isolated_point_detection", image=lena.image, include_diagonal_terms=False, threshold_value=0.5, normalization_method='unchanged')
    # lena.transform_image(transformation_type="isolated_point_detection", image=lena.image, include_diagonal_terms=False, threshold_value=0.8, normalization_method='unchanged')
    # lena.transform_image(transformation_type="isolated_point_detection", image=lena.image, include_diagonal_terms=False, threshold_value=0.2, normalization_method='unchanged')
    # lena.transform_image(transformation_type="isolated_point_detection", image=lena.image, include_diagonal_terms=True, threshold_value=0.5, normalization_method='unchanged')
    # lena.transform_image(transformation_type="isolated_point_detection", image=lena.image, include_diagonal_terms=False, threshold_value=0.2, normalization_method='cutoff')
    # lena.transform_image(transformation_type="isolated_point_detection", image=lena.image, include_diagonal_terms=False, threshold_value=0.8, normalization_method='stretch')
    # Line detection.
    # lena.transform_image(transformation_type="line_detection", image=lena.image, threshold_value=0.5, normalization_method='unchanged')
    # lena.transform_image(transformation_type="line_detection", image=lena.image, threshold_value=0.2, normalization_method='unchanged')
    # lena.transform_image(transformation_type="line_detection", image=lena.image, threshold_value=0.8, normalization_method='unchanged')
    # lena.transform_image(transformation_type="line_detection", image=lena.image, threshold_value=0.5, normalization_method='stretch')
    # Kirsch edge detection.
    # lena.transform_image(transformation_type="kirsch_edge_detection", image=lena.image, compare_max_value=False, normalization_method='cutoff')
    # Marr-Hildreth edge detection.
    # lena.transform_image(transformation_type="marr_hildreth_edge_detection", image=lena.image, filter_size=3, sigma=1, include_diagonal_terms=False, threshold=0.1)
    # lena.transform_image(transformation_type="marr_hildreth_edge_detection", image=lena.image, filter_size=3, sigma=1, include_diagonal_terms=True, threshold=0.1)
    # lena.transform_image(transformation_type="marr_hildreth_edge_detection", image=lena.image, filter_size=13, sigma=1, include_diagonal_terms=False, threshold=0.1)
    # lena.transform_image(transformation_type="marr_hildreth_edge_detection", image=lena.image, filter_size=13, sigma=1, include_diagonal_terms=True, threshold=0.1)
    # lena.transform_image(transformation_type="marr_hildreth_edge_detection", image=lena.image, filter_size=13, sigma=2, include_diagonal_terms=True, threshold=0.1)
    # Thresholding.
    # lena.transform_image(transformation_type="thresholding", image=lena.image, threshold_value=0.5)
    # Global thresholding.
    # lena.transform_image(transformation_type="global_thresholding", image=lena.image, initial_threshold=0.1, delta_t=0.07)


    lena.display_all_images()


if __name__ == '__main__':
    # NASA API demo.
    nasa_api_demo()

    # Image processing demo.
    intensity_transformations_demo()


