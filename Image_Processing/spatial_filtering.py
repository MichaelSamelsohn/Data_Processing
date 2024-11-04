"""
Script Name - spatial_filtering.py

Purpose - Perform spatial filtering on an image. Intensity transformations refer to changes based on a neighbourhood (as
opposed to intensity transformations, pixel based operations).

Created by Michael Samelsohn, 20/05/22
"""

# Imports #
import numpy as np
from numpy import ndarray
from common import generate_filter, convolution_2d, image_normalization
from Settings import image_settings
from Utilities.decorators import book_reference
from Settings.settings import log

# Constants #
SOBEL_OPERATORS = {
    "VERTICAL": np.array([[1, 2, 1],
                          [0, 0, 0],
                          [-1, -2, -1]]),
    "HORIZONTAL": np.array([[-1, 0, 1],
                            [-2, 0, 2],
                            [-1, 0, 1]])
}


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 3.5 - Smoothing (Lowpass) Spatial Filters, p.164-175")
def blur_image(image: ndarray, filter_type=image_settings.DEFAULT_FILTER_TYPE,
               filter_size=image_settings.DEFAULT_FILTER_SIZE, padding_type=image_settings.DEFAULT_PADDING_TYPE,
               sigma=image_settings.DEFAULT_SIGMA_VALUE,
               normalization_method=image_settings.DEFAULT_NORMALIZATION_METHOD) -> ndarray:
    """
    Apply a low pass filter (blur) on an image.

    :param image: The image to be filtered.
    :param filter_type: The filter type.
    :param filter_size: The filter size.
    :param padding_type: The padding type used for the convolution.
    :param sigma: Standard deviation (relevant only if filter_type='gaussian').
    :param normalization_method: Method used for image normalization. Options are - unchanged, stretch, cutoff.
    Note - Since blurring kernels can't introduce negative or above 1 pixel values, the cutoff option is meaningless.
    TODO: Maybe stretch too?

    :return: Filtered image.
    """

    log.info(f"Blurring image with the filter type - {filter_type}")

    # Generating the kernel.
    kernel = generate_filter(filter_type=filter_type, filter_size=filter_size, sigma=sigma)

    # Convolving the image with the generated kernel.
    return convolution_2d(image=image, kernel=kernel, padding_type=padding_type,
                          normalization_method=normalization_method)


"""
Background on derivatives:
Derivatives of a digital function are defined in terms of differences. There are various ways to define these 
differences. However, we require that any definition we use for a first derivative:
    1. Must be zero in areas of constant intensity.
    2. Must be nonzero at the onset of an intensity step or ramp.
    3. Must be nonzero along intensity ramps.
Similarly, any definition of a second derivative:
    1. Must be zero in areas of constant intensity.
    2. Must be nonzero at the onset and end of an intensity step or ramp.
    3. Must be zero along intensity ramps.

We are dealing with digital quantities whose values are finite. Therefore, the maximum possible intensity change also is
finite, and the shortest distance over which that change can occur is between adjacent pixels. A basic definition of the
first-order derivative of a one-dimensional function f(x) is the difference:
                                                    ∂f/∂x=f(x+1)-f(x)
We define the second-order derivative of f(x) as the difference:
                                              ∂^2f/∂x^2=f(x+1)+f(x-1)-2f(x)
                                               
Further detailed explanation on derivatives:
We obtain an approximation to the first-order derivative at an arbitrary point x of a one-dimensional function f(x) by 
expanding the function f(x+delta_x) into a Taylor series about x:
                         f(x+delta_x) = f(x) + delta_x*∂f/∂x + (delta_x^2)/2 * ∂^2f/∂x^2 + • • •
where delta_x is the separation between samples of f. For our purposes, this separation is measured in pixel units. 
Thus, following the convention in the book, delta_x=1 for the sample preceding x and delta_x=−1 for the sample following 
x.
When delta_x=1, the taylor series becomes:
                                    f(x+1) = f(x) + ∂f/∂x + (1/2)*∂^2f/∂x^2 + • • •
Similarly, for delta_x=-1:
                                    f(x-1) = f(x) - ∂f/∂x + (1/2)*∂^2f/∂x^2 + • • •        
In what follows, we compute intensity differences using just a few terms of the Taylor series. For first-order 
derivatives we use only the linear terms, and we can form differences in one of three ways.
The forward difference is:                      ∂f/∂x=f(x+1)-f(x)
The backward difference is:                     ∂f/∂x=f(x)-f(x-1)
The central difference is (f(x+1)-f(x-1)):   ∂f/∂x=[f(x+1)-f(x-1)]/2       

The higher terms of the series that we did not use represent the error between an exact and an approximate derivative 
expansion. In general, the more terms we use from the Taylor series to represent a derivative, the more accurate the 
approximation will be. To include more terms implies that more points are used in the approximation, yielding a lower 
error. However, it turns out that central differences have a lower error for the same number of points. For this reason,
derivatives are usually expressed as central differences.

When adding the equations for f(x+1) and f(x-1), we get the second derivative:
                                         ∂^2f/∂x^2 = f(x+1) - 2f(x) + f(x-1)                                            
"""


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 3.6 - Sharpening (Highpass) Spatial Filters, p.178-182")
def laplacian_gradient(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                       include_diagonal_terms=image_settings.DEFAULT_INCLUDE_DIAGONAL_TERMS,
                       normalization_method=image_settings.DEFAULT_NORMALIZATION_METHOD) -> ndarray:
    """
    Apply the Laplacian gradient (second derivative) on an image.

    Based on the conclusions reached above, we know that point detection should be based on the second derivative which,
    means using the Laplacian:
                                          ∇^2f(x,y) = ∂^2f/∂x^2 + ∂^2f/∂y^2
    where the partial derivatives are computed using the second-order finite differences.
    The Laplacian is then:
                             ∇^2f(x,y) = f(x+1,y) + f(x-1,y) + f(x,y+1) + f(x,y-1) - 4f(x,y)
    This expression can be implemented using the Laplacian kernel:
                                                    0    1    0

                                                    1   -4    1

                                                    0    1    0

    The kernel above is isotropic for rotations in increments of 90° with respect to the x- and y-axes. The diagonal
    directions can be incorporated in the definition of the digital Laplacian by adding four more terms:
    ∇^2f(x,y) =
      f(x+1,y) + f(x-1,y) + f(x,y+1) + f(x,y-1)                Vertical/Horizontal direction terms
    + f(x-1,y-1) + f(x-1, y+1) + f(x+1, y-1) + f(x+1,y+1)      Diagonal direction terms
    - 8f(x,y)
    This expression can be implemented using the extended Laplacian kernel:
                                                    1    1    1

                                                    1   -8    1

                                                    1    1    1

    :param image: The image for applying a Laplacian gradient.
    :param padding_type: Padding type used for applying the kernel.
    :param include_diagonal_terms: Boolean determining if diagonal terms are included in the gradient.
    :param normalization_method: Method used for image normalization. Options are - unchanged, stretch, cutoff.

    :return: Laplacian (smoothed) image.
    """

    log.info(f"Applying the Laplacian kernel ({'with' if include_diagonal_terms else 'without'} diagonal terms) "
             f"on the image")

    laplacian_kernels = {
        "WITHOUT_DIAGONAL_TERMS": np.array([[0, 1, 0],
                                            [1, -4, 1],
                                            [0, 1, 0]]),
        "WITH_DIAGONAL_TERMS": np.array([[1, 1, 1],
                                         [1, -8, 1],
                                         [1, 1, 1]])
    }
    laplacian_kernel = laplacian_kernels["WITHOUT_DIAGONAL_TERMS"] if not include_diagonal_terms \
        else laplacian_kernels["WITH_DIAGONAL_TERMS"]

    # Convolving the image with the generated kernel.
    return convolution_2d(image=image, kernel=laplacian_kernel, padding_type=padding_type,
                          normalization_method=normalization_method)


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 3.6 - Sharpening (Highpass) Spatial Filters, p.178-182")
def laplacian_image_sharpening(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                               include_diagonal_terms=image_settings.DEFAULT_INCLUDE_DIAGONAL_TERMS) -> ndarray:
    """
    Perform image sharpening using the laplacian operator.

    Because the Laplacian is a derivative operator, it highlights sharp intensity transitions in an image and
    de-emphasizes regions of slowly varying intensities. This will tend to produce images that have grayish edge lines
    and other discontinuities, all superimposed on a dark, featureless background. Background features can be
    “recovered” while still preserving the sharpening effect of the Laplacian by adding the Laplacian image to the
    original. As noted in the previous paragraph, it is important to keep in mind which definition of the Laplacian is
    used. If the definition used has a negative center coefficient, then we subtract the Laplacian image from the
    original to obtain a sharpened result. Thus, the basic way in which we use the Laplacian for image sharpening is:
                                                g(x,y)=f(x,y)-∇^2f(x,y)
    where f(x,y) and g(x,y) are the input and sharpened images, respectively.

    :param image: The image for sharpening.
    :param padding_type: The padding type used for the convolution.
    :param include_diagonal_terms: Boolean determining if diagonal terms are included in the gradient.

    :return: Sharpened image.
    """

    log.info("Segmenting the image using the Laplacian operator")

    # Applying the Laplacian kernel on the image.
    post_laplacian_image = laplacian_gradient(image=image, padding_type=padding_type,
                                              include_diagonal_terms=include_diagonal_terms,
                                              normalization_method='cutoff')

    log.debug("Subtracting the Laplacian image from the original one")
    return image - post_laplacian_image


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 3.6 - Sharpening (Highpass) Spatial Filters, p.182-184")
def high_boost_filter(image: ndarray, filter_type=image_settings.DEFAULT_FILTER_TYPE,
                      filter_size=image_settings.DEFAULT_FILTER_SIZE,
                      padding_type=image_settings.DEFAULT_PADDING_TYPE, k=image_settings.DEFAULT_K_VALUE) -> ndarray:
    """
    Use a high boost filter (un-sharp masking) to sharpen the image.

    Subtracting an un-sharp (smoothed) version of an image from the original image is process that has been used since
    the 1930s by the printing and publishing industry to sharpen images. This process, called un-sharp masking, consists
    of the following steps:
    1. Blur the original image.
    2. Subtract the blurred image from the original (the resulting difference is called the mask.)
    3. Add the mask to the original.

    The mask in equation form is given by:
                                            g_mask(x,y) = f(x,y) - f_blur(x,y)
    Then we add a weighted portion of the mask back to the original image:
                                             g(x,y) = f(x,y) - k*g_mask(x,y)
    Where we included a weight, k (k≥0), for generality.
    When k = 1 we have un-sharp masking, as defined above.
    When k > 1, the process is referred to as high-boost filtering.
    Choosing k < 1 reduces the contribution of the un-sharp mask.

    :param image: The image for sharpening.
    :param filter_type: The filter used for the image blurring.
    :param filter_size: The filter size used for the image blurring.
    :param padding_type: The padding type used for the convolution.
    :param k: Weight used to determine if un-sharp masking (k=1) is used or high-boost filtering (k>1).

    :return: Sharpened image.
    """

    log.info("Performing un-sharp masking") if k == 1 else log.info("Performing high-boost filtering")

    # Blurring the image.
    blurred_image = blur_image(image=image, filter_type=filter_type, filter_size=filter_size, padding_type=padding_type)

    log.debug("Generating the mask (subtracting the blurred image from the original one)")
    mask = image - blurred_image

    log.debug("Adding the weighted mask to the original image")
    return image + k * mask


@book_reference(book=image_settings.GONZALES_WOODS_BOOK,
                reference="Chapter 3.6 - Sharpening (Highpass) Spatial Filters, p.184-188")
# TODO: Find the article reference.
def sobel_filter(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                 normalization_method=image_settings.DEFAULT_NORMALIZATION_METHOD) -> (ndarray, ndarray):
    """
    Use a sobel operator filter (first-order derivative) to sharpen the image.

    Quick reminder:
    Derivatives of a digital function are defined in terms of differences. There are various ways to define these
    differences. However, we require that any definition we use for a first derivative:
    1. Must be zero in areas of constant intensity.
    2. Must be nonzero at the onset of an intensity step or ramp.
    3. Must be nonzero along intensity ramps.

    The magnitude (length), denoted as M(x,y) (the vector norm notation f is also used frequently), where:
                                        M(x,y) = sqrt((∂f/∂x)^2 + (∂f/∂y)^2)
    is the value at (x,y) of the rate of change in the direction of the gradient vector. Note that M(x,y) is an image
    of the same size as the original, created when x and y are allowed to vary over all pixel locations in f. It is
    common practice to refer to this image as the gradient image (or simply as the gradient when the meaning is clear).

    we prefer to use kernels of odd sizes because they have a unique, (integer) center of spatial symmetry. The smallest
    kernels in which we are interested are of size 3x3. Approximations to ∂f/∂x and ∂f/∂y are the Sobel operators:
                                           -1  -2   -1     -1    0    1

                                           0    0    0     -2    0    2

                                           1    2    1     -1    0    1

    The idea behind using a weight value of 2 in the center coefficient is to achieve some smoothing by giving more
    importance to the center point. The coefficients in all the kernels sum to zero, so they would give a response of
    zero in areas of constant intensity, as expected of a derivative operator. As noted earlier, when an image is
    convolved with a kernel whose coefficients sum to zero, the elements of the resulting filtered image sum to zero
    also, so images convolved with the kernels will have negative values in general. The computations of gx and gy are
    linear operations and are implemented using convolution, as noted above.

    The nonlinear aspect of sharpening with the gradient is the computation of M(x,y) involving squaring and square
    roots, or the use of absolute values, all of which are nonlinear operations. These operations are performed after
    the linear process (convolution) that yields ∂f/∂x and ∂f/∂y.

    :param image: The image for sharpening.
    :param padding_type: The padding type used for the convolution.
    :param normalization_method: Method used for image normalization. Options are - unchanged, stretch, cutoff.

    :return: Tuple containing the magnitude (sharpened) and direction images.
    """

    log.info("Applying the Laplacian kernel on the image")

    log.debug("Calculating the horizontal-directional derivative")
    gx = convolution_2d(image=image, kernel=SOBEL_OPERATORS["HORIZONTAL"], padding_type=padding_type,
                        normalization_method='unchanged')
    log.debug("Calculating the vertical-directional derivative")
    gy = convolution_2d(image=image, kernel=SOBEL_OPERATORS["VERTICAL"], padding_type=padding_type,
                        normalization_method='unchanged')

    log.debug("Calculating the magnitude (length) of the image gradient")
    magnitude = np.sqrt(np.power(gx, 2) + np.power(gy, 2))

    log.debug("Calculating the direction (angle) of the image gradient")
    """
    When calculating the arctan of a value, there are two potential problems:
    1) when x=0 (possibly, y too).
    2) When x is negative. In this case, the angle that we find isn't in the range of an entire circle.
    the method np.arctan2 handles both issues with the following definition:
    arctan(y/x),       if x>0
    arctan(y/x) + pi,  if x<0, y>=0
    arctan(y/x) - pi,  if x<0, y<0
    +pi/2,             if x=0, y>0
    -pi/2,             if x=0, y<0
    undefined,         if x=0,y=0
    """
    direction = np.arctan2(gy, gx)  # In radians.

    return {
        "Magnitude": image_normalization(image=magnitude, normalization_method=normalization_method),
        "Direction": image_normalization(image=direction, normalization_method=normalization_method)
    }
