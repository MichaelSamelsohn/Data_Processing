from Image_Processing.Advanced.thinning import *
from Image_Processing.Advanced.segmentation import *


def doublet_processing(doublet: ndarray):
    """
    TODO: Complete the docstring.
    """

    # Stretching the contrast of the image.
    stretched_image = contrast_stretching(image=doublet)

    # Thresholding the image to extract the high intensity contour.
    high_intensity_contour = thresholding(image=stretched_image, threshold_value=0.75)

    # Thresholding the negative image to extract the low intensity contour.
    negative_image = negative(image=stretched_image)
    low_intensity_contour = thresholding(image=negative_image, threshold_value=0.75)

    # Blurring the image to join the two intensity contours.
    blurred = blur_image(image=low_intensity_contour + high_intensity_contour, filter_size=23)

    # Thresholding the blurred image to obtain a blob centered on the required line.
    blob = global_thresholding(image=blurred, initial_threshold=0.1)

    thinned_image = parallel_sub_iteration_thinning(image=blob, method="ZS", is_pre_thinning=False)

    return thinned_image
