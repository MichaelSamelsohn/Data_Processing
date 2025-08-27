# Imports #
import cmath
import math

from tabulate import tabulate
from Image_Processing.Source.Basic.image import Image
from Image_Processing.Source.Metashells.spatial_comparison import (generate_multifoil, plot, measure_hausdorff_distance,
                                                                   measure_average_distance)
from Image_Processing.Source.Metashells.spatial_conversion import extract_skeleton_parameters, \
    find_equal_distance_pixels, transform_to_spatial_space
from Image_Processing.Source.Advanced.thinning import *
from Image_Processing.Source.Advanced.segmentation import *
from Utilities.decorators import measure_runtime


class MetaShell:
    def __init__(self, shell_path: str,
                 number_of_coefficients: int, scaling_factor: float,
                 processing_parameters: dict, multifoil_parameters: dict,
                 debug_mode=True, display_time=None):
        self.debug_mode = debug_mode
        self.display_time = display_time
        self.shell = Image(image_path=shell_path, display_time=self.display_time)

        self.processing_parameters = processing_parameters
        self.multifoil_parameters = multifoil_parameters

        self.number_of_coefficients = number_of_coefficients
        self.scaling_factor = scaling_factor

        self.thinned_image = None
        self.x, self.y = None, None
        self.metrics = None

        self.fourier_coefficients = []

    def doublet_processing(self, filter_size: int, global_threshold: float, thinning_method: str):
        """
        Image processing for the raw meta-shell data. The purpose is to extract a thinned image of the contour that is
        the middle of the foreground object.

        Assumptions:
        1) The image has two pseudo-closed contour.
        2) The contour are close to each other.
        3) The contour are of opposite values to each other.
        4) Noise in the image is not too strong, relative to the contour values.

        Based on the assumptions above, the following algorithm is applied:
        Step I - Threshold the image with a high value and a low value to obtain the two contour (based on assumptions
        (1), (3) and (4)).
        Step II - Blur the image containing only the contour to merge them together (based on assumption (2)) and clean
        all the noise and artifacts (based on assumption (4)).
        Step III - Thin the image to get a skeleton of the contour between the original two (based on assumptions (1)
        and (2)).
        """

        # Stretching the contrast of the image (to be able to work with [0, 1] values).
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
                             filter_size=filter_size)

        # Thresholding the blurred image to obtain a blob centered on the required line.
        blob = global_thresholding(image=blurred, initial_threshold=global_threshold)

        # Thinning the image.
        self.thinned_image = parallel_sub_iteration_thinning(image=blob, method=thinning_method)

    def spatial_conversion(self):
        """
        Conversion of skeleton image links from image space to spatial space.

        The following algorithm is applied:
        1) Extraction of skeleton parameters.
        2) Finding equal distance pixels.
        3) transforming to spatial space.
        """

        # Extracting skeleton parameters.
        skeleton_links, skeleton_link_distances = extract_skeleton_parameters(skeleton_image=self.thinned_image)

        # Finding equal distance pixels.
        pixel_coordinates = find_equal_distance_pixels(number_of_pixels=self.number_of_coefficients,
                                                       skeleton_links=skeleton_links,
                                                       skeleton_link_distances=skeleton_link_distances)

        # Transforming image space coordinates to spatial space.
        self.x, self.y = transform_to_spatial_space(image_size=self.thinned_image.shape[0],
                                                    scaling_factor=self.scaling_factor,
                                                    pixel_coordinates=pixel_coordinates)

        # For the curve to be closed, the last point is re-added at the end.
        self.x.append(self.x[0])
        self.y.append(self.y[0])

    def spatial_comparison(self):
        """
        Debug function used for estimation.

        Two methods are used for the estimation:
        1) Visual - Comparison plot between the generated skeleton and the reference multifoil.
        2) Analytical - Measuring metric to estimate how close/similar the plots are to one another.
        """

        # Generating a multifoil used for the spatial evaluation/comparison.
        x2, y2 = generate_multifoil(a=self.multifoil_parameters['a'], b=self.multifoil_parameters['b'],
                                    lobes=self.multifoil_parameters['lobes'],
                                    number_of_points=self.number_of_coefficients)

        log.debug("Calculating similarity metrics")
        self.metrics = {
            "Average": measure_average_distance(
                curve1=np.column_stack((x2, y2)), curve2=np.column_stack((self.x, self.y))),
            "Hausdorff": measure_hausdorff_distance(
                curve1=np.column_stack((x2, y2)), curve2=np.column_stack((self.x, self.y)))
        }
        log.print_data(data=tabulate([[metric, "{:.3f}".format(self.metrics[metric])] for metric in self.metrics],
                                     headers=["Metric", "Value"], tablefmt="pretty"), log_level="info")

        if self.debug_mode:
            log.debug("Plotting the curves for visual comparison")
            plot(x1=self.x, y1=self.y, x2=x2, y2=y2, display_time=self.display_time)

    @measure_runtime
    def dft_2d(self):
        """
        TODO: Complete the docstring.
        """

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
            self.fourier_coefficients.append(a)

    def set_configuration_processing(self):
        """
        TODO: Complete the docstring.
        """

        log.info("Processing of the meta-shell using pre-defined parameters")

        self.doublet_processing(filter_size=self.processing_parameters['filter_size'],
                                global_threshold=self.processing_parameters['global_threshold'],
                                thinning_method=self.processing_parameters['thinning_method'])

        if self.debug_mode:
            self.shell.image = self.thinned_image
            self.shell.compare_to_original()

        self.spatial_conversion()

        self.spatial_comparison()

        self.dft_2d()

    def empirical_processing(self):
        """
        TODO: Complete the docstring.
        """

        log.info("Optimal processing of the meta-shell using an empirical method")

        best_parameters = {}
        best_metrics = {}
        best_score = math.inf
        # TODO: Add explanation about adding more loops if necessary to extend the optimal search.
        for thinning_method in ["ZS", "BST", "GH1", "GH2", "DLH"]:
            for filter_size in range(3, 50, 2):
                for global_threshold in [i / 10 for i in range(1, 10)]:
                    # Reset the image for display.
                    self.shell.reset_to_original_image()

                    try:
                        self.doublet_processing(filter_size=filter_size,
                                                global_threshold=global_threshold,
                                                thinning_method=thinning_method)

                        if self.debug_mode:
                            self.shell.image = self.thinned_image
                            self.shell.compare_to_original()

                        self.spatial_conversion()

                        self.spatial_comparison()

                        # Calculate weighted metric score.
                        # TODO: Add explanation why these are the weights.
                        current_score = 0.8 * self.metrics["Average"] + 0.2 * self.metrics["Hausdorff"]
                        if current_score < best_score:
                            best_score = current_score

                            best_parameters = {
                                "Thinning method": thinning_method,
                                "Filter size": filter_size,
                                "Global threshold": global_threshold,
                            }
                            best_metrics = copy.deepcopy(self.metrics)

                    except IndexError:
                        log.warning("Generated skeleton isn't connected")

        log.info("Summary:")
        log.print_data(data=best_parameters, log_level="info")
        log.print_data(data=tabulate([[metric, best_metrics[metric]] for metric in best_metrics],
                                     headers=["Metric", "Value"], tablefmt="pretty"), log_level="info")

        # Processing the meta-shell using the best found parameters.
        self.processing_parameters['thinning_method'] = best_parameters['Thinning method']
        self.processing_parameters['filter_size'] = best_parameters['Filter size']
        self.processing_parameters['global_threshold'] = best_parameters['Global threshold']
        self.set_configuration_processing()

