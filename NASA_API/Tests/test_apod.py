# Imports #
import pytest

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time

from NASA_API.Source.apod import APOD
from constants import *


# Shared mock data #
MOCK_IMAGE_PATH = "/tmp/APOD_test.JPG"
MOCK_APOD_RESPONSE = {
    "copyright": "NASA",
    "date": "2025-01-01",
    "explanation": "Test explanation.",
    "hdurl": "https://apod.nasa.gov/apod/image/test_hd.jpg",
    "media_type": "image",
    "service_version": "v1",
    "title": "Test APOD",
    "url": "https://apod.nasa.gov/apod/image/test.jpg",
}
MOCK_VIDEO_RESPONSE = {
    "date": "2025-01-01",
    "media_type": "video",
    "title": "Test Video APOD",
    "url": "https://www.youtube.com/embed/test",
}
MOCK_APOD_NO_HDURL = {
    "date": "2025-01-01",
    "media_type": "image",
    "title": "Test APOD (no HD)",
    "url": "https://apod.nasa.gov/apod/image/test.jpg",
}


# ──────────────────────────────────────────────────────────── #
#  Date validation tests                                        #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize(
    "input_date, result",
    [
        # Valid dates.
        ("2000-01-01", True),                                              # Correct format, within range.
        (date.today().strftime('%Y-%m-%d'), True),                         # Today's date (upper bound).
        # Invalid dates / formats.
        ("1900-01-01", False),                                             # Before the first APOD (Jun 16 1995).
        ("2000-02-30", False),                                             # Non-existent calendar date.
        ((date.today() + timedelta(days=1)).strftime('%Y-%m-%d'), False),  # Future date.
        ("INVALID_DATE", False),                                           # Wrong format entirely.
    ]
)
def test_validate_date(input_date, result):
    """
    Test purpose - Basic functionality of date validation.
    Criteria: Correct boolean returned for valid and invalid dates/formats.

    Test steps:
    1) Call APOD.validate_date() with the parametrized input.
    2) Assert the return value matches the expected result.
    """

    # Steps (1)+(2) - Validate and assert.
    assert APOD.validate_date(date=input_date) == result


# ──────────────────────────────────────────────────────────── #
#  astronomy_picture_of_the_day() unit tests                    #
# ──────────────────────────────────────────────────────────── #

def test_apod_invalid_date():
    """
    Test purpose - Correct error handling when an invalid date is provided at construction.
    Criteria: False is returned when astronomy_picture_of_the_day() is called with an invalid date.

    Test steps:
    1) Create an APOD instance with an invalid date string.
    2) Call astronomy_picture_of_the_day().
    3) Assert False is returned.
    """

    # Steps (1)+(2)+(3) - Create, call, assert.
    apod = APOD(date="INVALID_DATE")
    assert apod.astronomy_picture_of_the_day() is False


def test_apod_api_request_failure():
    """
    Test purpose - Correct error handling when the API request fails.
    Criteria: False is returned when get_request() returns None.

    Test steps:
    1) Create an APOD instance with a valid date.
    2) Mock get_request to return None (simulating a network error or bad status code).
    3) Call astronomy_picture_of_the_day().
    4) Assert False is returned.
    """

    apod = APOD(date="2025-01-01")

    with patch("NASA_API.Source.apod.get_request", return_value=None):
        # Steps (3)+(4) - Call and assert.
        assert apod.astronomy_picture_of_the_day() is False


def test_apod_video_response():
    """
    Test purpose - Correct handling of a video APOD entry.
    Criteria: False is returned (download skipped) when the API response indicates a video.

    Test steps:
    1) Create an APOD instance with a valid date.
    2) Mock get_request to return a video-type response.
    3) Call astronomy_picture_of_the_day().
    4) Assert False is returned and no download was attempted.
    """

    apod = APOD(date="2025-01-01")

    with patch("NASA_API.Source.apod.get_request", return_value=MOCK_VIDEO_RESPONSE), \
         patch("NASA_API.Source.apod.download_image_url") as mock_download:
        result = apod.astronomy_picture_of_the_day()

        # Steps (3)+(4) - Assert result and that download was never called.
        assert result is False
        mock_download.assert_not_called()


def test_apod_success_standard_resolution():
    """
    Test purpose - Successful download of a standard resolution APOD image.
    Criteria: True is returned and download_image_url is called with the standard URL.

    Test steps:
    1) Create an APOD instance with a valid date (hd=False).
    2) Mock get_request to return a valid image response.
    3) Mock download_image_url to return a dummy image path.
    4) Call astronomy_picture_of_the_day().
    5) Assert True is returned and the standard URL was used for the download.
    """

    apod = APOD(date="2025-01-01", hd=False)

    with patch("NASA_API.Source.apod.get_request", return_value=MOCK_APOD_RESPONSE), \
         patch("NASA_API.Source.apod.download_image_url", return_value=MOCK_IMAGE_PATH) as mock_download:
        result = apod.astronomy_picture_of_the_day()

        # Steps (4)+(5) - Assert result and correct URL usage.
        assert result is True
        mock_download.assert_called_once()
        call_kwargs = mock_download.call_args.kwargs
        assert call_kwargs["image_url_list"] == [MOCK_APOD_RESPONSE["url"]]


def test_apod_success_hd():
    """
    Test purpose - Successful download of an HD APOD image.
    Criteria: True is returned and download_image_url is called with the HD URL.

    Test steps:
    1) Create an APOD instance with a valid date (hd=True).
    2) Mock get_request to return a valid image response that includes an hdurl.
    3) Mock download_image_url to return a dummy image path.
    4) Call astronomy_picture_of_the_day().
    5) Assert True is returned and the HD URL was used for the download.
    """

    apod = APOD(date="2025-01-01", hd=True)

    with patch("NASA_API.Source.apod.get_request", return_value=MOCK_APOD_RESPONSE), \
         patch("NASA_API.Source.apod.download_image_url", return_value=MOCK_IMAGE_PATH) as mock_download:
        result = apod.astronomy_picture_of_the_day()

        # Steps (4)+(5) - Assert result and HD URL usage.
        assert result is True
        call_kwargs = mock_download.call_args.kwargs
        assert call_kwargs["image_url_list"] == [MOCK_APOD_RESPONSE["hdurl"]]


def test_apod_hd_fallback_to_standard():
    """
    Test purpose - HD fallback when the API response contains no hdurl.
    Criteria: True is returned and download_image_url falls back to the standard URL.

    Test steps:
    1) Create an APOD instance with hd=True.
    2) Mock get_request to return a response without an hdurl field.
    3) Mock download_image_url to return a dummy image path.
    4) Call astronomy_picture_of_the_day().
    5) Assert True is returned and the standard URL was used as the fallback.
    """

    apod = APOD(date="2025-01-01", hd=True)

    with patch("NASA_API.Source.apod.get_request", return_value=MOCK_APOD_NO_HDURL), \
         patch("NASA_API.Source.apod.download_image_url", return_value=MOCK_IMAGE_PATH) as mock_download:
        result = apod.astronomy_picture_of_the_day()

        # Steps (4)+(5) - Assert fallback to standard URL.
        assert result is True
        call_kwargs = mock_download.call_args.kwargs
        assert call_kwargs["image_url_list"] == [MOCK_APOD_NO_HDURL["url"]]


def test_apod_download_failure():
    """
    Test purpose - Correct error handling when the image download fails.
    Criteria: False is returned when download_image_url returns None.

    Test steps:
    1) Create an APOD instance with a valid date.
    2) Mock get_request to return a valid image response.
    3) Mock download_image_url to return None (simulating a download failure).
    4) Call astronomy_picture_of_the_day().
    5) Assert False is returned.
    """

    apod = APOD(date="2025-01-01")

    with patch("NASA_API.Source.apod.get_request", return_value=MOCK_APOD_RESPONSE), \
         patch("NASA_API.Source.apod.download_image_url", return_value=None):
        result = apod.astronomy_picture_of_the_day()

        # Steps (4)+(5) - Assert failure is propagated.
        assert result is False


# ──────────────────────────────────────────────────────────── #
#  Integration test (requires Chrome WebDriver)                 #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.integration
def test_apod_reference():
    """
    Test purpose - Validate that the APOD API returns the same image as the official website.
    Criteria: The image downloaded via the API is byte-for-byte identical to the one on apod.nasa.gov.

    Test steps:
    1) Open the APOD website using Selenium and retrieve the current image URL.
    2) Download the image directly from the resolved URL using requests.
    3) Download the same date's image using the APOD class.
    4) Compare both downloaded files byte-for-byte.
    """

    # Determine today's date for a deterministic comparison.
    today = date.today().strftime('%Y-%m-%d')
    save_dir = Path(r"C:\Users\micha\PycharmProjects\Data_Processing\NASA_API\Images")
    save_dir.mkdir(parents=True, exist_ok=True)

    # Step (1) - Open the APOD website and click the image to resolve the full-resolution URL.
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://apod.nasa.gov/apod/astropix.html")
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/center[1]/p[2]/a/img")))
    driver.execute_script("arguments[0].style.outline='3px solid red'", element)
    element.click()

    time.sleep(5)
    reference_url = driver.current_url
    driver.quit()

    # Step (2) - Download the reference image from the website URL.
    reference_path = save_dir / f"reference_{today}.jpg"
    with requests.get(reference_url, stream=True) as r:
        r.raise_for_status()
        with open(reference_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    # Step (3) - Download the same date's image using the APOD API class.
    apod = APOD(image_directory=str(save_dir), date=today, hd=True)
    assert apod.astronomy_picture_of_the_day() is True

    time.sleep(5)

    # Step (4) - Compare both files byte-for-byte.
    api_path = save_dir / f"APOD_{today}.JPG"
    with open(reference_path, "rb") as f1, open(api_path, "rb") as f2:
        assert f1.read() == f2.read()