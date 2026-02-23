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
#  Attribute tests                                              #
# ──────────────────────────────────────────────────────────── #

def test_nil_query_encoded_in_constructor():
    """
    Test purpose - Automatic URL encoding of spaces in the query at construction time.
    Criteria: Spaces in the query string are replaced with '%20' by the constructor.

    Test steps:
    1) Create a NIL instance with a query string containing spaces.
    2) Assert the stored query attribute has spaces replaced with '%20'.
    """

    nil = NIL(query="Crab nebula")

    # Step (2) - Assert spaces are encoded.
    assert nil.query == "Crab%20nebula"


# ──────────────────────────────────────────────────────────── #
#  nasa_image_library_query() unit tests                        #
# ──────────────────────────────────────────────────────────── #

def test_nil_no_query_set():
    """
    Test purpose - Correct error handling when no query is configured.
    Criteria: False is returned when nasa_image_library_query() is called without a query.

    Test steps:
    1) Create a NIL instance with media type and year range but no query.
    2) Call nasa_image_library_query().
    3) Assert False is returned.
    """

    nil = NIL(media_type="image", search_years=[2000, 2020])
    assert nil.nasa_image_library_query() is False


def test_nil_no_media_type_set():
    """
    Test purpose - Correct error handling when no media type is configured.
    Criteria: False is returned when nasa_image_library_query() is called without a media type.

    Test steps:
    1) Create a NIL instance with query and year range but no media type.
    2) Call nasa_image_library_query().
    3) Assert False is returned.
    """

    nil = NIL(query="Crab nebula", search_years=[2000, 2020])
    assert nil.nasa_image_library_query() is False


def test_nil_invalid_media_type():
    """
    Test purpose - Correct error handling when an unsupported media type is provided.
    Criteria: False is returned when the media type is not in the supported list.

    Test steps:
    1) Create a NIL instance with a query, an unsupported media type, and a valid year range.
    2) Call nasa_image_library_query().
    3) Assert False is returned.
    """

    nil = NIL(query="Crab nebula", media_type="video", search_years=[2000, 2020])
    assert nil.nasa_image_library_query() is False


def test_nil_no_search_years():
    """
    Test purpose - Correct error handling when no search year range is configured.
    Criteria: False is returned when nasa_image_library_query() is called without a year range.

    Test steps:
    1) Create a NIL instance with query and media type but no search year range.
    2) Call nasa_image_library_query().
    3) Assert False is returned.
    """

    nil = NIL(query="Crab nebula", media_type="image")
    assert nil.nasa_image_library_query() is False


def test_nil_api_request_failure():
    """
    Test purpose - Correct error handling when the API request fails.
    Criteria: False is returned when get_request() returns None.

    Test steps:
    1) Create a NIL instance with all required parameters.
    2) Mock get_request to return None.
    3) Call nasa_image_library_query().
    4) Assert False is returned.
    """

    nil = NIL(query="Crab nebula", media_type="image", search_years=[2000, 2020])

    with patch("NASA_API.Source.nil.get_request", return_value=None):
        # Steps (3)+(4) - Call and assert.
        assert nil.nasa_image_library_query() is False


def test_nil_no_results():
    """
    Test purpose - Correct handling of an API response with no matching results.
    Criteria: False is returned when the items list is empty.

    Test steps:
    1) Create a NIL instance with all required parameters.
    2) Mock get_request to return an empty items collection.
    3) Call nasa_image_library_query().
    4) Assert False is returned.
    """

    nil = NIL(query="Crab nebula", media_type="image", search_years=[2000, 2020])

    with patch("NASA_API.Source.nil.get_request", return_value=MOCK_NIL_EMPTY_RESPONSE):
        # Steps (3)+(4) - Call and assert.
        assert nil.nasa_image_library_query() is False


def test_nil_success():
    """
    Test purpose - Successful query and download from the NASA Image Library.
    Criteria: True is returned and download_image_url is called with the correct URL from the response.

    Test steps:
    1) Create a NIL instance with all required parameters.
    2) Mock get_request to return a valid response with one result.
    3) Mock download_image_url to return a dummy path.
    4) Call nasa_image_library_query().
    5) Assert True is returned and the correct image URL was passed to the download function.
    """

    nil = NIL(query="Crab nebula", media_type="image", search_years=[2000, 2020])

    with patch("NASA_API.Source.nil.get_request", return_value=MOCK_NIL_RESPONSE), \
         patch("NASA_API.Source.nil.download_image_url", return_value=MOCK_IMAGE_PATH) as mock_download:
        result = nil.nasa_image_library_query()

        # Steps (4)+(5) - Assert result and correct URL.
        assert result is True
        call_kwargs = mock_download.call_args.kwargs
        expected_url = MOCK_NIL_RESPONSE["collection"]["items"][0]["links"][0]["href"]
        assert call_kwargs["image_url_list"] == [expected_url]


def test_nil_download_failure():
    """
    Test purpose - Correct error handling when the image download fails.
    Criteria: False is returned when download_image_url returns None.

    Test steps:
    1) Create a NIL instance with all required parameters.
    2) Mock get_request to return a valid response.
    3) Mock download_image_url to return None.
    4) Call nasa_image_library_query().
    5) Assert False is returned.
    """

    nil = NIL(query="Crab nebula", media_type="image", search_years=[2000, 2020])

    with patch("NASA_API.Source.nil.get_request", return_value=MOCK_NIL_RESPONSE), \
         patch("NASA_API.Source.nil.download_image_url", return_value=None):
        # Steps (4)+(5) - Call and assert.
        assert nil.nasa_image_library_query() is False