# NASA API Module

A Python client for querying multiple NASA public APIs: the Astronomy Picture of the Day (APOD), Earth Polychromatic Imaging Camera (EPIC), Mars Rover Photos, and the NASA Image and Video Library (NIL). Images are downloaded via the `requests` library with automatic retry logic.

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
- HTTP GET requests via the `requests` library (with timeout and exception handling)
- Streaming image downloads with up to `MAX_RETRIES` attempts and `RETRY_DELAY` seconds between each
- Custom log levels per API source
- `@property` patterns throughout for safe, validated state management

---

## Project Structure

```
NASA_API/
├── Images/                     # Downloaded images
├── References/                 # Related articles and papers
├── Settings/
│   └── api_settings.py         # API key, URLs, retry config, log levels, rover date ranges
├── Source/
│   ├── api_utilities.py        # Shared HTTP and download helpers
│   ├── apod.py                 # APOD class
│   ├── epic.py                 # EPIC class
│   ├── mars.py                 # MARS class
│   └── nil.py                  # NIL class
├── Tests/
│   ├── constants.py            # Shared test configuration (suppresses log output)
│   ├── test_apod.py            # APOD unit + integration tests
│   ├── test_epic.py            # EPIC unit tests
│   ├── test_mars.py            # MARS unit tests
│   └── test_nil.py             # NIL unit tests
└── main.py                     # Demo script
```

---

## Settings

**File:** `Settings/api_settings.py`

| Constant | Default | Description |
|---|---|---|
| `API_KEY` | env `NASA_API_KEY` | NASA API key (reads from environment variable with a built-in fallback) |
| `MAX_RETRIES` | `3` | Maximum download attempts per image URL |
| `RETRY_DELAY` | `5` | Seconds between download retries |
| `REQUEST_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `DEFAULT_IMAGE_DIRECTORY` | `NASA_API/Images/` | Default save directory (resolved relative to the settings file) |
| `APOD_FIRST_DATE` | `"1995-06-16"` | Date of the first APOD entry (lower bound for date validation) |
| `MARS_ROVER_DATE_RANGES` | dict | Per-rover mission date ranges (see MARS section) |
| `NIL_FIRST_YEAR` | `1960` | Earliest valid start year for NIL queries |

**Custom log levels** (registered per API):

| Level Name | Level Number | Color |
|---|---|---|
| `apod` | 11 | Orange |
| `epic` | 12 | Magenta |
| `mars` | 13 | Red |
| `nil` | 14 | Blue |

**API key via environment variable:**

```bash
export NASA_API_KEY="your_key_here"
```

---

## Utility Functions

**File:** `Source/api_utilities.py`

### `get_request(url)`
Performs an HTTP GET request using `requests.get` with a `REQUEST_TIMEOUT` second timeout.

- Handles `Timeout`, `ConnectionError`, and general `RequestException` separately
- Returns the response JSON as a dict on HTTP 200, or `None` on any failure

### `download_image_url(image_directory, api_type, image_url_list, image_suffix="")`
Downloads images from a list of URLs using streaming `requests.get` calls.

- **Retry logic**: up to `MAX_RETRIES` attempts with `RETRY_DELAY` seconds between each
- **Single image filename**: `{api_type}{image_suffix}.{format}` (e.g., `APOD_2025-01-01.JPG`)
- **Multiple image filenames**: `{api_type}{image_suffix}_{index}.{format}` (e.g., `MARS_Curiosity_2015-04-27_1.JPG`)
- Creates the target directory automatically if it does not exist
- Returns the path to the last successfully downloaded file, or `None` if all attempts fail

### `display_image(image_path)`
Opens and displays a downloaded image using the system's default viewer (PIL `Image.show()`). Checks both that a path was provided and that the file exists before opening.

---

## APOD — Astronomy Picture of the Day

**File:** `Source/apod.py`

### Class: `APOD`

#### Constructor

```python
apod = APOD(image_directory="NASA_API/Images")
```

#### Properties

| Property | Type | Description |
|---|---|---|
| `date` | `str` | Query date in `YYYY-MM-DD` format. Validated on assignment. |
| `hd` | `bool` | If `True`, requests the HD image URL. Falls back to standard if HD is unavailable. |
| `apod_image` | `str` | Path to the most recently downloaded image. |

#### `validate_date(date)` — `@staticmethod`
Validates a date string against three rules:
1. Matches `YYYY-MM-DD` format (regex)
2. Represents a real calendar date (no Feb 30)
3. Falls within the APOD archive range: **June 16, 1995** to **today**

#### `astronomy_picture_of_the_day()`
Downloads the APOD image for the configured date.

- Returns `False` if no date is set, the API request fails, or the entry is a **video** (gracefully skipped)
- If `hd=True` but no `hdurl` is present in the response, automatically falls back to the standard URL
- Returns `True` on successful download, `False` if the download fails

**Example:**
```python
apod = APOD(image_directory="NASA_API/Images")
apod.date = "2025-04-15"
apod.hd = True
apod.astronomy_picture_of_the_day()
```

---

## EPIC — Earth Polychromatic Imaging Camera

**File:** `Source/epic.py`

### Class: `EPIC`

#### Constructor

```python
epic = EPIC(image_directory="NASA_API/Images")
```

#### `earth_polychromatic_imaging_camera(date=None)`
Downloads a full-disk Earth image from the DSCOVR satellite.

| Parameter | Default | Description |
|---|---|---|
| `date` | `None` | Optional `YYYY-MM-DD` date. If `None`, the most recent available image is retrieved. |

- Returns `False` if the API request fails or the response contains no images
- Returns `True` on successful download

**Example:**
```python
# Latest image
epic.earth_polychromatic_imaging_camera()

# Specific date
epic.earth_polychromatic_imaging_camera(date="2025-01-15")
```

#### `reformat_images_url(image_date)` — `@staticmethod`
Parses an EPIC API date-time string (`'YYYY-MM-DD HH:MM:SS'`) into `(year, month, day)` for building archive URLs.

---

## MARS — Mars Rover Photos

**File:** `Source/mars.py`

### Class: `MARS`

#### Constructor

```python
mars = MARS(image_directory="NASA_API/Images")
```

#### Supported Rovers and Mission Ranges

| Rover | Mission Start | Mission End |
|---|---|---|
| Curiosity | 2012-08-06 | today (ongoing) |
| Opportunity | 2004-01-25 | 2018-06-11 |
| Spirit | 2004-01-04 | 2010-03-21 |

Date ranges are centralized in `MARS_ROVER_DATE_RANGES` in `api_settings.py`.

#### Properties

| Property | Description |
|---|---|
| `rover` | Rover name. Validated against `MARS_ROVERS` on assignment. |
| `date` | Earth date for the photo query. Validated against the rover's mission range. **Rover must be set first.** |
| `mars_image` | Path to the most recently downloaded image. |

#### `validate_date(date, rover)` — `@staticmethod`
Validates a date string against:
1. `YYYY-MM-DD` format
2. Real calendar date
3. The selected rover's mission date range

#### `mars(max_photos=1)`
Downloads Mars rover photo(s) for the configured rover and date.

| Parameter | Default | Description |
|---|---|---|
| `max_photos` | `1` | Maximum photos to download. Pass `-1` to download all available photos. |

- Returns `False` if rover/date not set, API fails, or no photos exist for that date
- Returns `True` if at least one photo was downloaded successfully

**Example:**
```python
mars = MARS(image_directory="NASA_API/Images")
mars.rover = "Curiosity"
mars.date = "2015-04-27"
mars.mars()          # Download 1 photo (default)
mars.mars(max_photos=-1)  # Download all photos for this date
```

#### `mars_rover_manifest()`
Retrieves the mission manifest (landing date, last active date, total photos, status).
Returns a dict, or `None` if no rover is set or the request fails.

---

## NIL — NASA Image and Video Library

**File:** `Source/nil.py`

### Class: `NIL`

#### Constructor

```python
nil = NIL(image_directory="NASA_API/Images")
```

#### Properties

| Property | Type | Description |
|---|---|---|
| `query` | `str` | Search query. Spaces are automatically URL-encoded (`' '` → `'%20'`). |
| `media_type` | `str` | Media type filter. Validated against `NIL_MEDIA_TYPES` (`'image'` or `'audio'`). |
| `search_years` | `list/tuple` | Optional `[start_year, end_year]` range. Validated on assignment. |
| `nil_image` | `str` | Path to the most recently downloaded image. |

#### `validate_year_range(year_range)` — `@staticmethod`
Validates a year range as `[int, int]` where `1960 ≤ start ≤ end ≤ current_year`.

#### `nasa_image_library_query()`
Queries the NASA Image Library and downloads the first matching result.

- **`query` and `media_type` are required** before calling this method
- `search_years` is **optional** — omitting it searches the entire archive
- Returns `False` if required fields are missing, the API fails, or no results are found
- Returns `True` on successful download

**Example:**
```python
nil = NIL(image_directory="NASA_API/Images")
nil.query = "Crab nebula"
nil.media_type = "image"
nil.search_years = [2000, 2020]   # Optional
nil.nasa_image_library_query()
```

---

## Tests

**File:** `Tests/test_apod.py`, `Tests/test_epic.py`, `Tests/test_mars.py`, `Tests/test_nil.py`

All unit tests use `unittest.mock.patch` to mock network calls (`get_request`, `download_image_url`), making the test suite fully offline and deterministic. Log output is suppressed during tests via `Tests/constants.py`.

Run all tests:
```bash
pytest NASA_API/Tests/
```

Run only unit tests (excluding Selenium integration test):
```bash
pytest NASA_API/Tests/ -m "not integration"
```

### APOD Tests (`test_apod.py`)

| Test | Description |
|---|---|
| `test_validate_date` (×6) | Parametrized: valid dates, too old, non-existent, future, wrong format |
| `test_apod_no_date_set` | `False` returned when date is not configured |
| `test_apod_api_request_failure` | `False` returned when `get_request` returns `None` |
| `test_apod_video_response` | `False` returned and download skipped for video entries |
| `test_apod_success_standard_resolution` | `True` returned; standard URL passed to download |
| `test_apod_success_hd` | `True` returned; HD URL passed to download |
| `test_apod_hd_fallback_to_standard` | `True` returned; falls back to standard URL when `hdurl` absent |
| `test_apod_download_failure` | `False` returned when download fails |
| `test_apod_reference` *(integration)* | Selenium + `requests` vs API byte-for-byte comparison |

### EPIC Tests (`test_epic.py`)

| Test | Description |
|---|---|
| `test_reformat_images_url` (×3) | Parametrized: correct year/month/day extraction |
| `test_epic_api_request_failure` | `False` returned on API failure |
| `test_epic_empty_response` | `False` returned when API returns no images |
| `test_epic_success_latest` | `True` returned; correct archive URL constructed |
| `test_epic_success_specific_date` | `True` returned; date-specific URL used |
| `test_epic_download_failure` | `False` returned when download fails |

### MARS Tests (`test_mars.py`)

| Test | Description |
|---|---|
| `test_validate_date` (×16) | Parametrized across all three rovers: valid dates, out-of-range, invalid format |
| `test_rover_setter_valid` (×3) | All valid rover names accepted |
| `test_rover_setter_invalid` | Unknown rover rejected; property stays `None` |
| `test_date_setter_without_rover` | Date not set when no rover is configured |
| `test_mars_no_rover_set` | `False` returned from `mars()` |
| `test_mars_no_date_set` | `False` returned from `mars()` |
| `test_mars_api_request_failure` | `False` returned on API failure |
| `test_mars_no_photos_available` | `False` returned for empty photo list |
| `test_mars_success_single_photo` | `True` returned; one URL passed to download |
| `test_mars_success_multiple_photos` | `True` returned; all URLs passed when `max_photos=-1` |
| `test_mars_download_failure` | `False` returned when download fails |
| `test_mars_rover_manifest_no_rover` | `None` returned when no rover set |
| `test_mars_rover_manifest_success` | Correct manifest dict returned |

### NIL Tests (`test_nil.py`)

| Test | Description |
|---|---|
| `test_validate_year_range` (×10) | Parametrized: valid ranges, wrong types, out-of-bounds |
| `test_media_type_setter_valid` (×2) | Both `'image'` and `'audio'` accepted |
| `test_media_type_setter_invalid` | Invalid type rejected; property stays `None` |
| `test_query_setter_encodes_spaces` | Spaces replaced with `%20` |
| `test_nil_no_query_set` | `False` returned when query missing |
| `test_nil_no_media_type_set` | `False` returned when media type missing |
| `test_nil_api_request_failure` | `False` returned on API failure |
| `test_nil_no_results` | `False` returned for empty results collection |
| `test_nil_success` | `True` returned; correct URL passed to download |
| `test_nil_success_without_year_range` | `True` returned; no year params in request URL |
| `test_nil_download_failure` | `False` returned when download fails |

---

## Demo (main.py)

```python
from NASA_API.Source.apod import APOD
from NASA_API.Source.epic import EPIC
from NASA_API.Source.mars import MARS
from NASA_API.Source.nil import NIL

# APOD - April 27, 1999
apod = APOD()
apod.date = "1999-04-27"
apod.astronomy_picture_of_the_day()

# EPIC - most recent available
epic = EPIC()
epic.earth_polychromatic_imaging_camera()

# MARS - Curiosity rover, April 27, 2015
mars = MARS()
mars.rover = "Curiosity"
mars.date = "2015-04-27"
mars.mars()

# NIL - "Crab nebula" images from 2000–2020
nil = NIL()
nil.query = "Crab nebula"
nil.search_years = [2000, 2020]
nil.media_type = "image"
nil.nasa_image_library_query()
```