"""
Script Name - Image.py

Purpose - Class for image representation.

Created by Michael Samelsohn, 12/05/22
"""

# Imports #
import matplotlib.image as im
import matplotlib.pyplot as plt

from Common import *
from Intensity_Transformations import *
from Segmentation import *
from Spatial_Filtering import *
from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


class Image:
    def __init__(self, image_path=Settings.DEFAULT_IMAGE_LENA):
        # TODO: Add support for initialization using image array.
        # TODO: Add support for grayscale images.

        self.__original_image = None

        self.__image_path = image_path
        self.__load_original_image()

        self.__image = im.imread(fname=self.__image_path)

    def __load_original_image(self):
        """
        Check if image path exists. If not, use default image (Lena).
        Once path is established, load the image.
        """

        log.debug(f"The selected directory is - {self.__image_path}")
        if os.path.exists(path=self.__image_path):
            log.info(f"Image, {self.__image_path}, exists")
            self.__original_image = im.imread(fname=self.__image_path)
            return True
        else:
            log.error(f"Image, {self.__image_path}, doesn't exist, will use Lena image")
            self.__image_path = Settings.DEFAULT_IMAGE_LENA
            self.__original_image = im.imread(fname=self.__image_path)
            return False

    @property
    def image_path(self):
        """
        Get the image path.
        :return: The image path.
        """
        return self.__image_path

    @image_path.setter
    def image_path(self, new_image_path):
        """
        Set the image path.
        :param new_image_path: The new image path.
        """
        self.__image_path = new_image_path
        self.__load_original_image()

    def reset_to_original_image(self):
        """
        Reset the edited image to the original one.
        """

        log.warning("Resetting the edited image to original one")
        self.__image = copy.deepcopy(self.__original_image)

    def display_original_image(self):
        """
        Display the original image.
        """

        log.debug("Displaying the original image")
        plt.imshow(self.__original_image)
        plt.show()

    def display_image(self):
        """
        Display the edited image.
        """

        log.debug("Displaying the edited image")
        if len(self.__image.shape) == 2:
            # Grayscale image.
            plt.imshow(self.__image, cmap='gray')
        else:
            # Color image.
            plt.imshow(self.__image)

        plt.title("Image")
        plt.show()

    def compare_to_original(self):
        """
        Display the edited image in comparison with the original one.
        """

        log.debug("Displaying the original and edited images side-by-side for comparison")
        figure, axs = plt.subplots(1, 2)
        axs[0].imshow(self.__original_image)
        if len(self.__image.shape) == 2:
            # Grayscale image.
            axs[1].imshow(self.__image, cmap='gray')
        else:
            # Color image.
            axs[1].imshow(self.__image)

        plt.title("Image Comparison")
        # TODO: Add titles for the different images.
        plt.show()

    def display_histogram(self, normalize=Settings.DEFAULT_HISTOGRAM_NORMALIZATION):
        # TODO: Handle color image histogram display.
        histogram = calculate_histogram(image=self.__image, normalize=normalize)
        plt.title("Image Histogram")
        plt.xlabel("Pixel Intensity")
        plt.ylabel("Pixel Count")
        plt.bar(range(256), histogram)
        plt.show()

    def test(self):
        self.__image = convert_to_grayscale(image=self.__image)


if __name__ == "__main__":
    obj = Image("/Users/michaelsamelsohn/PycharmProjects/Data_Processing/Images/Lena.png")
    obj.test()
    obj.display_histogram(normalize=True)
    # obj.compare_to_original()
