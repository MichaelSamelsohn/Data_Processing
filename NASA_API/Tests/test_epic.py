# Imports #
import pytest

from unittest.mock import patch
from NASA_API.Source.epic import EPIC
from constants import *


# Shared mock data #
MOCK_IMAGE_PATH = "/tmp/EPIC_test.png"
MOCK_EPIC_RESPONSE = [
    {
        "image": "epic_1b_20250115120000",
        "date": "2025-01-15 12:00:00",
        "caption": "Test EPIC image",
        "centroid_coordinates": {"lat": 0.0, "lon": 0.0},
    }
]


# ──────────────────────────────────────────────────────────── #
#  reformat_images_url() unit tests                             #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize(
    "image_date, expected_year, expected_month, expected_day",
    [
        ("2025-01-15 12:00:00", "2025", "01", "15"),   # Standard date-time string.
        ("2000-06-30 00:00:00", "2000", "06", "30"),   # Year 2000, end of June.
        ("2024-12-01 23:59:59", "2024", "12", "01"),   # End of year, first day of month.
    ]
)
def test_reformat_images_url(image_date, expected_year, expected_month, expected_day):
    """
    Test purpose - Correct parsing of EPIC API date-time strings.
    Criteria: Year, month, and day components are correctly extracted from the API date string.

    Test steps:
    1) Call EPIC.reformat_images_url() with the parametrized date string.
    2) Assert the returned (year, month, day) tuple matches the expected values.
    """

    # Steps (1)+(2) - Call and assert.
    year, month, day = EPIC.reformat_images_url(image_date=image_date)
    assert year == expected_year
    assert month == expected_month
    assert day == expected_day


# ──────────────────────────────────────────────────────────── #
#  earth_polychromatic_imaging_camera() unit tests              #
# ──────────────────────────────────────────────────────────── #

def test_epic_api_request_failure():
    """
    Test purpose - Correct error handling when the API request fails.
    Criteria: False is returned when get_request() returns None.

    Test steps:
    1) Create an EPIC instance.
    2) Mock get_request to return None.
    3) Call earth_polychromatic_imaging_camera().
    4) Assert False is returned.
    """

    epic = EPIC()

    with patch("NASA_API.Source.epic.get_request", return_value=None):
        # Steps (3)+(4) - Call and assert.
        assert epic.earth_polychromatic_imaging_camera() is False


def test_epic_empty_response():
    """
    Test purpose - Correct error handling when the API returns no images.
    Criteria: False is returned when the API response is an empty list.

    Test steps:
    1) Create an EPIC instance.
    2) Mock get_request to return an empty list.
    3) Call earth_polychromatic_imaging_camera().
    4) Assert False is returned.
    """

    epic = EPIC()

    with patch("NASA_API.Source.epic.get_request", return_value=[]):
        # Steps (3)+(4) - Call and assert.
        assert epic.earth_polychromatic_imaging_camera() is False


def test_epic_success_latest():
    """
    Test purpose - Successful download of the most recent EPIC image (no date specified).
    Criteria: True is returned and download_image_url is called with the correctly built archive URL.

    Test steps:
    1) Create an EPIC instance.
    2) Mock get_request and download_image_url.
    3) Call earth_polychromatic_imaging_camera() without a date argument.
    4) Assert True is returned.
    5) Assert the download URL references the correct date path and image name.
    """

    epic = EPIC()

    with patch("NASA_API.Source.epic.get_request", return_value=MOCK_EPIC_RESPONSE), \
         patch("NASA_API.Source.epic.download_image_url", return_value=MOCK_IMAGE_PATH) as mock_download:
        result = epic.earth_polychromatic_imaging_camera()

        # Steps (4)+(5) - Assert result and URL construction.
        assert result is True
        mock_download.assert_called_once()
        call_kwargs = mock_download.call_args.kwargs
        expected_url = (
            "https://epic.gsfc.nasa.gov/archive/natural/2025/01/15/png/epic_1b_20250115120000.png"
        )
        assert call_kwargs["image_url_list"] == [expected_url]


def test_epic_success_specific_date():
    """
    Test purpose - Successful download of an EPIC image for a specified date.
    Criteria: True is returned and get_request is called with the date-specific URL.

    Test steps:
    1) Create an EPIC instance.
    2) Mock get_request and download_image_url.
    3) Call earth_polychromatic_imaging_camera(date="2025-01-15").
    4) Assert True is returned.
    5) Assert get_request was called with a URL containing the specified date.
    """

    epic = EPIC()

    with patch("NASA_API.Source.epic.get_request", return_value=MOCK_EPIC_RESPONSE) as mock_get, \
         patch("NASA_API.Source.epic.download_image_url", return_value=MOCK_IMAGE_PATH):
        result = epic.earth_polychromatic_imaging_camera(date="2025-01-15")

        # Steps (4)+(5) - Assert result and URL format.
        assert result is True
        call_args = mock_get.call_args
        assert "2025-01-15" in call_args.kwargs["url"]


def test_epic_download_failure():
    """
    Test purpose - Correct error handling when the image download fails.
    Criteria: False is returned when download_image_url returns None.

    Test steps:
    1) Create an EPIC instance.
    2) Mock get_request to return a valid response.
    3) Mock download_image_url to return None.
    4) Call earth_polychromatic_imaging_camera().
    5) Assert False is returned.
    """

    epic = EPIC()

    with patch("NASA_API.Source.epic.get_request", return_value=MOCK_EPIC_RESPONSE), \
         patch("NASA_API.Source.epic.download_image_url", return_value=None):
        # Steps (4)+(5) - Call and assert.
        assert epic.earth_polychromatic_imaging_camera() is False