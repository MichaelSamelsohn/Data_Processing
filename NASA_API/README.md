# NASA API Module

A Python client for querying multiple NASA public APIs: the Astronomy Picture of the Day (APOD), Earth Polychromatic Imaging Camera (EPIC), Mars Rover Photos, and the NASA Image and Video Library (NIL). Images are downloaded via `curl` subprocess calls with retry logic.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Settings](#settings)
- [Utility Functions](#utility-functions)
- [APOD — Astronomy Picture of the Day](#apod--astronomy-picture-of-the-day)
- [EPIC — Earth Polychromatic Imaging Camera](#epic--earth-polychromatic-imaging-camera)
- [MARS — Mars Rover Photos](#mars--mars-rover-photos)
- [NIL — NASA Image and Video Library](#nil--nasa-image-and-video-library)
- [Tests](#tests)
- [Demo (main.py)](#demo-mainpy)

---

## Overview

Each NASA data source is encapsulated in its own class (`APOD`, `EPIC`, `MARS`, `NIL`) with:
- Input validation via property setters
- HTTP GET requests via the `requests` library
- Image downloading via `curl` subprocess with up to 3 retries
- Custom log levels per API source

---

## Project Structure

```
NASA_API/
├── Images/                     # Downloaded images
├── References/                 # Related articles/papers
├── Settings/
│   └── api_settings.py         # API keys, URLs, retry config, log levels
├── Source/
│   ├── api_utilities.py        # Shared HTTP and download helpers
│   ├── apod.py                 # APOD class
│   ├── epic.py                 # EPIC class
│   ├── mars.py                 # MARS class
│   └── nil.py                  # NIL class
├── Tests/
│   └── test_apod.py            # pytest tests for APOD
└── main.py                     # Demo script
```

---

## Settings

**File:** `Settings/api_settings.py`

| Constant | Value | Description |
|---|---|---|
| `API_KEY` | `"..."` | NASA API key |
| `MAX_RETRIES` | `3` | Maximum download attempts |
| `RETRY_DELAY` | `5` | Seconds between retries |
| `APOD_URL_PREFIX` | `"..."` | Base URL for APOD endpoint |
| `EPIC_URL_PREFIX` | `"..."` | Base URL for EPIC endpoint |
| `MARS_URL_PREFIX` | `"..."` | Base URL for Mars Rover endpoint |
| `NIL_URL_PREFIX` | `"..."` | Base URL for NIL endpoint |

**Custom log levels** (registered per API):

| Level Name | Level Number |
|---|---|
| `apod` | 11 |
| `epic` | 12 |
| `mars` | 13 |
| `nil` | 14 |

---

## Utility Functions

**File:** `Source/api_utilities.py`

### `get_request(url, params)`
Performs an HTTP GET request using the `requests` library and verifies the HTTP status code.

Returns the response object on success, or `False` on failure.

### `download_image_url(url, image_directory, api_type, suffix, image_format)`
Downloads an image from a URL using a `curl` subprocess call.

- **Retry logic**: up to `MAX_RETRIES` (3) attempts with `RETRY_DELAY` (5s) between each
- **Output filename**: `{api_type}{suffix}.{image_format}` (e.g., `APOD_2025-01-01.JPG`)
- Saves the file to `image_directory`

### `display_image(image_path)`
Opens and displays a downloaded image using PIL (`Image.open().show()`).

---

## APOD — Astronomy Picture of the Day

**File:** `Source/apod.py`

### Class: `APOD`

#### Constructor

```python
apod = APOD(image_directory="path/to/save")
```

#### Properties

| Property | Type | Description |
|---|---|---|
| `date` | `str` | Date of the picture (`YYYY-MM-DD`). Validated on set. |
| `hd` | `bool` | If `True`, requests the HD version of the image. |

#### `validate_date(date)` — `@staticmethod`
Validates that a date string is:
1. In `YYYY-MM-DD` format (regex check)
2. A real calendar date (no Feb 30, etc.)
3. Within the valid APOD range: **June 16, 1995** to **today**

Returns `True` if valid, `False` otherwise.

#### `astronomy_picture_of_the_day()`
Requests the APOD for the configured `date`.

- Returns `False` if no date is set
- Sends GET request to the APOD API endpoint
- Downloads the image using `download_image_url()`
- Returns the API response JSON on success

**Example:**
```python
apod = APOD(image_directory=r"NASA_API/Images")
apod.date = "2025-04-15"
apod.hd = True
apod.astronomy_picture_of_the_day()
```

---

## EPIC — Earth Polychromatic Imaging Camera

**File:** `Source/epic.py`

### Class: `EPIC`

Retrieves full-disk Earth images from the DSCOVR satellite.

#### `earth_polychromatic_imaging_camera()`
Queries the EPIC API for the latest available images and downloads them.

#### `reformat_images_url(response)` — `@staticmethod`
Reformats the raw API image URLs into the correct downloadable format. The EPIC API returns metadata with image names that must be reconstructed into full URLs using the date embedded in the response.

---

## MARS — Mars Rover Photos

**File:** `Source/mars.py`

### Class: `MARS`

Retrieves photos taken by NASA Mars rovers. Supports three rovers with known operational date ranges.

#### Valid Rover Date Ranges

| Rover | Start Date | End Date |
|---|---|---|
| Opportunity | 2004-01-25 | 2018-06-11 |
| Spirit | 2004-01-04 | 2010-03-21 |
| Curiosity | 2012-08-06 | today |

#### Properties

| Property | Description |
|---|---|
| `rover` | Selected rover name (`"opportunity"`, `"spirit"`, `"curiosity"`) |
| `date` | Earth date for photo query. Validated against rover's operational range. |

#### `mars()`
Queries the Mars Rover Photos API for the selected rover and date, then downloads all available images.

#### `mars_rover_manifest()`
Retrieves the mission manifest for the selected rover (total photos, mission status, date range, etc.).

**Example:**
```python
mars = MARS(image_directory=r"NASA_API/Images")
mars.rover = "curiosity"
mars.date = "2015-04-27"
mars.mars()
```

---

## NIL — NASA Image and Video Library

**File:** `Source/nil.py`

### Class: `NIL`

Queries the NASA Image and Video Library for images matching a text search.

#### Properties

| Property | Type | Description |
|---|---|---|
| `query` | `str` | Search term (spaces are URL-encoded automatically) |
| `year_start` | `int` | Start year of search range |
| `year_end` | `int` | End year of search range |

#### `validate_year_range(start, end)` — internal
Validates that:
- `1960 ≤ start ≤ end ≤ current_year`

#### `nasa_image_library_query()`
Sends the search request to the NIL API with the configured query and year range, then downloads the first matching image result.

**Example:**
```python
nil = NIL(image_directory=r"NASA_API/Images")
nil.query = "Crab nebula"
nil.year_start = 2000
nil.year_end = 2020
nil.nasa_image_library_query()
```

---

## Tests

**File:** `Tests/test_apod.py`

Uses `pytest` with `selenium`, `requests`, and standard library components.

### `test_validate_date` — Parametrized

Tests the `APOD.validate_date()` static method with 6 cases:

| Input | Expected | Reason |
|---|---|---|
| `"2000-01-01"` | `True` | Valid date within range |
| Today's date | `True` | Edge case: today is valid |
| `"1900-01-01"` | `False` | Too old (before June 1995) |
| `"2000-02-30"` | `False` | Non-existent calendar date |
| Tomorrow's date | `False` | Future dates are invalid |
| `"INVALID_DATE"` | `False` | Wrong format |

### `test_apod_no_date_set`

Verifies that calling `astronomy_picture_of_the_day()` without setting a date returns `False`.

```python
apod = APOD()
assert apod.astronomy_picture_of_the_day() == False
```

### `test_apod_reference`

End-to-end integration test using **Selenium WebDriver**:

1. Opens the official APOD website (`apod.nasa.gov`)
2. Clicks the APOD image to get its direct URL
3. Downloads the image via `requests` to a local file
4. Downloads the same date's image using the `APOD` class API
5. Compares the two files byte-by-byte using `f1.read() == f2.read()`

---

## Demo (main.py)

```python
# APOD - April 27, 1999
apod = APOD(image_directory=r"NASA_API/Images")
apod.date = "1999-04-27"
apod.astronomy_picture_of_the_day()

# EPIC - latest available
epic = EPIC(image_directory=r"NASA_API/Images")
epic.earth_polychromatic_imaging_camera()

# MARS - Curiosity rover, April 27, 2015
mars = MARS(image_directory=r"NASA_API/Images")
mars.rover = "curiosity"
mars.date = "2015-04-27"
mars.mars()

# NIL - "Crab nebula" images from 2000–2020
nil = NIL(image_directory=r"NASA_API/Images")
nil.query = "Crab nebula"
nil.year_start = 2000
nil.year_end = 2020
nil.nasa_image_library_query()
```