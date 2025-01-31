"""
Script Name - image.py

Purpose - Class for image representation.

Created by Michael Samelsohn, 12/05/22
"""

# Imports #
import traceback
import matplotlib.image as im
import matplotlib.pyplot as plt
from scipy.io import loadmat

from common import *
from spatial_filtering import *
from intensity_transformations import *
from noise_models import *
from segmentation import *
from restoration import *
from thinning import *
from morphology import *
from Settings import image_settings
from Settings.settings import log


class Image:
    """
    TODO: Add explanation how the class works.
    """

    def __init__(self, image_path=image_settings.DEFAULT_IMAGE_LENA):
        # TODO: Add support for grayscale images.

        self.__image_path = image_path
        log.debug(f"The selected directory is - {self.__image_path}")

        log.debug("Asserting that image path exists")
        log.error(f"Image, {self.__image_path}, doesn't exist, will use Lena image") \
            if not os.path.exists(path=self.__image_path) \
            else log.info(f"Image, {self.__image_path}, exists")

        log.debug("Loading the image (in accordance to its format)")
        try:
            if '.mat' in self.__image_path:
                log.debug("MATLAB file identified")
                self.__original_image = loadmat(self.__image_path)
                log.debug("Searching for ndarray class object")
                for key in self.__original_image:
                    if isinstance(self.__original_image[key], ndarray):
                        self.__original_image = self.__original_image[key]
                        break  # Image found, no need to continue.
            else:
                log.debug("Normal image format identified")
                self.__original_image = im.imread(fname=self.__image_path)
            log.info("Custom image loaded successfully")
        except Exception:  # TODO: Identify potential error types.
            log.error("Failed to load image")
            log.print_data(data=traceback.format_exc(), log_level='error')

        log.debug("Deep copying image (for later comparison)")
        self.__images = [{"Name": "Original", "Image": self.__original_image}]
        self.__image = copy.deepcopy(self.__original_image)

    # Properties #

    @property
    def image_path(self):
        """
        Get the image path.
        :return: The image path.
        """
        return self.__image_path

    @property
    def image(self):
        """
        Get the image pixel array.
        :return: The image pixel array.
        """
        return self.__image

    # Basic operations #

    def reset_to_original_image(self):
        """
        Reset the edited image to the original one.
        """

        log.warning("Resetting the edited image to original one")
        self.__image = copy.deepcopy(self.__original_image)

    def transform_image(self, transformation_type: str, *args, **kwargs):
        """
        Performing a transformation on the selected image.

        :param transformation_type: The name of the method to be used.
        :param args: Arguments (no assigned to a keyword).
        :param kwargs: Keyword arguments.
        """

        # Performing the selected transformation with given arguments.
        transformed_image = globals()[transformation_type](*args, **kwargs)

        log.debug("Matching the return type of the transformation")
        if isinstance(transformed_image, ndarray):
            log.debug("Single image returned")
            self.__images.append({"Name": transformation_type, "Image": transformed_image})
            self.__image = transformed_image
        else:
            log.debug("Image dictionary returned")
            for image in transformed_image:
                self.__images.append({"Name": f"{transformation_type} ({image})",
                                      "Image": transformed_image[image]})
                self.__image = transformed_image[image]

    # Image(s) display #

    def display_original_image(self):
        """
        Display the original image.
        """

        log.debug("Displaying the original image")
        plt.imshow(self.__original_image)
        # TODO: Add option to have grid lines.
        plt.show()

    def display_image(self):
        """
        Display the edited image.
        """

        log.debug("Displaying the edited image")
        plt.imshow(self.__image, cmap='gray') if len(self.__image.shape) == 2 else plt.imshow(self.__image)
        plt.title("Image")
        # TODO: Add option to have grid lines.
        plt.show()

    def compare_to_original(self):
        """
        Display the edited image in comparison with the original one.
        """

        log.debug("Displaying the original and edited images side-by-side for comparison")
        plt.subplot(1, 2, 1)
        plt.title("original")
        plt.imshow(self.__original_image)

        plt.subplot(1, 2, 2)
        plt.title(self.__images[-1]["Name"])
        plt.imshow(self.__images[-1]["Image"], cmap='gray') if len(self.__image.shape) == 2 \
            else plt.imshow(self.__images[-1]["Image"])

        # TODO: Add option to have grid lines.
        plt.show()

    def display_histogram(self, normalize=image_settings.DEFAULT_HISTOGRAM_NORMALIZATION):
        """
        Display image histogram. Histogram is a graph showing the pixel count per pixel value. It provides an insight of
        the dominant pixel values in the image.

        :param normalize: TODO: Complete.
        """

        # TODO: Handle color image histogram display.
        histogram = calculate_histogram(image=self.__image, normalize=normalize)
        plt.title("Image Histogram")
        plt.xlabel("Pixel Intensity")
        plt.ylabel("Pixel Count")
        plt.bar(range(256), histogram)
        # TODO: Add option to have grid lines.
        plt.show()

    def display_all_images(self):
        """
        Show all accumulated images in the buffer. The first image is always the original one.
        """

        log.info("Displaying all available images in the buffer")

        # Understand how many plots there are and rows/cols accordingly.
        number_of_images = len(self.__images)
        log.debug(f"Number of images found in buffer - {number_of_images}")

        # Displaying original image.
        plt.subplot(1, number_of_images, 1)
        plt.title("original")
        plt.imshow(self.__original_image)

        # Displaying the rest of the images found in the buffer.
        for i in range(1, number_of_images):
            current_image = self.__images[i]
            plt.subplot(1, number_of_images, i + 1)
            plt.imshow(current_image["Image"], cmap='gray') if len(current_image["Image"].shape) == 2 \
                else plt.imshow(current_image["Image"])
            plt.title(current_image["Name"])

        # TODO: Add option to have grid lines.
        plt.show()
