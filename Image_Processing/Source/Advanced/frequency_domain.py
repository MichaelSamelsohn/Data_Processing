"""
Script Name - frequency_domain.py

Purpose - Perform frequency-domain filtering on an image. Frequency-domain processing transforms an image via the 2-D
Discrete Fourier Transform (DFT/FFT), manipulates its spectrum H(u,v), and recovers the result with the inverse DFT.
Compared with spatial convolution, frequency-domain filters give precise control over which frequency bands are passed
or rejected, enable efficient large-kernel filtering via the convolution theorem, and allow operations (e.g. homomorphic
and notch filtering) that are awkward to express as spatial kernels.

Created by Michael Samelsohn, 27/02/26
"""

# Imports #
import numpy as np
from numpy import ndarray
from Image_Processing.Source.Basic.common import image_normalization
from Image_Processing.Settings.image_settings import *
from Utilities.decorators import book_reference, measure_runtime


# ──────────────────────────────────────────────────────────────────────────── #
# Internal helpers                                                              #
# ──────────────────────────────────────────────────────────────────────────── #

def _frequency_distance_map(shape: tuple[int, int]) -> ndarray:
    """
    Build the Euclidean-distance matrix D(u, v) used by all frequency-domain filter functions.

    After an fftshift the DC component sits at (M//2, N//2).  D(u, v) is the Euclidean distance of each spectral sample
    from that centre point:
                        D(u, v) = sqrt((u − M/2)² + (v − N/2)²)

    :param shape: (M, N) spatial dimensions of the image.

    :return:      Real-valued distance matrix of shape (M, N). D == 0 at the DC centre; increases monotonically towards
                  the corners.
    """

    M, N = shape
    u = np.arange(M) - M // 2   # row offsets from DC centre
    v = np.arange(N) - N // 2   # column offsets from DC centre
    V, U = np.meshgrid(v, u)
    return np.sqrt(U ** 2 + V ** 2)


def _apply_frequency_filter(image: ndarray, filter_mask: ndarray,
                             normalization_method: str) -> ndarray:
    """
    Internal pipeline: FFT → centre-shift → multiply by filter → un-shift → IFFT → normalize.

    The convolution theorem states that multiplication in the frequency domain is equivalent to convolution in the
    spatial domain.  This helper implements the complete frequency-domain filtering cycle:
                                    G(u, v) = H(u, v) · F(u, v)
                                    g(x, y) = Re{ IFFT{ G(u, v) } }
    where F = FFT{f} and H is the supplied filter mask.  The fftshift / ifftshift pair is applied so that the filter
    mask H is defined relative to the centred DC component.

    :param image:                Input grayscale image, pixel values in [0, 1].
    :param filter_mask:          Real- or complex-valued filter H(u, v), same shape as image.
    :param normalization_method: Passed verbatim to image_normalization.

    :return:                     Filtered image after IFFT, same shape as input.
    """

    log.debug("Computing 2-D FFT of the image")
    F_shifted = np.fft.fftshift(np.fft.fft2(image))

    log.debug("Applying the filter mask in the frequency domain")
    G_shifted = filter_mask * F_shifted

    log.debug("Computing the inverse FFT and discarding the negligible imaginary residual")
    result = np.real(np.fft.ifft2(np.fft.ifftshift(G_shifted)))

    return image_normalization(image=result, normalization_method=normalization_method)


# ──────────────────────────────────────────────────────────────────────────── #
# DFT / IDFT  (educational, manual implementation)                             #
# ──────────────────────────────────────────────────────────────────────────── #

@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 4.2 - Introduction to the Fourier Transform and the "
                          "Frequency Domain, p.221-225")
@measure_runtime
def dft_2d(image: ndarray) -> ndarray:
    """
    Compute the 2-D Discrete Fourier Transform using separable 1-D DFT matrices.

    The 2-D DFT is defined as:
                        F(u, v) = Σ_{x=0}^{M-1} Σ_{y=0}^{N-1} f(x,y) · e^{-j2π(ux/M + vy/N)}

    Because the complex exponential factorises as e^{-j2πux/M} · e^{-j2πvy/N}, the 2-D transform is separable: it can be
    computed by successive 1-D transforms, first along every row and then along every column.  In matrix form this
    reads:
                                              F = W_M · f · W_N^T
    where:
        W_M[u, x] = e^{-j2πux/M}   (M×M row-DFT matrix)
        W_N[v, y] = e^{-j2πvy/N}   (N×N column-DFT matrix)

    Complexity: O(M²·N + M·N²) = O(N³) for square images, far better than the O(N^4) naive double loop. numpy.fft.fft2
    uses the Cooley–Tukey FFT (O(N² log N)) and should be preferred for production use; this function is provided as an
    educational reference that exposes the separability property of the 2-D DFT.

    :param image: 2-D grayscale image array of shape (M, N), dtype float.

    :return:      Complex ndarray F(u, v) of shape (M, N). The DC component F(0, 0) equals the sum of all pixel values.
                  No fftshift is applied; DC is at the top-left corner.
    """

    log.info("Computing the 2-D DFT via separable row/column DFT matrices")

    if image.ndim != 2:
        log.raise_exception(
            message="dft_2d expects a 2-D (grayscale) image; got shape " + str(image.shape),
            exception=ValueError)

    M, N = image.shape
    log.debug(f"Image dimensions: M={M}, N={N}")

    log.debug("Building row DFT matrix W_M  (shape M×M)")
    u = np.arange(M).reshape(-1, 1)   # column vector  [0, 1, …, M-1]^T
    x = np.arange(M).reshape(1, -1)   # row    vector  [0, 1, …, M-1]
    W_M = np.exp(-2j * np.pi * u * x / M)   # W_M[u, x] = e^{-j2πux/M}

    log.debug("Building column DFT matrix W_N  (shape N×N)")
    v = np.arange(N).reshape(-1, 1)
    y = np.arange(N).reshape(1, -1)
    W_N = np.exp(-2j * np.pi * v * y / N)   # W_N[v, y] = e^{-j2πvy/N}

    log.debug("Computing F = W_M @ image @ W_N^T")
    return W_M @ image.astype(complex) @ W_N.T


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 4.2 - Introduction to the Fourier Transform and the "
                          "Frequency Domain, p.221-225")
@measure_runtime
def idft_2d(dft: ndarray) -> ndarray:
    """
    Compute the 2-D Inverse Discrete Fourier Transform using separable 1-D IDFT matrices.

    The 2-D IDFT is defined as: f(x, y) = (1/MN) · Σ_{u=0}^{M-1} Σ_{v=0}^{N-1} F(u,v) · e^{j2π(ux/M + vy/N)}
    Analogously to dft_2d, the separability of the exponential factorisation gives a matrix form:
                                    f = (1/MN) · W_M_inv · F · W_N_inv^T
    where W_M_inv[x, u] = e^{j2πxu/M} is the element-wise complex conjugate of W_M (without the normalisation factor
    1/M).

    Note - Floating-point arithmetic introduces negligible imaginary residuals; the real part is taken before returning.

    :param dft: Complex ndarray F(u, v) as produced by dft_2d, shape (M, N).

    :return:    Reconstructed spatial-domain image f(x, y), real-valued, shape (M, N).
    """

    log.info("Computing the 2-D IDFT via separable row/column IDFT matrices")

    M, N = dft.shape
    log.debug(f"Spectrum dimensions: M={M}, N={N}")

    log.debug("Building inverse row matrix W_M_inv  (shape M×M)")
    x = np.arange(M).reshape(-1, 1)
    u = np.arange(M).reshape(1, -1)
    W_M_inv = np.exp(2j * np.pi * x * u / M)   # conjugate of W_M

    log.debug("Building inverse column matrix W_N_inv  (shape N×N)")
    y = np.arange(N).reshape(-1, 1)
    v = np.arange(N).reshape(1, -1)
    W_N_inv = np.exp(2j * np.pi * y * v / N)

    log.debug("Computing f = (1/MN) · W_M_inv @ F @ W_N_inv^T  (taking real part)")
    result = (W_M_inv @ dft @ W_N_inv.T) / (M * N)
    return np.real(result)


# ──────────────────────────────────────────────────────────────────────────── #
# Ideal low-pass / high-pass filters                                            #
# ──────────────────────────────────────────────────────────────────────────── #

@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 4.3 - Smoothing Frequency-Domain Filters, p.240-247")
def ideal_lowpass_filter(image: ndarray, cutoff: float, normalization_method: str) -> ndarray:
    """
    Apply an ideal (binary) low-pass filter in the frequency domain.

    The ideal LPF transfer function is:
                                        H(u, v) = 1   if D(u, v) ≤ D₀
                                        H(u, v) = 0   otherwise
    where D(u, v) is the Euclidean distance from the DC component (after fftshift) and D₀ is the cutoff radius in pixels
    of the shifted spectrum.  All frequencies inside the disc of radius D₀ are passed without attenuation; all others
    are completely blocked.

    Warning: the abrupt transition produces ringing artefacts (Gibbs phenomenon) in the output image. Use the
    Butterworth or Gaussian variants for artefact-free results.

    :param image:                Grayscale image, pixel values in [0, 1].
    :param cutoff:               Cutoff frequency D₀ (pixels from DC in the shifted spectrum).
    :param normalization_method: Normalization applied to the IFFT output.

    :return:                     Low-pass filtered image, same shape as input.
    """

    log.info(f"Applying ideal low-pass filter with cutoff frequency D₀={cutoff}")

    D = _frequency_distance_map(image.shape)
    H = (D <= cutoff).astype(float)
    log.debug(f"Ideal LPF mask: {int(np.sum(H))} of {H.size} frequencies passed")

    return _apply_frequency_filter(image=image, filter_mask=H,
                                   normalization_method=normalization_method)


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 4.4 - Sharpening Frequency-Domain Filters, p.252-256")
def ideal_highpass_filter(image: ndarray, cutoff: float, normalization_method: str) -> ndarray:
    """
    Apply an ideal (binary) high-pass filter in the frequency domain.

    The ideal HPF transfer function is the complement of the ideal LPF:
                                            H(u, v) = 0   if D(u, v) ≤ D₀
                                            H(u, v) = 1   otherwise
    Because H_HP(u,v) = 1 − H_LP(u,v), the ideal HPF and ideal LPF are strictly complementary:
    IFFT{H_HP · F} + IFFT{H_LP · F} = f(x,y) for any image f.

    High-pass filtering removes slowly varying (low-frequency) components, retaining only sharp transitions such as
    edges and fine textures.  The abrupt cut causes ringing in the output image.

    :param image:                Grayscale image, pixel values in [0, 1].
    :param cutoff:               Cutoff frequency D₀ (pixels from DC in the shifted spectrum).
    :param normalization_method: Normalization applied to the IFFT output.

    :return:                     High-pass filtered image, same shape as input.
    """

    log.info(f"Applying ideal high-pass filter with cutoff frequency D₀={cutoff}")

    D = _frequency_distance_map(image.shape)
    H = (D > cutoff).astype(float)
    log.debug(f"Ideal HPF mask: {int(np.sum(H))} of {H.size} frequencies passed")

    return _apply_frequency_filter(image=image, filter_mask=H,
                                   normalization_method=normalization_method)


# ──────────────────────────────────────────────────────────────────────────── #
# Butterworth low-pass / high-pass filters                                      #
# ──────────────────────────────────────────────────────────────────────────── #

@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 4.3 - Smoothing Frequency-Domain Filters, p.247-252")
def butterworth_lowpass_filter(image: ndarray, cutoff: float, order: int,
                                normalization_method: str) -> ndarray:
    """
    Apply a Butterworth low-pass filter in the frequency domain.

    The Butterworth LPF has a smooth, monotonically decreasing transfer function that eliminates the ringing artefacts
    caused by the abrupt cut-off of the ideal LPF: H(u, v) = 1 / (1 + (D(u,v) / D₀)^{2n})

    Key properties:
        • At D = D₀:    H = 0.5  (3 dB point for all orders).
        • As n → ∞:     Butterworth → ideal binary filter (ringing reappears).
        • For small n:  The transition is very gradual (no ringing); for large n it sharpens.
        • At D = 0:     H = 1  (DC component fully passed).

    :param image:                Grayscale image, pixel values in [0, 1].
    :param cutoff:               Cutoff frequency D₀ (pixels from DC in the shifted spectrum).
    :param order:                Filter order n (positive integer). n=1 gives the flattest response.
    :param normalization_method: Normalization applied to the IFFT output.

    :return:                     Low-pass filtered image, same shape as input.
    """

    log.info(f"Applying Butterworth low-pass filter: D₀={cutoff}, order n={order}")

    D = _frequency_distance_map(image.shape)
    # Division by cutoff is safe: D=0 yields (0/D₀)^2n = 0, so H=1 (correct DC behaviour).
    H = 1.0 / (1.0 + (D / cutoff) ** (2 * order))
    log.debug(f"Butterworth LPF: H_max={H.max():.4f}, H_min={H.min():.6f}")

    return _apply_frequency_filter(image=image, filter_mask=H,
                                   normalization_method=normalization_method)


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 4.4 - Sharpening Frequency-Domain Filters, p.256-260")
def butterworth_highpass_filter(image: ndarray, cutoff: float, order: int,
                                 normalization_method: str) -> ndarray:
    """
    Apply a Butterworth high-pass filter in the frequency domain.

    Derived from the complementary relationship H_HP = 1 − H_LP, the Butterworth HPF is:
                                    H(u, v) = 1 / (1 + (D₀ / D(u,v))^{2n})
    This is algebraically equivalent to 1 − H_BW_LP(u,v): 1 − 1/(1 + x^2n)  =  x^2n / (1 + x^2n)  =  1 / (1 + x^{-2n})
    where x = D/D₀
    Therefore IFFT{H_BW_LP · F} + IFFT{H_BW_HP · F} = f(x,y) for any image f.

    The DC component (D=0) is completely blocked; frequencies far from DC are fully passed. This emphasises edges while
    smoothly suppressing flat regions.

    :param image:                Grayscale image, pixel values in [0, 1].
    :param cutoff:               Cutoff frequency D₀ (pixels from DC in the shifted spectrum).
    :param order:                Filter order n (positive integer).
    :param normalization_method: Normalization applied to the IFFT output.

    :return:                     High-pass filtered image, same shape as input.
    """

    log.info(f"Applying Butterworth high-pass filter: D₀={cutoff}, order n={order}")

    D = _frequency_distance_map(image.shape)
    # Replace D=0 (DC) with a tiny epsilon to avoid division by zero; H→0 there anyway.
    D_safe = np.where(D == 0, np.finfo(float).eps, D)
    H = 1.0 / (1.0 + (cutoff / D_safe) ** (2 * order))
    log.debug(f"Butterworth HPF: H_max={H.max():.4f}, H_min={H.min():.6f}")

    return _apply_frequency_filter(image=image, filter_mask=H,
                                   normalization_method=normalization_method)


# ──────────────────────────────────────────────────────────────────────────── #
# Gaussian low-pass / high-pass filters                                         #
# ──────────────────────────────────────────────────────────────────────────── #

@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 4.3 - Smoothing Frequency-Domain Filters, p.252")
def gaussian_lowpass_filter(image: ndarray, sigma: float, normalization_method: str) -> ndarray:
    """
    Apply a Gaussian low-pass filter in the frequency domain.

    The Gaussian LPF transfer function is: H(u, v) = e^{-D²(u,v) / (2σ²)}

    The Gaussian is the unique filter that is self-reciprocal under the Fourier transform: a Gaussian spectrum
    corresponds to a Gaussian spatial kernel.  This guarantees that no ringing occurs in the filtered output — the
    Gaussian LPF is the smoothest possible low-pass filter.

    The parameter σ controls the width of the pass-band (in pixels of the shifted spectrum):
        • Small σ → narrow pass-band → heavy blurring (only very low frequencies pass).
        • Large σ → wide pass-band  → mild blurring.

    :param image:                Grayscale image, pixel values in [0, 1].
    :param sigma:                Standard deviation σ of the Gaussian (pixels of the spectrum).
    :param normalization_method: Normalization applied to the IFFT output.

    :return:                     Low-pass filtered image, same shape as input.
    """

    log.info(f"Applying Gaussian low-pass filter with σ={sigma}")

    D = _frequency_distance_map(image.shape)
    H = np.exp(-(D ** 2) / (2.0 * sigma ** 2))
    log.debug(f"Gaussian LPF: H_max={H.max():.4f}, H_min={H.min():.6f}")

    return _apply_frequency_filter(image=image, filter_mask=H,
                                   normalization_method=normalization_method)


@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 4.4 - Sharpening Frequency-Domain Filters, p.260-263")
def gaussian_highpass_filter(image: ndarray, sigma: float, normalization_method: str) -> ndarray:
    """
    Apply a Gaussian high-pass filter in the frequency domain.

    The complementary relationship gives the Gaussian HPF transfer function: H(u, v) = 1 − e^{-D²(u,v) / (2σ²)}

    At D = 0 (DC): H = 0 — the mean brightness is completely removed.
    At D → ∞:      H → 1 — very high frequencies are passed without attenuation.

    Like the Butterworth HPF, the Gaussian HPF sharpens the image by emphasising edges. Because
    H_GHP(u,v) = 1 − H_GLP(u,v), the two are strictly complementary: IFFT{H_GLP · F} + IFFT{H_GHP · F} = f(x,y).

    :param image:                Grayscale image, pixel values in [0, 1].
    :param sigma:                Standard deviation σ (pixels of the spectrum).
                                 Smaller σ → stronger high-pass effect.
    :param normalization_method: Normalization applied to the IFFT output.

    :return:                     High-pass filtered image, same shape as input.
    """

    log.info(f"Applying Gaussian high-pass filter with σ={sigma}")

    D = _frequency_distance_map(image.shape)
    H = 1.0 - np.exp(-(D ** 2) / (2.0 * sigma ** 2))
    log.debug(f"Gaussian HPF: H_max={H.max():.4f}, H_min={H.min():.6f}")

    return _apply_frequency_filter(image=image, filter_mask=H,
                                   normalization_method=normalization_method)


# ──────────────────────────────────────────────────────────────────────────── #
# Notch reject filter                                                           #
# ──────────────────────────────────────────────────────────────────────────── #

@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 4.8 - Selective Filtering, p.277-283")
def notch_reject_filter(image: ndarray, notch_centers: list[tuple[int, int]],
                         notch_radius: float, normalization_method: str) -> ndarray:
    """
    Apply an ideal notch reject filter to remove periodic noise.

    Periodic noise in an image manifests as bright impulse pairs (±u₀, ±v₀) in the magnitude spectrum. A notch reject
    filter selectively zeroes those pairs while leaving the rest of the spectrum intact.

    Because the DFT of a real image is conjugate-symmetric, noise at (u₀, v₀) always
    has a conjugate partner at (−u₀, −v₀).  The filter must suppress both:
                        H(u, v) = 0   if D_k(u,v) ≤ R₀  or  D_{-k}(u,v) ≤ R₀,  for any pair k
                        H(u, v) = 1   otherwise
    where:
        D_k(u,v)   = sqrt((u − M/2 − u₀ₖ)² + (v − N/2 − v₀ₖ)²)
        D_{-k}(u,v) = sqrt((u − M/2 + u₀ₖ)² + (v − N/2 + v₀ₖ)²)

    The notch centres (u₀, v₀) are expressed as pixel offsets from the DC component in the centred (shifted) spectrum.
    They can be read off the shifted magnitude spectrum by identifying the bright impulse locations relative to the
    image centre.

    If notch_centers is empty, an all-pass filter H = 1 is applied (no-op).

    :param image:                Grayscale image, pixel values in [0, 1].
    :param notch_centers:        List of (u₀, v₀) offsets from the DC centre.  Each entry
                                 creates two circular rejection zones (the notch and its
                                 conjugate symmetric counterpart).
    :param notch_radius:         Radius R₀ of each rejection disc (pixels of the spectrum).
    :param normalization_method: Normalization applied to the IFFT output.

    :return:                     Image with periodic noise attenuated, same shape as input.
    """

    log.info(f"Applying notch reject filter: {len(notch_centers)} notch pair(s), "
             f"radius R₀={notch_radius}")

    M, N = image.shape
    H = np.ones((M, N), dtype=float)   # Start from an all-pass filter.

    u_axis = np.arange(M) - M // 2
    v_axis = np.arange(N) - N // 2
    V, U = np.meshgrid(v_axis, u_axis)   # broadcast grids, shape (M, N)

    for u0, v0 in notch_centers:
        log.debug(f"Adding notch pair at (u₀, v₀) = ({u0}, {v0})")
        D_k     = np.sqrt((U - u0) ** 2 + (V - v0) ** 2)   # primary notch
        D_neg_k = np.sqrt((U + u0) ** 2 + (V + v0) ** 2)   # conjugate notch
        H[D_k     <= notch_radius] = 0
        H[D_neg_k <= notch_radius] = 0

    log.debug(f"Notch filter: {int(np.sum(H == 0))} of {H.size} frequencies rejected")

    return _apply_frequency_filter(image=image, filter_mask=H,
                                   normalization_method=normalization_method)


# ──────────────────────────────────────────────────────────────────────────── #
# Homomorphic filter                                                            #
# ──────────────────────────────────────────────────────────────────────────── #

@book_reference(book=GONZALES_WOODS_BOOK,
                reference="Chapter 4.9 - Image Enhancement Using the Homomorphic Filter, p.283-287")
def homomorphic_filter(image: ndarray, gamma_l: float, gamma_h: float, c: float,
                        sigma: float, normalization_method: str) -> ndarray:
    """
    Apply a homomorphic filter to simultaneously compress illumination and expand reflectance.

    The illumination-reflectance model decomposes image intensity as a product: f(x, y) = i(x, y) · r(x, y)
    where i(x, y) is the slowly varying illumination (captured by low-frequency components) and r(x, y) is the rapidly
    varying reflectance detail (high-frequency components). Taking the natural logarithm converts the multiplicative
    relationship to an additive one: z(x, y) = ln f(x, y) = ln i(x, y) + ln r(x, y)

    The homomorphic filter H(u, v) is then designed to attenuate low-frequency illumination (γ_L < 1) while boosting
    high-frequency reflectance (γ_H > 1).  A Gaussian high-pass-based transfer function achieves this continuously:
                            H(u, v) = (γ_H − γ_L) · [1 − e^{−c · D²(u,v) / (2σ²)}] + γ_L
        • At D = 0  (DC, low frequencies):  H = γ_L    → illumination is attenuated.
        • At D → ∞  (high frequencies):      H = γ_H    → reflectance is amplified.
        • c controls how steeply H transitions from γ_L to γ_H.

    Processing pipeline:
        1. z(x,y)  = ln(f(x,y) + ε)          (log; ε = machine epsilon prevents log(0))
        2. Z(u,v)  = FFT{ z(x,y) }            (forward transform on log image)
        3. S(u,v)  = H(u,v) · Z(u,v)          (filter in the frequency domain)
        4. s(x,y)  = Re{ IFFT{ S(u,v) } }     (inverse transform)
        5. g(x,y)  = exp(s(x,y))              (exponentiate to undo the log)
        6. Normalize g(x,y) to the target range via normalization_method.

    :param image:                Grayscale image, positive pixel values (ideally in [0, 1]).
    :param gamma_l:              Low-frequency gain γ_L (< 1 suppresses illumination variation).
    :param gamma_h:              High-frequency gain γ_H (> 1 boosts reflectance detail).
    :param c:                    Steepness constant controlling the sharpness of the transition.
    :param sigma:                Standard deviation σ of the embedded Gaussian HPF (pixels of the shifted spectrum).
    :param normalization_method: Normalization applied to the exponentiated output.

    :return:                     Homomorphically filtered image with compressed dynamic range and enhanced fine detail,
                                 same shape as input.
    """

    log.info(f"Applying homomorphic filter: γ_L={gamma_l}, γ_H={gamma_h}, c={c}, σ={sigma}")

    log.debug("Step 1 – Taking the natural logarithm of the image")
    epsilon = np.finfo(float).eps           # avoid log(0) for zero-valued pixels
    z = np.log(image + epsilon)

    log.debug("Step 2 – Computing the FFT of the log image")
    Z_shifted = np.fft.fftshift(np.fft.fft2(z))

    log.debug("Step 3 – Building the homomorphic transfer function H(u,v)")
    D = _frequency_distance_map(image.shape)
    H = (gamma_h - gamma_l) * (1.0 - np.exp(-c * D ** 2 / (2.0 * sigma ** 2))) + gamma_l

    log.debug("Step 4 – Multiplying in the frequency domain")
    S_shifted = H * Z_shifted

    log.debug("Step 5 – Inverse FFT")
    s = np.real(np.fft.ifft2(np.fft.ifftshift(S_shifted)))

    log.debug("Step 6 – Exponentiating to invert the logarithm")
    g = np.exp(s)

    return image_normalization(image=g, normalization_method=normalization_method)
