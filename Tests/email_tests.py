"""
Script Name - email_tests.py (part of Tests directory).

Purpose - Unit tests for the email class.

Created by - Michael Samelsohn, 09/04/2024
"""

# Imports #
import pytest

from Utilities.email import Email
from Settings.settings import log

# Constants #
MOCK_EMAIL_ADDRESS = "mock.email@gmail.com"
MOCK_EMAIL_PASSWORD = "mock_password"


class TestClass:
    @pytest.mark.parametrize(
        "recipients, expected_outcome",
        [([], False),  # Empty recipient list.
         ([MOCK_EMAIL_ADDRESS], True)])  # Recipient list includes an email.
    def test_recipients(self, recipients, expected_outcome):
        """
        Test type - Unit.
        Function under test - Email.__check_essential_parameters().
        Test purpose - Check that the function returns False when recipients list is empty and True if not.
        Test steps:
            1) Create an email object.
            2) Activate the check essential parameters method.
            3) Assert that outcome is as expected.

        :return: True if test passes, AssertionError otherwise.
        """

        email = Email(sender_address=MOCK_EMAIL_ADDRESS, sender_password=MOCK_EMAIL_PASSWORD,
                      recipients=recipients, subject="")
        assert email._Email__check_essential_parameters() == expected_outcome
        return True

    @pytest.mark.parametrize(
        "recipients, expected_outcome",
        # Good email addresses.
        [(["niceandsimple@gmail.com", "very.common@gmail.com",
           "disposable.style.email.with+symbol@gmail.com", "other.email-with-dash@gmail.com"], True),
         # Bad email addresses.
         (["invalid..email@gmail.com", "-invalid-email@gmail.com",
           "invalid--email@gmail.com", "niceandsimple@fakedomain.com"], False)])
    def test_email_addresses_validity(self, recipients, expected_outcome):
        """
        Test type - Unit.
        Function under test - Email.__check_essential_parameters().
        Test purpose - Check that the function returns False when recipients list includes invalid email addresses and
        True otherwise.
        Test steps:
            1) Create an email object.
            2) Activate the check essential parameters method.
            3) Assert that outcome is as expected.

        :return: True if test passes, AssertionError otherwise.
        """

        email = Email(sender_address=MOCK_EMAIL_ADDRESS, sender_password=MOCK_EMAIL_PASSWORD,
                      recipients=recipients, subject="")
        assert email._Email__check_essential_parameters() == expected_outcome
        return True
