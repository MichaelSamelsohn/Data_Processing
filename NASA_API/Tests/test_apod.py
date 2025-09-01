# Imports #
import pytest

from datetime import date, timedelta
from NASA_API.Source.apod import APOD


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
