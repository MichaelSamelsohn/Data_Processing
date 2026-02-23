# Image Processing Module

A comprehensive digital image processing library implementing classical algorithms from *"Digital Image Processing (4th ed.)" by Gonzales & Woods*. The module covers the full pipeline from basic intensity transformations to advanced segmentation, morphological operations, and image thinning.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Settings](#settings)
- [Core Class: Image](#core-class-image)
- [Basic Operations](#basic-operations)
- [Intensity Transformations](#intensity-transformations)
- [Spatial Filtering](#spatial-filtering)
- [Segmentation](#segmentation)
- [Noise Models](#noise-models)
- [Image Restoration](#image-restoration)
- [Morphology](#morphology)
- [Thinning](#thinning)
- [MetaShell Sub-Module](#metashell-sub-module)
- [Demo (main.py)](#demo-mainpy)

---

## Overview

The Image Processing module provides a class-based interface (`Image`) that wraps all processing algorithms. Each operation appends its result to an internal buffer, enabling side-by-side comparison of multiple processing stages. Algorithms are traced back to their textbook source via `@book_reference` and `@article_reference` decorators.

---

## Project Structure

```
Image_Processing/
├── Images/                     # Input images (e.g., Lena.png)
├── References/                 # Article/paper reference materials
├── Settings/
│   └── image_settings.py       # Centralized constants and defaults
├── Source/
│   ├── Basic/
│   │   ├── image.py            # Core Image class
│   │   └── common.py           # Shared utility functions
│   └── Advanced/
│       ├── intensity_transformations.py
│       ├── spatial_filtering.py
│       ├── segmentation.py
│       ├── noise_models.py
│       ├── restoration.py
│       ├── morphology.py
│       └── thinning.py
│   └── Metashells/
│       └── meta_shells.py      # Shell-shape analysis sub-module
└── main.py                     # Demo script
```

---

## Settings

**File:** `Settings/image_settings.py`

Centralizes all module-wide constants and default parameter values.

| Constant | Value | Description |
|---|---|---|
| `DEFAULT_IMAGE_PATH` | `Lena.png` | Default input image |
| `GONZALES_WOODS_BOOK` | `"Digital Image Processing..."` | Book citation string |
| `DEFAULT_FILTER_SIZE` | `3` | Default spatial filter size |
| `DEFAULT_SIGMA_VALUE` | `1` | Default Gaussian sigma |
| `DEFAULT_HARRIS_K_VALUE` | `0.05` | Harris detector sensitivity constant |
| `DEFAULT_GAUSSIAN_SIGMA` | `0.01` | Default Gaussian noise sigma |
| `DEFAULT_THINNING_METHOD` | `"ZS"` | Default thinning algorithm |
| `DEFAULT_STRUCTURING_ELEMENT` | `np.ones((3,3))` | Default morphological structuring element |

---

## Core Class: Image

**File:** `Source/Basic/image.py`

The central class that loads images and exposes all processing operations as methods.

### Initialization

```python
image = Image(image_path="path/to/image.png")
```

Supports `.png`, `.jpg`, and MATLAB `.mat` files.

### Internal Buffer

Each processing operation appends a dictionary entry to `_image_buffer`:

```python
{"Name": "<operation_name>", "Image": <ndarray>}
```

| Attribute | Description |
|---|---|
| `_image_buffer` | List of processed image stages |
| `_original_image` | The unmodified source image |
| `_last_image` | Most recently processed image |

### Key Methods

| Method | Description |
|---|---|
| `reset_to_original_image()` | Clears the buffer and resets to the source image |
| `convert_to_grayscale()` | Converts to grayscale using the NTSC formula |
| `display_all_images()` | Displays all buffered images side by side |
| `compare_to_original()` | Displays the original alongside the latest result |
| `plt_show(timeout=None)` | Shows a matplotlib figure with optional auto-close |

---

## Basic Operations

**File:** `Source/Basic/common.py`

Low-level utility functions used across all advanced modules.

### `convert_to_grayscale(image)`
Converts an RGB image to grayscale using the NTSC luminance formula:
```
Y = 0.2989 * R + 0.5870 * G + 0.1140 * B
```

### `convolution_2d(image, kernel, padding_type, normalization_method)`
Core 2D convolution engine. Decorated with `@measure_runtime`.

- **`padding_type`**: controls border handling
- **`normalization_method`**: `unchanged` | `stretch` | `cutoff`

### `generate_filter(filter_type, filter_size, sigma)`
Generates Box or Gaussian filter kernels.

### `image_normalization(image, normalization_method)`
Normalizes pixel values. Methods:
- `unchanged` — no change
- `stretch` — linearly maps min→0, max→1
- `cutoff` — clips values to [0, 1]

### `connected_component_4(image, ...)` / `connected_component_8(image, ...)`
Recursive connected-component labeling with 4-connectivity and 8-connectivity. Decorated with `@log_suppression` to silence verbose recursive logging.

### Additional Utilities
- `use_lookup_table()` — O(1) pixel-wise transform via pre-computed table
- `contrast_stretching()` — linear contrast enhancement
- `pad_image()` / `extract_sub_image()` — border management helpers

---

## Intensity Transformations

**File:** `Source/Advanced/intensity_transformations.py`

> Reference: *Gonzales & Woods, Chapter 3*

All functions decorated with `@book_reference`.

| Function | Description | Key Parameters |
|---|---|---|
| `negative(image)` | Computes `L-1-f(x,y)` (inverts intensities) | — |
| `gamma_correction(image, gamma)` | Applies `c * f(x,y)^gamma` power-law transform | `gamma`: < 1 brightens, > 1 darkens |
| `bit_plane_reconstruction(image, degree_of_reduction)` | Reconstructs image using only the top N bit planes | `degree_of_reduction`: 1–7 |
| `bit_plane_slicing(image, bit_plane)` | Extracts a single bit plane | `bit_plane`: 1–8 |

`bit_plane_reconstruction` and `bit_plane_slicing` use the `@scale_pixel_values(255)` decorator to rescale output.

---

## Spatial Filtering

**File:** `Source/Advanced/spatial_filtering.py`

> Reference: *Gonzales & Woods, Chapter 3.5–3.6*

### `blur_image(image, filter_type, filter_size, padding_type, sigma, normalization_method)`
Applies a low-pass (smoothing) filter via 2D convolution.
- `filter_type`: `"box"` | `"gaussian"`
- `filter_size`: kernel dimensions (odd integer)
- `sigma`: relevant only for Gaussian filter

### `laplacian_gradient(image, padding_type, include_diagonal_terms, normalization_method)`
Applies the Laplacian second-derivative operator.

**Without diagonal terms (isotropic at 90°):**
```
 0   1   0
 1  -4   1
 0   1   0
```

**With diagonal terms (fully isotropic):**
```
 1   1   1
 1  -8   1
 1   1   1
```

### `laplacian_image_sharpening(image, padding_type, include_diagonal_terms)`
Sharpens an image by subtracting the Laplacian from the original:
```
g(x,y) = f(x,y) - ∇²f(x,y)
```

### `high_boost_filter(image, filter_type, filter_size, padding_type, k)`
Implements unsharp masking (`k=1`) or high-boost filtering (`k>1`):
```
mask = f(x,y) - f_blur(x,y)
g(x,y) = f(x,y) + k * mask
```

### `sobel_filter(image, padding_type, normalization_method)`
Applies first-order derivative Sobel operators. Returns a dict:
```python
{"Magnitude": ndarray, "Direction": ndarray}
```
Magnitude: `M(x,y) = sqrt(gx² + gy²)`
Direction: `arctan2(gy, gx)` (radians, via `np.arctan2` for full-circle range)

**Sobel kernels:**
```
Vertical (∂f/∂y):    Horizontal (∂f/∂x):
 1   2   1           -1   0   1
 0   0   0           -2   0   2
-1  -2  -1           -1   0   1
```

---

## Segmentation

**File:** `Source/Advanced/segmentation.py`

> Reference: *Gonzales & Woods, Chapter 10*

### Point & Line Detection

| Function | Description |
|---|---|
| `isolated_point_detection(image, ...)` | Detects isolated pixels using Laplacian kernel |
| `line_detection(image, ...)` | Detects lines in 4 directions using directional kernels |
| `kirsch_edge_detection(image, ...)` | Edge detection using 8 compass-direction Kirsch kernels |

### `harris_corner_detector(image, k, ...)`
Five-step corner detection:
1. Compute Sobel gradients (Ix, Iy)
2. Smooth Ix², Iy², IxIy with Gaussian
3. Build structure tensor M at each pixel
4. Compute Harris response: `R = det(M) - k * tr(M)²`
5. Non-maximum suppression to isolate corner peaks

`k` (default `0.05`) controls corner/edge sensitivity.

### `marr_hildreth_edge_detection(image, sigma, ...)`
Laplacian-of-Gaussian (LoG) edge detection:
1. Smooth with Gaussian
2. Apply Laplacian
3. Detect zero-crossings as edge locations

### `canny_edge_detection(image, sigma, low_threshold, high_threshold, ...)`
Full Canny pipeline:
1. Gaussian smoothing
2. Sobel gradient (magnitude + direction)
3. Non-maxima suppression along gradient direction
4. Hysteresis thresholding (strong / weak / suppressed edges)

### Thresholding

| Function | Description |
|---|---|
| `thresholding(image, threshold)` | Simple binary threshold |
| `global_thresholding(image, delta_threshold)` | Iterative threshold estimation until convergence |
| `otsu_global_thresholding(image)` | Maximizes between-class variance (Otsu's method) |

---

## Noise Models

**File:** `Source/Advanced/noise_models.py`

> Reference: *Gonzales & Woods, Chapter 5*

All functions add noise to an image and return the corrupted result.

| Function | Distribution | Key Parameters |
|---|---|---|
| `add_gaussian_noise(image, sigma)` | Gaussian (normal) | `sigma`: std dev (default `0.01`) |
| `add_rayleigh_noise(image)` | Rayleigh | — |
| `add_erlang_noise(image)` | Erlang (Gamma) | — |
| `add_exponential_noise(image)` | Exponential | — |
| `add_uniform_noise(image)` | Uniform | — |
| `add_salt_and_pepper(image, salt, pepper)` | Impulse (S&P) | `salt`, `pepper`: corruption probabilities |

`generate_noise(distribution, ...)` is an internal helper that generates noise arrays from the specified distribution.

---

## Image Restoration

**File:** `Source/Advanced/restoration.py`

> Reference: *Gonzales & Woods, Chapter 5*

### `mean_filter(image, filter_type, filter_size, q)`
Applies a mean-based restoration filter over a sliding window.

| `filter_type` | Formula | Notes |
|---|---|---|
| `arithmetic` | mean of window | Reduces Gaussian noise |
| `geometric` | product^(1/n) of window | Less detail blurring |
| `harmonic` | n / sum(1/pixel) | Good for salt noise |
| `contra-harmonic` | sum(p^(Q+1)) / sum(p^Q) | `q>0`: pepper; `q<0`: salt |

### `order_statistic_filter(image, filter_type, filter_size, percentile)`
Applies an order-statistic (rank) filter.

| `filter_type` | Description |
|---|---|
| `median` | 50th percentile (removes S&P with less blur) |
| `max` | Maximum value in window |
| `min` | Minimum value in window |
| `midpoint` | (max + min) / 2 |
| `custom` | User-defined percentile |

---

## Morphology

**File:** `Source/Advanced/morphology.py`

> Reference: *Gonzales & Woods, Chapter 9*

All operations use a `structuring_element` (default `np.ones((3,3))`).

| Function | Description | Formula |
|---|---|---|
| `erosion(image, SE)` | Shrinks bright regions | A ⊖ B |
| `dilation(image, SE)` | Expands bright regions | A ⊕ B |
| `opening(image, SE)` | Erosion then dilation | A ∘ B = (A ⊖ B) ⊕ B |
| `closing(image, SE)` | Dilation then erosion | A • B = (A ⊕ B) ⊖ B |
| `boundary_extraction(image, SE)` | Edge = image - erosion | β(A) = A - (A ⊖ B) |

Supporting functions:
- `morphological_convolution()` — sliding window operation core
- `reflect_structuring_element()` — 180° rotation of SE
- `local_dilation()` / `local_erosion()` — per-pixel morphological primitives

---

## Thinning

**File:** `Source/Advanced/thinning.py`

> References: Zhang-Suen (1984), BST, GH1/GH2, DLH, PTA2T

Thinning reduces binary shapes to 1-pixel-wide skeletons while preserving topology.

### `parallel_sub_iteration_thinning(image, method)`
Parallel thinning using two alternating sub-iterations. Supported `method` values:

| Method | Description |
|---|---|
| `"ZS"` | Zhang-Suen (default) — widely-used, fast |
| `"BST"` | BST algorithm |
| `"GH1"` | Guo-Hall variant 1 |
| `"GH2"` | Guo-Hall variant 2 |
| `"DLH"` | DLH algorithm |

### `pta2t_thinning(image)`
Template-based thinning using a 256-entry condition lookup table and 11 deletion templates.

### Supporting Functions

| Function | Description |
|---|---|
| `measure_thinning_rate(before, after)` | `TR = 1 - TM1/TM2` — quantifies skeleton compactness |
| `pre_thinning(image)` | Applies `B_odd(P)` pre-processing step before thinning |

---

## MetaShell Sub-Module

**File:** `Source/Metashells/meta_shells.py`

A specialized sub-module for analyzing physical shell-shaped objects (e.g., biological or geological specimens). It processes doublet contours extracted from shell images and compares their shape using Fourier analysis and spatial metrics.

### Class: `MetaShell`

#### `doublet_processing(image, thinning_method, filter_size, global_threshold)`
Full preprocessing pipeline:
1. Threshold the image
2. Apply Gaussian blur
3. Thin the result
4. Return the skeleton contour

#### `spatial_conversion(skeleton)`
Converts the binary skeleton to spatial coordinate space (list of (x,y) points).

#### `spatial_comparison(contour_1, contour_2)`
Computes two distance metrics between two contours:
- **Hausdorff Distance** — worst-case point separation
- **Average Distance** — mean point separation

#### `dft_2d(contour)`
Manual computation of the 2D Discrete Fourier Transform of a contour (not using FFT library). Returns Fourier coefficient array.

#### `set_configuration_processing(thinning_method, filter_size, global_threshold)`
Runs processing with a fixed configuration for deterministic analysis.

#### `empirical_processing()`
Grid search over the parameter space:
- `thinning_method` × `filter_size` × `global_threshold`

Evaluates all combinations and returns the best configuration based on spatial comparison metrics.

---

## Demo (main.py)

The top-level `main.py` demonstrates a representative sequence of operations on `Lena.png`.

```python
# Load and convert to grayscale
image = Image(image_path=r"...\Lena.png")
image.convert_to_grayscale()

# Intensity transformations
image.negative()
image.gamma_correction(gamma=0.5)
image.gamma_correction(gamma=2)
image.bit_plane_reconstruction(degree_of_reduction=1)   # high quality
image.bit_plane_reconstruction(degree_of_reduction=4)   # medium quality
image.bit_plane_reconstruction(degree_of_reduction=7)   # low quality
image.bit_plane_slicing(bit_plane=1)
image.bit_plane_slicing(bit_plane=4)
image.bit_plane_slicing(bit_plane=7)

# Noise models
image.add_gaussian_noise(sigma=0.02)
image.add_rayleigh_noise()
image.add_erlang_noise()
image.add_exponential_noise()
image.add_uniform_noise()
image.add_salt_and_pepper(salt=0.01, pepper=0.01)

# Image restoration
image.add_salt_and_pepper(salt=0.01, pepper=0.01)
image.blur_image(filter_type="gaussian", filter_size=5)
image.mean_filter(filter_type="contra-harmonic", q=0)
```

The `reset_image()` helper used between operations resets the buffer to the original grayscale image before each new demonstration.