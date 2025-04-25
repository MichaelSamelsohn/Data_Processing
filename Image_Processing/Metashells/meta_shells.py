# Imports #
import cmath
import math

from tabulate import tabulate
from Image_Processing.Basic.image import Image
from Image_Processing.Metashells.spatial_comparison import generate_multifoil, plot, measure_hausdorff_distance, measure_average_distance
from Image_Processing.Metashells.spatial_conversion import extract_skeleton_parameters, \
    find_equal_distance_pixels, transform_to_spatial_space
from Image_Processing.Advanced.thinning import *
from Image_Processing.Advanced.segmentation import *
from Utilities.decorators import measure_runtime


class MetaShell:
    def __init__(self, shell_path: str, number_of_coefficients: int, scaling_factor: float,
                 processing_parameters=None, multifoil_parameters=None):
        self.shell = Image(image_path=shell_path)
        self.processing_parameters = processing_parameters
        self.multifoil_parameters = multifoil_parameters
        self.number_of_coefficients = number_of_coefficients
        self.scaling_factor = scaling_factor

        self.thinned_image = None
        self.x, self.y = None, None
        self.fourier_coefficients = None

    def doublet_processing(self):
        # Stretching the contrast of the image.
        stretched_image = contrast_stretching(image=self.shell.image)

        # Thresholding the image to extract the high intensity contour.
        high_intensity_contour = thresholding(image=stretched_image,
                                              threshold_value=self.processing_parameters['high_threshold'])

        # Thresholding the negative image to extract the low intensity contour.
        negative_image = negative(image=stretched_image)
        low_intensity_contour = thresholding(image=negative_image,
                                             threshold_value=self.processing_parameters['low_threshold'])

        # Blurring the image to join the two intensity contours.
        blurred = blur_image(image=low_intensity_contour + high_intensity_contour,
                             filter_size=self.processing_parameters['filter_size'])

        # Thresholding the blurred image to obtain a blob centered on the required line.
        blob = global_thresholding(image=blurred, initial_threshold=self.processing_parameters['global_threshold'])

        self.thinned_image = parallel_sub_iteration_thinning(
            image=blob, method=self.processing_parameters['thinning_method'],
            is_pre_thinning=self.processing_parameters['is_pre_thinning'])

    def spatial_conversion(self):
        """
        TODO: Complete the docstring.
        """

        skeleton_links, skeleton_link_distances = extract_skeleton_parameters(skeleton_image=self.thinned_image)

        pixel_coordinates = find_equal_distance_pixels(number_of_pixels=self.number_of_coefficients,
                                                       skeleton_links=skeleton_links,
                                                       skeleton_link_distances=skeleton_link_distances)

        # TODO: Generalize.
        self.x, self.y = transform_to_spatial_space(image_size=401, scaling_factor=self.scaling_factor,
                                                    pixel_coordinates=pixel_coordinates)

        # TODO: Explain why this step is necessary.
        self.x.append(self.x[0])
        self.y.append(self.y[0])

    def spatial_comparison(self):
        """
        TODO: Complete the docstring.
        """

        # Generating a multifoil used for the spatial evaluation/comparison.
        x2, y2 = generate_multifoil(a=self.multifoil_parameters['a'], b=self.multifoil_parameters['b'],
                                    lobes=self.multifoil_parameters['lobes'],
                                    number_of_points=self.number_of_coefficients)

        # Calculating similarity metrics.
        data = [
            ["Hausdorff", measure_hausdorff_distance(
                curve1=np.column_stack((x2, y2)), curve2=np.column_stack((self.x, self.y)))],
            ["Average", measure_average_distance(
                curve1=np.column_stack((x2, y2)), curve2=np.column_stack((self.x, self.y)))]
        ]
        log.print_data(data=tabulate(data, headers=["Metric", "Value"], tablefmt="pretty"), log_level="info")

        log.debug("Plotting the curves for visual comparison")
        plot(x1=self.x, y1=self.y, x2=x2, y2=y2)

    @measure_runtime
    def dft_2d(self):
        """
        TODO: Complete the docstring.
        """

        fourier_coefficients = []

        log.debug("Turning spatial coordinates into complex numbers")
        spatial_coordinates = np.column_stack((self.x, self.y))
        complex_coordinates = [x + 1j * y for x, y in spatial_coordinates]

        log.debug("Calculating the Fourier coefficients")
        normalization_factor = 1 / len(spatial_coordinates)  # Simplified, because it's used many times.
        for k in range(len(spatial_coordinates)):
            a = 0  # Resetting the coefficient calculation.
            for n in range(len(spatial_coordinates)):
                a += normalization_factor * complex_coordinates[n] * cmath.exp(
                    -1j * 2 * math.pi * n * k * normalization_factor)
            fourier_coefficients.append(a)

        return fourier_coefficients
