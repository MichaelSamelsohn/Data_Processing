# Imports #
import pytest

from datetime import date, timedelta
from NASA_API.Source.apod import APOD
from constants import *

@pytest.mark.parametrize(
    "input_date, result",
    [
        # Valid dates.
        ("2000-01-01", True),                                              # Correct format date.
        (date.today().strftime('%Y-%m-%d'), True),                         # Today's date.
        # Invalid dates/format.
        ("1900-01-01", False),                                             # Too old date.
        ("2000-02-30", False),                                             # Non-existent date.
        ((date.today() + timedelta(days=1)).strftime('%Y-%m-%d'), False),  # Tomorrow's date.
        ("INVALID_DATE", False)                                            # Invalid format.
    ]
)
def test_validate_date(input_date, result):
    """
    Test purpose - Basic functionality of date validation.
    Criteria: Correct result for valid/invalid dates/formats.

    Test steps:
    1) Validate a date/format.
    2) Assert that result matches the expected outcome.
    """

    # Steps (1)+(2) - Validate and assert that result is correct.
    assert APOD.validate_date(date=input_date) == result


def test_apod_no_date_set():
    """
    Test purpose - Correct error handling of when no date is set.
    Criteria: False is returned when requesting APOD without specifying a date.

    Test steps:
    1) Request APOD without a date set.
    2) Assert that False is returned.
    """

    # Step (1)+(2) - Request APOD without set date and assert False return value.
    apod = APOD()
    assert apod.astronomy_picture_of_the_day() == False
