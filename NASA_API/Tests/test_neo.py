# Imports #
import pytest

from unittest.mock import patch
from NASA_API.Source.neo import NEO
from constants import *


# Shared mock data #
MOCK_NEO_FEED_RESPONSE = {
    "element_count": 2,
    "near_earth_objects": {
        "2024-01-01": [
            {
                "id": "2000433",
                "name": "433 Eros (A898 PA)",
                "is_potentially_hazardous_asteroid": False,
                "estimated_diameter": {
                    "meters": {
                        "estimated_diameter_min": 10800.0,
                        "estimated_diameter_max": 24100.0,
                    }
                },
                "close_approach_data": [
                    {
                        "close_approach_date": "2024-01-01",
                        "miss_distance": {"kilometers": "5432100.0"},
                        "relative_velocity": {"kilometers_per_hour": "48500.0"},
                    }
                ],
            }
        ],
        "2024-01-02": [
            {
                "id": "3542519",
                "name": "(2010 PK9)",
                "is_potentially_hazardous_asteroid": True,
                "estimated_diameter": {
                    "meters": {
                        "estimated_diameter_min": 150.0,
                        "estimated_diameter_max": 340.0,
                    }
                },
                "close_approach_data": [
                    {
                        "close_approach_date": "2024-01-02",
                        "miss_distance": {"kilometers": "1200000.0"},
                        "relative_velocity": {"kilometers_per_hour": "72000.0"},
                    }
                ],
            }
        ],
    },
}
MOCK_LOOKUP_RESPONSE = {
    "id": "2000433",
    "name": "433 Eros (A898 PA)",
    "is_potentially_hazardous_asteroid": False,
    "orbital_data": {
        "orbit_class": {"orbit_class_type": "AMO"},
        "semi_major_axis": "1.457978",
        "eccentricity": "0.222739",
        "inclination": "10.829",
        "orbital_period": "643.219",
    },
}


# ──────────────────────────────────────────────────────────── #
#  validate_date tests                                          #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize(
    "input_date, result",
    [
        # Valid dates.
        ("2024-01-01", True),   # Typical past date.
        ("2030-06-15", True),   # Future date (orbital predictions are allowed).
        # Invalid dates / formats.
        ("2024-02-30", False),  # Non-existent calendar date.
        ("01-01-2024", False),  # Wrong order (DD-MM-YYYY).
        ("2024/01/01", False),  # Wrong separator.
        ("INVALID",    False),  # Non-date string entirely.
    ]
)
def test_validate_date(input_date, result):
    """
    Test purpose - Basic functionality of date format validation.
    Criteria: Correct boolean returned for valid and invalid date strings.

    Test steps:
    1) Call NEO.validate_date() with the parametrized input.
    2) Assert the return value matches the expected result.
    """

    # Steps (1)+(2) - Validate and assert.
    assert NEO.validate_date(date=input_date) == result


# ──────────────────────────────────────────────────────────── #
#  validate_date_range tests                                    #
# ──────────────────────────────────────────────────────────── #

@pytest.mark.parametrize(
    "start_date, end_date, result",
    [
        # Valid ranges.
        ("2024-01-01", "2024-01-01", True),   # Same day (delta = 0).
        ("2024-01-01", "2024-01-04", True),   # Mid-range (delta = 3).
        ("2024-01-01", "2024-01-08", True),   # Exactly at the 7-day limit (delta = 7).
        # Invalid ranges.
        ("2024-01-08", "2024-01-01", False),  # start > end.
        ("2024-01-01", "2024-01-09", False),  # Exceeds 7-day API limit (delta = 8).
        ("2024-01-01", "2024-02-01", False),  # Far exceeds the limit.
    ]
)
def test_validate_date_range(start_date, end_date, result):
    """
    Test purpose - Date range validation enforcing ordering and the 7-day API window.
    Criteria: Correct boolean returned for valid and invalid date pairs.

    Test steps:
    1) Call NEO.validate_date_range() with the parametrized start and end dates.
    2) Assert the return value matches the expected result.
    """

    # Steps (1)+(2) - Validate and assert.
    assert NEO.validate_date_range(start_date=start_date, end_date=end_date) == result


# ──────────────────────────────────────────────────────────── #
#  near_earth_objects() unit tests                              #
# ──────────────────────────────────────────────────────────── #

def test_neo_invalid_start_date():
    """
    Test purpose - Correct error handling when the start date is invalid.
    Criteria: False is returned when near_earth_objects() is called with a malformed start date.

    Test steps:
    1) Create a NEO instance with an invalid start date.
    2) Call near_earth_objects().
    3) Assert False is returned.
    """

    neo = NEO(start_date="INVALID", end_date="2024-01-07")
    assert neo.near_earth_objects() is False


def test_neo_invalid_end_date():
    """
    Test purpose - Correct error handling when the end date is invalid.
    Criteria: False is returned when near_earth_objects() is called with a malformed end date.

    Test steps:
    1) Create a NEO instance with an invalid end date.
    2) Call near_earth_objects().
    3) Assert False is returned.
    """

    neo = NEO(start_date="2024-01-01", end_date="INVALID")
    assert neo.near_earth_objects() is False


def test_neo_start_after_end():
    """
    Test purpose - Correct error handling when start date is later than end date.
    Criteria: False is returned when start_date > end_date.

    Test steps:
    1) Create a NEO instance with start_date after end_date.
    2) Call near_earth_objects().
    3) Assert False is returned.
    """

    neo = NEO(start_date="2024-01-07", end_date="2024-01-01")
    assert neo.near_earth_objects() is False


def test_neo_range_exceeds_limit():
    """
    Test purpose - Correct error handling when the date range exceeds the 7-day API limit.
    Criteria: False is returned when the window spans more than 7 days.

    Test steps:
    1) Create a NEO instance with a 30-day date range.
    2) Call near_earth_objects().
    3) Assert False is returned.
    """

    neo = NEO(start_date="2024-01-01", end_date="2024-01-31")
    assert neo.near_earth_objects() is False


def test_neo_api_request_failure():
    """
    Test purpose - Correct error handling when the API request fails.
    Criteria: False is returned when get_request() returns None.

    Test steps:
    1) Create a NEO instance with valid dates.
    2) Mock get_request to return None (simulating a network error or bad status code).
    3) Call near_earth_objects().
    4) Assert False is returned.
    """

    neo = NEO(start_date="2024-01-01", end_date="2024-01-07")

    with patch("NASA_API.Source.neo.get_request", return_value=None):
        # Steps (3)+(4) - Call and assert.
        assert neo.near_earth_objects() is False


def test_neo_success():
    """
    Test purpose - Successful feed query stores results in _neo_feed.
    Criteria: True is returned and neo_feed is populated with the API response.

    Test steps:
    1) Create a NEO instance with valid dates.
    2) Mock get_request to return the shared mock feed response.
    3) Call near_earth_objects().
    4) Assert True is returned.
    5) Assert neo_feed matches the mock response.
    """

    neo = NEO(start_date="2024-01-01", end_date="2024-01-07")

    with patch("NASA_API.Source.neo.get_request", return_value=MOCK_NEO_FEED_RESPONSE):
        result = neo.near_earth_objects()

    # Steps (4)+(5) - Assert result and populated feed.
    assert result is True
    assert neo.neo_feed == MOCK_NEO_FEED_RESPONSE


def test_neo_feed_element_count():
    """
    Test purpose - Correct element count is accessible from the stored feed.
    Criteria: The element_count field of neo_feed matches the value in the mock response.

    Test steps:
    1) Create a NEO instance with valid dates.
    2) Mock get_request to return the shared mock feed response.
    3) Call near_earth_objects().
    4) Assert neo_feed["element_count"] equals the expected count.
    """

    neo = NEO(start_date="2024-01-01", end_date="2024-01-07")

    with patch("NASA_API.Source.neo.get_request", return_value=MOCK_NEO_FEED_RESPONSE):
        neo.near_earth_objects()

    # Step (4) - Assert element count.
    assert neo.neo_feed["element_count"] == MOCK_NEO_FEED_RESPONSE["element_count"]


def test_neo_feed_none_before_query():
    """
    Test purpose - neo_feed is None before near_earth_objects() is called.
    Criteria: The neo_feed property returns None on a freshly constructed instance.

    Test steps:
    1) Create a NEO instance.
    2) Assert neo_feed is None without calling near_earth_objects().
    """

    neo = NEO(start_date="2024-01-01", end_date="2024-01-07")

    # Step (2) - Assert initial state.
    assert neo.neo_feed is None


# ──────────────────────────────────────────────────────────── #
#  lookup() unit tests                                          #
# ──────────────────────────────────────────────────────────── #

def test_neo_lookup_success():
    """
    Test purpose - Successful asteroid lookup returns the API response dict.
    Criteria: The dict returned by lookup() matches the mock response.

    Test steps:
    1) Mock get_request to return the shared mock lookup response.
    2) Call NEO.lookup() with a valid SPK-ID.
    3) Assert the returned dict matches the mock response.
    """

    with patch("NASA_API.Source.neo.get_request", return_value=MOCK_LOOKUP_RESPONSE):
        # Steps (2)+(3) - Call and assert.
        result = NEO.lookup(asteroid_id="2000433")

    assert result == MOCK_LOOKUP_RESPONSE


def test_neo_lookup_failure():
    """
    Test purpose - Correct error handling when the asteroid lookup fails.
    Criteria: None is returned when get_request() returns None.

    Test steps:
    1) Mock get_request to return None.
    2) Call NEO.lookup() with an arbitrary ID.
    3) Assert None is returned.
    """

    with patch("NASA_API.Source.neo.get_request", return_value=None):
        # Steps (2)+(3) - Call and assert.
        result = NEO.lookup(asteroid_id="9999999")

    assert result is None
