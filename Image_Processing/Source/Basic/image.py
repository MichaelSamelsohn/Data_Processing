"""
Script Name - image.py

Purpose - Class for image representation.

Created by Michael Samelsohn, 12/05/22.
"""

# Imports #
import traceback
import matplotlib.image as im
import matplotlib.pyplot as plt
from scipy.io import loadmat

from common import *
from Image_Processing.Source.Advanced.intensity_transformations import *
from Image_Processing.Source.Advanced.spatial_filtering import *
from Image_Processing.Source.Advanced.segmentation import *
from Image_Processing.Source.Advanced.restoration import *
from Image_Processing.Source.Advanced.noise_models import *
from Image_Processing.Source.Advanced.thinning import *
from Image_Processing.Source.Advanced.morphology import *


class Image:
    def __init__(self, image_path=DEFAULT_IMAGE_LENA, display_time=None):
        log.info(f"Initiating image class (image path - {image_path})")

        self.display_time = display_time

        log.debug("Checking that image path exists")
        log.error(f"Image, {image_path}, doesn't exist, will use Lena image") \
            if not os.path.exists(path=image_path) \
            else log.success(f"Image, {image_path}, exists")

        log.debug("Loading the image (in accordance to its format)")
        try:
            if '.mat' in image_path:
                log.debug("MATLAB (.mat) file identified")
                self._original_image = loadmat(image_path)
                log.debug("Searching for ndarray class object")
                for key in self._original_image:
                    if isinstance(self._original_image[key], ndarray):
                        self._original_image = self._original_image[key]
                        break  # Image found, no need to continue.
            else:
                log.debug("Normal image format identified")
                self._original_image = im.imread(fname=image_path)
            log.success("Custom image loaded successfully")
        except Exception:  # TODO: Identify potential error types.
            log.error("Failed to load image")
            log.print_data(data=traceback.format_exc(), log_level='error')

        log.debug("Deep copying original image")
        self._image_buffer = [{"Name": "Original", "Image": self._original_image}]
        self._last_image = copy.deepcopy(self._original_image)

    # Basic operations #

    def reset_to_original_image(self):
        """
        Reset the edited image to the original one.
        """

        log.info("Resetting the last image to original one")
        self._last_image = copy.deepcopy(self._original_image)

    # Image(s) display #

    def display_original_image(self):
        """
        Display the original image.
        """

        log.debug("Displaying the original image")
        plt.imshow(self._original_image)
        plt.title("Original image")
        # TODO: Add option to have grid lines.
        self.plt_show()

    def display_last_image(self):
        """
        Display the edited image.
        """

        log.debug("Displaying the last image")
        plt.imshow(self._last_image, cmap='gray') if len(self._last_image.shape) == 2 else plt.imshow(self._last_image)
        plt.title("Last image")
        # TODO: Add option to have grid lines.
        self.plt_show()

    def compare_to_original(self):
        """
        Display the edited image in comparison with the original one.
        """

        log.debug("Displaying the original and last images side-by-side for comparison")
        plt.subplot(1, 2, 1)
        plt.title("Original")
        plt.imshow(self._original_image, cmap='gray') if len(self._last_image.shape) == 2 \
            else plt.imshow(self._original_image)

        plt.subplot(1, 2, 2)
        plt.title(self._image_buffer[-1]["Name"])
        plt.imshow(self._image_buffer[-1]["Image"], cmap='gray') if len(self._last_image.shape) == 2 \
            else plt.imshow(self._image_buffer[-1]["Image"])

        # TODO: Add option to have grid lines.
        self.plt_show()

    def display_histogram(self, normalize=DEFAULT_HISTOGRAM_NORMALIZATION):
        """
        Display image histogram. Histogram is a graph showing the pixel count per pixel value. It provides an insight of
        the dominant pixel values in the image.

        :param normalize: TODO: Complete.
        """

        # TODO: Handle color image histogram display.
        histogram = calculate_histogram(image=self._last_image, normalize=normalize)
        plt.title("Image Histogram")
        plt.xlabel("Pixel Intensity")
        plt.ylabel("Pixel Count")
        plt.bar(range(256), histogram)
        # TODO: Add option to have grid lines.
        self.plt_show()

    def display_all_images(self):
        """
        Show all accumulated images in the buffer. The first image is always the original one.
        """

        log.info("Displaying all available images in the buffer")

        # Understand how many plots there are and rows/cols accordingly.
        number_of_images = len(self._image_buffer)
        log.debug(f"Number of images found in buffer - {number_of_images}")

        # Displaying original image.
        plt.subplot(1, number_of_images, 1)
        plt.title("Original")
        plt.imshow(self._original_image)

        # Displaying the rest of the images found in the buffer.
        for i in range(1, number_of_images):
            current_image = self._image_buffer[i]
            plt.subplot(1, number_of_images, i + 1)
            plt.imshow(current_image["Image"], cmap='gray') if len(current_image["Image"].shape) == 2 \
                else plt.imshow(current_image["Image"])
            plt.title(current_image["Name"])

        # TODO: Add option to have grid lines.
        self.plt_show()

    def plt_show(self):
        """
        Display a matplotlib plot with optional timed display.

        If display_time is set (i.e., not None or 0), the plot will be shown in non-blocking mode for the specified
        number of seconds and then automatically closed. Otherwise, the plot will be shown in blocking mode, requiring
        the user to manually close it.

        Note - This method assumes that a matplotlib plot has already been created prior to calling it.
        """

        if self.display_time:
            plt.show(block=False)
            plt.pause(self.display_time)
            plt.close()
        else:
            plt.show()

    # Basic operations #

    def convert_to_grayscale(self):
        self._last_image = convert_to_grayscale(image=self._last_image)
        self._image_buffer.append({"Name": "Grayscale", "Image": self._last_image})

    # Intensity transformations #

    def negative(self):
        self._last_image = negative(image=self._last_image)
        self._image_buffer.append({"Name": "Negative", "Image": self._last_image})

    def gamma_correction(self, gamma=DEFAULT_GAMMA_VALUE):
        self._last_image = gamma_correction(image=self._last_image, gamma=gamma)
        self._image_buffer.append({"Name": f"Gamma correction (gamma={gamma})", "Image": self._last_image})

    def bit_plane_reconstruction(self, degree_of_reduction=DEFAULT_DEGREE_OF_REDUCTION):
        self._last_image = bit_plane_reconstruction(image=self._last_image, degree_of_reduction=degree_of_reduction)
        self._image_buffer.append({"Name": f"Bit plane reconstruction (degree={degree_of_reduction})",
                                   "Image": self._last_image})

    def bit_plane_slicing(self, bit_plane=DEFAULT_BIT_PLANE):
        self._last_image = bit_plane_slicing(image=self._last_image, bit_plane=bit_plane)
        self._image_buffer.append({"Name": f"Bit plane slicing (plane={bit_plane})", "Image": self._last_image})

    # Spatial filtering #

    def blur_image(self, filter_type=DEFAULT_FILTER_TYPE, filter_size=DEFAULT_FILTER_SIZE,
                   padding_type=DEFAULT_PADDING_TYPE, sigma=DEFAULT_SIGMA_VALUE,
                   normalization_method=DEFAULT_NORMALIZATION_METHOD):
        self._last_image = blur_image(image=self._last_image, filter_type=filter_type, filter_size=filter_size,
                                      padding_type=padding_type, sigma=sigma, normalization_method=normalization_method)
        self._image_buffer.append({"Name": "Blur", "Image": self._last_image})

    def laplacian_gradient(self, padding_type=DEFAULT_PADDING_TYPE,
                           include_diagonal_terms=DEFAULT_INCLUDE_DIAGONAL_TERMS,
                           normalization_method=DEFAULT_NORMALIZATION_METHOD):
        self._last_image = laplacian_gradient(image=self._last_image, padding_type=padding_type,
                                              include_diagonal_terms=include_diagonal_terms,
                                              normalization_method=normalization_method)
        self._image_buffer.append({"Name": "Laplacian gradient", "Image": self._last_image})

    def laplacian_image_sharpening(self, padding_type=DEFAULT_PADDING_TYPE,
                                   include_diagonal_terms=DEFAULT_INCLUDE_DIAGONAL_TERMS):
        self._last_image = laplacian_image_sharpening(image=self._last_image, padding_type=padding_type,
                                                      include_diagonal_terms=include_diagonal_terms)
        self._image_buffer.append({"Name": "Laplacian image sharpening", "Image": self._last_image})

    def high_boost_filter(self, filter_type=DEFAULT_FILTER_TYPE, filter_size=DEFAULT_FILTER_SIZE,
                          padding_type=DEFAULT_PADDING_TYPE, k=DEFAULT_K_VALUE):
        self._last_image = high_boost_filter(image=self._last_image, filter_type=filter_type, filter_size=filter_size,
                                             padding_type=padding_type, k=k)
        self._image_buffer.append({"Name": "High boost filter", "Image": self._last_image})

    def sobel_filter(self, padding_type=DEFAULT_PADDING_TYPE, normalization_method=DEFAULT_NORMALIZATION_METHOD):
        self._last_image = sobel_filter(image=self._last_image, padding_type=padding_type,
                                        normalization_method=normalization_method)
        self._image_buffer.append({"Name": "Sobel filter", "Image": self._last_image})

    # Segmentation #

    def isolated_point_detection(self, padding_type=DEFAULT_PADDING_TYPE,
                                 normalization_method=DEFAULT_NORMALIZATION_METHOD,
                                 include_diagonal_terms=DEFAULT_INCLUDE_DIAGONAL_TERMS,
                                 threshold_value=DEFAULT_THRESHOLD_VALUE):
        self._last_image = isolated_point_detection(image=self._last_image, padding_type=padding_type,
                                                    normalization_method=normalization_method,
                                                    include_diagonal_terms=include_diagonal_terms,
                                                    threshold_value=threshold_value)
        self._image_buffer.append({"Name": "Isolated point detection", "Image": self._last_image})

    def line_detection(self, padding_type=DEFAULT_PADDING_TYPE, normalization_method=DEFAULT_NORMALIZATION_METHOD,
                       threshold_value=DEFAULT_THRESHOLD_VALUE):
        self._last_image = line_detection(image=self._last_image, padding_type=padding_type,
                                          normalization_method=normalization_method, threshold_value=threshold_value)
        self._image_buffer.append({"Name": "Line detection", "Image": self._last_image})

    def kirsch_edge_detection(self, padding_type=DEFAULT_PADDING_TYPE,
                              normalization_method=DEFAULT_NORMALIZATION_METHOD,
                              compare_max_value=DEFAULT_COMPARE_MAX_VALUES):
        kirsch_images = kirsch_edge_detection(image=self._last_image, padding_type=padding_type,
                                              normalization_method=normalization_method,
                                              compare_max_value=compare_max_value)
        for image in kirsch_images:
            self._image_buffer.append({"Name": f"{image}", "Image": kirsch_images[image]})

    def marr_hildreth_edge_detection(self, filter_size=DEFAULT_FILTER_SIZE, padding_type=DEFAULT_PADDING_TYPE,
                                     sigma=DEFAULT_SIGMA_VALUE, include_diagonal_terms=DEFAULT_INCLUDE_DIAGONAL_TERMS,
                                     threshold=DEFAULT_THRESHOLD_VALUE):
        self._last_image = marr_hildreth_edge_detection(image=self._last_image, filter_size=filter_size,
                                                        padding_type=padding_type, sigma=sigma,
                                                        include_diagonal_terms=include_diagonal_terms,
                                                        threshold=threshold)
        self._image_buffer.append({"Name": "Marr Hildreth edge detection", "Image": self._last_image})

    def canny_edge_detection(self, filter_size=DEFAULT_FILTER_SIZE,
                             padding_type=DEFAULT_PADDING_TYPE, sigma=DEFAULT_SIGMA_VALUE,
                             high_threshold=DEFAULT_HIGH_THRESHOLD_CANNY,
                             low_threshold=DEFAULT_LOW_THRESHOLD_CANNY):
        self._last_image = canny_edge_detection(image=self._last_image, filter_size=filter_size,
                                                padding_type=padding_type, sigma=sigma,
                                                high_threshold=high_threshold, low_threshold=low_threshold)
        self._image_buffer.append({"Name": "Canny edge detection", "Image": self._last_image})

    def thresholding(self, threshold_value=DEFAULT_THRESHOLD_VALUE):
        self._last_image = thresholding(image=self._last_image, threshold_value=threshold_value)
        self._image_buffer.append({"Name": "Thresholding", "Image": self._last_image})

    def global_thresholding(self, initial_threshold=DEFAULT_THRESHOLD_VALUE, delta_t=DEFAULT_DELTA_T):
        self._last_image = global_thresholding(image=self._last_image, initial_threshold=initial_threshold,
                                               delta_t=delta_t)
        self._image_buffer.append({"Name": "Global thresholding", "Image": self._last_image})

    def otsu_global_thresholding(self):
        self._last_image = otsu_global_thresholding(image=self._last_image)
        self._image_buffer.append({"Name": "Otsu global thresholding", "Image": self._last_image})

    # Restoration #

    def mean_filter(self, filter_type=DEFAULT_MEAN_FILTER_TYPE, padding_type=DEFAULT_PADDING_TYPE,
                    filter_size=DEFAULT_FILTER_SIZE, **kwargs):
        self._last_image = mean_filter(image=self._last_image, filter_type=filter_type, padding_type=padding_type,
                                       filter_size=filter_size, **kwargs)
        self._image_buffer.append({"Name": f"Mean filter ({filter_type})", "Image": self._last_image})

    def order_statistic_filter(self, filter_type=DEFAULT_ORDER_STATISTIC_FILTER_TYPE,
                               padding_type=DEFAULT_PADDING_TYPE, filter_size=DEFAULT_FILTER_SIZE, **kwargs):
        self._last_image = order_statistic_filter(image=self._last_image, filter_type=filter_type,
                                                  padding_type=padding_type, filter_size=filter_size, **kwargs)
        self._image_buffer.append({"Name": f"Order statistic filter ({filter_type})", "Image": self._last_image})

    # Noise models #

    def add_gaussian_noise(self, mean=DEFAULT_GAUSSIAN_MEAN, sigma=DEFAULT_GAUSSIAN_SIGMA):
        self._last_image = add_gaussian_noise(image=self._last_image, mean=mean, sigma=sigma)
        self._image_buffer.append({"Name": "Gaussian noise", "Image": self._last_image})

    def add_rayleigh_noise(self, a=DEFAULT_RAYLEIGH_A, b=DEFAULT_RAYLEIGH_B):
        self._last_image = add_rayleigh_noise(image=self._last_image, a=a, b=b)
        self._image_buffer.append({"Name": "Rayleigh noise", "Image": self._last_image})

    def add_erlang_noise(self, a=DEFAULT_ERLANG_A, b=DEFAULT_ERLANG_A):
        self._last_image = add_erlang_noise(image=self._last_image, a=a, b=b)
        self._image_buffer.append({"Name": "Erlang noise", "Image": self._last_image})

    def add_exponential_noise(self, a=DEFAULT_EXPONENTIAL_DECAY):
        self._last_image = add_exponential_noise(image=self._last_image, a=a)
        self._image_buffer.append({"Name": "Exponential noise", "Image": self._last_image})

    def add_uniform_noise(self, a=DEFAULT_UNIFORM_A, b=DEFAULT_UNIFORM_B):
        self._last_image = add_uniform_noise(image=self._last_image, a=a, b=b)
        self._image_buffer.append({"Name": "Uniform noise", "Image": self._last_image})

    def add_salt_and_pepper(self, pepper=DEFAULT_PEPPER, salt=DEFAULT_SALT):
        self._last_image = add_salt_and_pepper(image=self._last_image, pepper=pepper, salt=salt)
        self._image_buffer.append({"Name": "Salt & Pepper noise", "Image": self._last_image})

    # Thinning #

    def parallel_sub_iteration_thinning(self, method=DEFAULT_THINNING_METHOD, is_pre_thinning=DEFAULT_PRE_THINNING):
        self._last_image = parallel_sub_iteration_thinning(image=self._last_image, method=method,
                                                           is_pre_thinning=is_pre_thinning)
        self._image_buffer.append({"Name": f"Parallel sub-iteration thinning ({method} method, "
                                           f"{'with' if is_pre_thinning else 'without'} pre-thinning)",
                                   "Image": self._last_image})

    def pta2t_thinning(self):
        self._last_image = pta2t_thinning(image=self._last_image)
        self._image_buffer.append({"Name": "PTA2T thinning algorithm", "Image": self._last_image})

    def measure_thinning_rate(self):
        return measure_thinning_rate(self._last_image)

    # Morphology #

    def erosion(self, structuring_element=DEFAULT_STRUCTURING_ELEMENT, padding_type=DEFAULT_PADDING_TYPE):
        self._last_image = erosion(image=self._last_image, structuring_element=structuring_element,
                                   padding_type=padding_type)
        self._image_buffer.append({"Name": "Erosion", "Image": self._last_image})

    def dilation(self, structuring_element=DEFAULT_STRUCTURING_ELEMENT, padding_type=DEFAULT_PADDING_TYPE):
        self._last_image = dilation(image=self._last_image, structuring_element=structuring_element,
                                    padding_type=padding_type)
        self._image_buffer.append({"Name": "Dilation", "Image": self._last_image})

    def opening(self, structuring_element=DEFAULT_STRUCTURING_ELEMENT, padding_type=DEFAULT_PADDING_TYPE):
        self._last_image = opening(image=self._last_image, structuring_element=structuring_element,
                                   padding_type=padding_type)
        self._image_buffer.append({"Name": "Opening", "Image": self._last_image})

    def closing(self, structuring_element=DEFAULT_STRUCTURING_ELEMENT, padding_type=DEFAULT_PADDING_TYPE):
        self._last_image = closing(image=self._last_image, structuring_element=structuring_element,
                                   padding_type=padding_type)
        self._image_buffer.append({"Name": "Closing", "Image": self._last_image})

    def boundary_extraction(self, structuring_element=DEFAULT_STRUCTURING_ELEMENT, padding_type=DEFAULT_PADDING_TYPE):
        self._last_image = boundary_extraction(image=self._last_image, structuring_element=structuring_element,
                                               padding_type=padding_type)
        self._image_buffer.append({"Name": "Boundary extraction", "Image": self._last_image})
