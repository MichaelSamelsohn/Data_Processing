# Imports #
import pytest

from datetime import datetime
from unittest.mock import patch
from NASA_API.Source.nil import NIL
from constants import *


# Shared mock data #
MOCK_IMAGE_PATH = "/tmp/NIL_test.JPG"
MOCK_NIL_RESPONSE = {
    "collection": {
        "items": [
            {
                "links": [{"href": "https://images-assets.nasa.gov/image/crab/crab~thumb.jpg"}],
                "data": [{"title": "Crab Nebula", "description": "Test description."}],
            }
        ]
    }
}
MOCK_NIL_EMPTY_RESPONSE = {
    "collection": {
        "items": []
    }
}


# ──────────────────────────────────────────────────────────── #
#  Year range validation tests                                  #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize(
    "year_range, result",
    [
        # Valid ranges.
        ([1960, 2000], True),                                                        # Minimum start year.
        ([2000, 2020], True),                                                        # Typical range.
        ([2000, datetime.now().year], True),                                         # End at current year.
        # Invalid ranges.
        (1960, False),                                                               # Not a list/tuple.
        ([2000], False),                                                             # Only one element.
        ([2000, 2010, 2020], False),                                                 # Three elements.
        (["2000", "2020"], False),                                                   # String elements.
        ([1959, 2020], False),                                                       # start < NIL_FIRST_YEAR (1960).
        ([2020, 2010], False),                                                       # start > end.
        ([2000, datetime.now().year + 1], False),                                    # end > current year.
    ]
)
def test_validate_year_range(year_range, result):
    """
    Test purpose - Year range validation for NIL search queries.
    Criteria: Correct boolean returned for valid and invalid year ranges.

    Test steps:
    1) Call NIL.validate_year_range() with the parametrized input.
    2) Assert the return value matches the expected result.
    """

    # Steps (1)+(2) - Validate and assert.
    assert NIL.validate_year_range(year_range=year_range) == result


# ──────────────────────────────────────────────────────────── #
#  Property setter tests                                        #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize("media_type", ["image", "audio"])
def test_media_type_setter_valid(media_type):
    """
    Test purpose - Successful assignment of a valid media type.
    Criteria: The media_type property is set to the provided value.

    Test steps:
    1) Create a NIL instance.
    2) Set the media type to a valid value.
    3) Assert the media_type property equals the provided value.
    """

    nil = NIL()
    nil.media_type = media_type

    # Step (3) - Assert media type was set.
    assert nil.media_type == media_type


def test_media_type_setter_invalid():
    """
    Test purpose - Rejection of an unsupported media type.
    Criteria: The media_type property remains None when an invalid type is provided.

    Test steps:
    1) Create a NIL instance.
    2) Set the media type to an unsupported value.
    3) Assert the media_type property remains None.
    """

    nil = NIL()
    nil.media_type = "video"  # Not in NIL_MEDIA_TYPES.

    # Step (3) - Assert media type was not set.
    assert nil.media_type is None


def test_query_setter_encodes_spaces():
    """
    Test purpose - Automatic URL encoding of spaces in the search query.
    Criteria: Spaces in the query string are replaced with '%20'.

    Test steps:
    1) Create a NIL instance.
    2) Set the query to a string containing spaces.
    3) Assert spaces are URL-encoded in the stored query.
    """

    nil = NIL()
    nil.query = "Crab nebula"

    # Step (3) - Assert spaces are encoded.
    assert nil.query == "Crab%20nebula"


# ──────────────────────────────────────────────────────────── #
#  nasa_image_library_query() unit tests                        #
# ──────────────────────────────────────────────────────────── #

def test_nil_no_query_set():
    """
    Test purpose - Correct error handling when no query is configured.
    Criteria: False is returned when nasa_image_library_query() is called without a query.

    Test steps:
    1) Create a NIL instance with a media type but no query.
    2) Call nasa_image_library_query().
    3) Assert False is returned.
    """

    nil = NIL()
    nil.media_type = "image"
    assert nil.nasa_image_library_query() is False


def test_nil_no_media_type_set():
    """
    Test purpose - Correct error handling when no media type is configured.
    Criteria: False is returned when nasa_image_library_query() is called without a media type.

    Test steps:
    1) Create a NIL instance with a query but no media type.
    2) Call nasa_image_library_query().
    3) Assert False is returned.
    """

    nil = NIL()
    nil.query = "Crab nebula"
    assert nil.nasa_image_library_query() is False


def test_nil_api_request_failure():
    """
    Test purpose - Correct error handling when the API request fails.
    Criteria: False is returned when get_request() returns None.

    Test steps:
    1) Create a NIL instance with query and media type set.
    2) Mock get_request to return None.
    3) Call nasa_image_library_query().
    4) Assert False is returned.
    """

    nil = NIL()
    nil._query = "Crab%20nebula"
    nil._media_type = "image"

    with patch("NASA_API.Source.nil.get_request", return_value=None):
        # Steps (3)+(4) - Call and assert.
        assert nil.nasa_image_library_query() is False


def test_nil_no_results():
    """
    Test purpose - Correct handling of an API response with no matching results.
    Criteria: False is returned when the items list is empty.

    Test steps:
    1) Create a NIL instance with query and media type set.
    2) Mock get_request to return an empty items collection.
    3) Call nasa_image_library_query().
    4) Assert False is returned.
    """

    nil = NIL()
    nil._query = "Crab%20nebula"
    nil._media_type = "image"

    with patch("NASA_API.Source.nil.get_request", return_value=MOCK_NIL_EMPTY_RESPONSE):
        # Steps (3)+(4) - Call and assert.
        assert nil.nasa_image_library_query() is False


def test_nil_success():
    """
    Test purpose - Successful query and download from the NASA Image Library.
    Criteria: True is returned and download_image_url is called with the correct URL from the response.

    Test steps:
    1) Create a NIL instance with query, media type, and year range set.
    2) Mock get_request to return a valid response with one result.
    3) Mock download_image_url to return a dummy path.
    4) Call nasa_image_library_query().
    5) Assert True is returned and the correct image URL was passed to the download function.
    """

    nil = NIL()
    nil._query = "Crab%20nebula"
    nil._media_type = "image"
    nil._search_years = [2000, 2020]

    with patch("NASA_API.Source.nil.get_request", return_value=MOCK_NIL_RESPONSE), \
         patch("NASA_API.Source.nil.download_image_url", return_value=MOCK_IMAGE_PATH) as mock_download:
        result = nil.nasa_image_library_query()

        # Steps (4)+(5) - Assert result and correct URL.
        assert result is True
        call_kwargs = mock_download.call_args.kwargs
        expected_url = MOCK_NIL_RESPONSE["collection"]["items"][0]["links"][0]["href"]
        assert call_kwargs["image_url_list"] == [expected_url]


def test_nil_success_without_year_range():
    """
    Test purpose - Successful query without a year range (search entire archive).
    Criteria: True is returned and the request URL contains no year filter parameters.

    Test steps:
    1) Create a NIL instance with only query and media type set (no year range).
    2) Mock get_request and download_image_url.
    3) Call nasa_image_library_query().
    4) Assert True is returned.
    5) Assert the URL passed to get_request contains no year_start or year_end parameters.
    """

    nil = NIL()
    nil._query = "Saturn"
    nil._media_type = "image"
    # Intentionally no search_years set.

    with patch("NASA_API.Source.nil.get_request", return_value=MOCK_NIL_RESPONSE) as mock_get, \
         patch("NASA_API.Source.nil.download_image_url", return_value=MOCK_IMAGE_PATH):
        result = nil.nasa_image_library_query()

        # Steps (4)+(5) - Assert result and URL has no year filters.
        assert result is True
        call_url = mock_get.call_args.kwargs["url"]
        assert "year_start" not in call_url
        assert "year_end" not in call_url


def test_nil_download_failure():
    """
    Test purpose - Correct error handling when the image download fails.
    Criteria: False is returned when download_image_url returns None.

    Test steps:
    1) Create a NIL instance with all required properties set.
    2) Mock get_request to return a valid response.
    3) Mock download_image_url to return None.
    4) Call nasa_image_library_query().
    5) Assert False is returned.
    """

    nil = NIL()
    nil._query = "Crab%20nebula"
    nil._media_type = "image"

    with patch("NASA_API.Source.nil.get_request", return_value=MOCK_NIL_RESPONSE), \
         patch("NASA_API.Source.nil.download_image_url", return_value=None):
        # Steps (4)+(5) - Call and assert.
        assert nil.nasa_image_library_query() is False