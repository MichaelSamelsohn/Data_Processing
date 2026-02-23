# Imports #
import pytest

from datetime import date, timedelta
from unittest.mock import patch
from NASA_API.Source.mars import MARS
from constants import *


# Shared mock data #
MOCK_IMAGE_PATH = "/tmp/MARS_test.JPG"
MOCK_MARS_RESPONSE = {
    "photos": [
        {
            "id": 1,
            "sol": 1000,
            "camera": {"name": "MAST"},
            "img_src": "https://mars.nasa.gov/photo1.jpg",
            "earth_date": "2015-04-27",
            "rover": {"name": "Curiosity"},
        },
        {
            "id": 2,
            "sol": 1000,
            "camera": {"name": "NAVCAM"},
            "img_src": "https://mars.nasa.gov/photo2.jpg",
            "earth_date": "2015-04-27",
            "rover": {"name": "Curiosity"},
        },
    ]
}
MOCK_MANIFEST_RESPONSE = {
    "photo_manifest": {
        "name": "Curiosity",
        "landing_date": "2012-08-06",
        "max_date": "2025-01-01",
        "max_sol": 4500,
        "status": "active",
        "total_photos": 700000,
    }
}


# ──────────────────────────────────────────────────────────── #
#  Date validation tests                                        #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize(
    "rover, input_date, result",
    [
        # Curiosity (ongoing mission: 2012-08-06 to today).
        ("Curiosity", "2015-04-27", True),                                             # Valid mid-mission date.
        ("Curiosity", "2012-08-06", True),                                             # Landing date (lower bound).
        ("Curiosity", date.today().strftime('%Y-%m-%d'), True),                        # Today (upper bound).
        ("Curiosity", "2012-08-05", False),                                            # Day before landing.
        ("Curiosity", (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'), False), # Future date.
        # Opportunity (ended: 2004-01-25 to 2018-06-11).
        ("Opportunity", "2010-06-15", True),                                           # Valid mid-mission date.
        ("Opportunity", "2004-01-25", True),                                           # Landing date (lower bound).
        ("Opportunity", "2018-06-11", True),                                           # Last contact (upper bound).
        ("Opportunity", "2018-06-12", False),                                          # Day after last contact.
        ("Opportunity", "2003-12-31", False),                                          # Before landing.
        # Spirit (ended: 2004-01-04 to 2010-03-21).
        ("Spirit", "2007-07-04", True),                                                # Valid mid-mission date.
        ("Spirit", "2004-01-04", True),                                                # Landing date (lower bound).
        ("Spirit", "2010-03-21", True),                                                # Last contact (upper bound).
        ("Spirit", "2010-03-22", False),                                               # Day after last contact.
        # Format errors.
        ("Curiosity", "INVALID", False),                                               # Wrong format.
        ("Curiosity", "2015-02-30", False),                                            # Non-existent date.
    ]
)
def test_validate_date(rover, input_date, result):
    """
    Test purpose - Date validation against rover mission ranges.
    Criteria: Correct boolean returned for valid and invalid dates across all three rovers.

    Test steps:
    1) Call MARS.validate_date() with the parametrized rover and date.
    2) Assert the return value matches the expected result.
    """

    # Steps (1)+(2) - Validate and assert.
    assert MARS.validate_date(date=input_date, rover=rover) == result


# ──────────────────────────────────────────────────────────── #
#  Rover property tests                                         #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize("rover_name", ["Curiosity", "Opportunity", "Spirit"])
def test_rover_setter_valid(rover_name):
    """
    Test purpose - Successful rover assignment with a valid name.
    Criteria: The rover property is set to the provided name.

    Test steps:
    1) Create a MARS instance.
    2) Set the rover to a valid name.
    3) Assert the rover property equals the provided name.
    """

    mars = MARS()
    mars.rover = rover_name

    # Step (3) - Assert rover was set.
    assert mars.rover == rover_name


def test_rover_setter_invalid():
    """
    Test purpose - Rejection of an invalid rover name.
    Criteria: The rover property remains None when an unsupported name is provided.

    Test steps:
    1) Create a MARS instance.
    2) Set the rover to an invalid name.
    3) Assert the rover property remains None.
    """

    mars = MARS()
    mars.rover = "Perseverance"  # Valid rover, but not supported by this API wrapper.

    # Step (3) - Assert rover was not set.
    assert mars.rover is None


def test_date_setter_without_rover():
    """
    Test purpose - Correct error handling when setting a date before a rover is selected.
    Criteria: The date property remains None when set before a rover is configured.

    Test steps:
    1) Create a MARS instance (no rover set).
    2) Attempt to set a date.
    3) Assert the date property remains None.
    """

    mars = MARS()
    mars.date = "2015-04-27"

    # Step (3) - Assert date was not set due to missing rover.
    assert mars.date is None


# ──────────────────────────────────────────────────────────── #
#  mars() unit tests                                            #
# ──────────────────────────────────────────────────────────── #

def test_mars_no_rover_set():
    """
    Test purpose - Correct error handling when mars() is called without a rover.
    Criteria: False is returned when no rover has been configured.

    Test steps:
    1) Create a MARS instance without setting a rover.
    2) Call mars().
    3) Assert False is returned.
    """

    mars = MARS()
    assert mars.mars() is False


def test_mars_no_date_set():
    """
    Test purpose - Correct error handling when mars() is called without a date.
    Criteria: False is returned when no date has been configured.

    Test steps:
    1) Create a MARS instance with a rover but no date.
    2) Call mars().
    3) Assert False is returned.
    """

    mars = MARS()
    mars._rover = "Curiosity"  # Bypass setter to inject rover without triggering date validation.
    assert mars.mars() is False


def test_mars_api_request_failure():
    """
    Test purpose - Correct error handling when the API request fails.
    Criteria: False is returned when get_request() returns None.

    Test steps:
    1) Create a MARS instance with rover and date set.
    2) Mock get_request to return None.
    3) Call mars().
    4) Assert False is returned.
    """

    mars = MARS()
    mars._rover = "Curiosity"
    mars._date = "2015-04-27"

    with patch("NASA_API.Source.mars.get_request", return_value=None):
        # Steps (3)+(4) - Call and assert.
        assert mars.mars() is False


def test_mars_no_photos_available():
    """
    Test purpose - Correct handling of an API response with no available photos.
    Criteria: False is returned when the photos list is empty.

    Test steps:
    1) Create a MARS instance with rover and date set.
    2) Mock get_request to return a response with an empty photos list.
    3) Call mars().
    4) Assert False is returned.
    """

    mars = MARS()
    mars._rover = "Curiosity"
    mars._date = "2015-04-27"

    with patch("NASA_API.Source.mars.get_request", return_value={"photos": []}):
        # Steps (3)+(4) - Call and assert.
        assert mars.mars() is False


def test_mars_success_single_photo():
    """
    Test purpose - Successful download of a single Mars rover photo (default behaviour).
    Criteria: True is returned and download_image_url is called with one URL.

    Test steps:
    1) Create a MARS instance with rover and date set.
    2) Mock get_request and download_image_url.
    3) Call mars() with the default max_photos=1.
    4) Assert True is returned.
    5) Assert download_image_url was called with exactly one URL.
    """

    mars = MARS()
    mars._rover = "Curiosity"
    mars._date = "2015-04-27"

    with patch("NASA_API.Source.mars.get_request", return_value=MOCK_MARS_RESPONSE), \
         patch("NASA_API.Source.mars.download_image_url", return_value=MOCK_IMAGE_PATH) as mock_download:
        result = mars.mars(max_photos=1)

        # Steps (4)+(5) - Assert result and single-URL download.
        assert result is True
        call_kwargs = mock_download.call_args.kwargs
        assert len(call_kwargs["image_url_list"]) == 1
        assert call_kwargs["image_url_list"][0] == MOCK_MARS_RESPONSE["photos"][0]["img_src"]


def test_mars_success_multiple_photos():
    """
    Test purpose - Successful download of multiple Mars rover photos.
    Criteria: True is returned and download_image_url is called with all available URLs.

    Test steps:
    1) Create a MARS instance with rover and date set.
    2) Mock get_request to return a response with two photos.
    3) Mock download_image_url.
    4) Call mars(max_photos=-1) to download all available photos.
    5) Assert True is returned.
    6) Assert download_image_url was called with both URLs.
    """

    mars = MARS()
    mars._rover = "Curiosity"
    mars._date = "2015-04-27"

    with patch("NASA_API.Source.mars.get_request", return_value=MOCK_MARS_RESPONSE), \
         patch("NASA_API.Source.mars.download_image_url", return_value=MOCK_IMAGE_PATH) as mock_download:
        result = mars.mars(max_photos=-1)

        # Steps (5)+(6) - Assert result and multi-URL download.
        assert result is True
        call_kwargs = mock_download.call_args.kwargs
        assert len(call_kwargs["image_url_list"]) == 2


def test_mars_download_failure():
    """
    Test purpose - Correct error handling when the image download fails.
    Criteria: False is returned when download_image_url returns None.

    Test steps:
    1) Create a MARS instance with rover and date set.
    2) Mock get_request to return a valid response.
    3) Mock download_image_url to return None.
    4) Call mars().
    5) Assert False is returned.
    """

    mars = MARS()
    mars._rover = "Curiosity"
    mars._date = "2015-04-27"

    with patch("NASA_API.Source.mars.get_request", return_value=MOCK_MARS_RESPONSE), \
         patch("NASA_API.Source.mars.download_image_url", return_value=None):
        # Steps (4)+(5) - Call and assert.
        assert mars.mars() is False


# ──────────────────────────────────────────────────────────── #
#  mars_rover_manifest() unit tests                             #
# ──────────────────────────────────────────────────────────── #

def test_mars_rover_manifest_no_rover():
    """
    Test purpose - Correct error handling when manifest is requested without a rover.
    Criteria: None is returned when no rover is configured.

    Test steps:
    1) Create a MARS instance without setting a rover.
    2) Call mars_rover_manifest().
    3) Assert None is returned.
    """

    mars = MARS()
    assert mars.mars_rover_manifest() is None


def test_mars_rover_manifest_success():
    """
    Test purpose - Successful retrieval of a rover mission manifest.
    Criteria: A dictionary with the correct manifest fields is returned.

    Test steps:
    1) Create a MARS instance with a rover set.
    2) Mock get_request to return a valid manifest response.
    3) Call mars_rover_manifest().
    4) Assert the returned dictionary contains the expected keys and values.
    """

    mars = MARS()
    mars._rover = "Curiosity"

    with patch("NASA_API.Source.mars.get_request", return_value=MOCK_MANIFEST_RESPONSE):
        manifest = mars.mars_rover_manifest()

        # Steps (3)+(4) - Assert manifest content.
        assert manifest is not None
        assert manifest["landing_date"] == "2012-08-06"
        assert manifest["status"] == "active"
        assert manifest["total_photos"] == 700000