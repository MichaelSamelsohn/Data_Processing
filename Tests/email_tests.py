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
MOCK_SERVER_HOST = "mock.server.host"
MOCK_SERVER_PORT = 587


class TestClass:
    @pytest.mark.parametrize(
        "recipients, expected_outcome",
        [([], False),  # Empty recipient list.
         ([MOCK_EMAIL_ADDRESS], True)])  # Recipient list includes an email.
    def test_recipients_list_empty(self, recipients, expected_outcome):
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
    def test_recipient_email_addresses_validity(self, recipients, expected_outcome):
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

    @pytest.mark.parametrize(
        "server_host, expected_outcome",
        [("", False), ("mock.illegal$.host", False), (MOCK_SERVER_HOST, True)])
    def test_server_host_validity(self, server_host, expected_outcome):
        """
        Test type - Unit.
        Function under test - Email.__check_essential_parameters().
        Test purpose - Check that the function returns False when server host is invalid, True otherwise.
        Test steps:
            1) Create an email object.
            2) Activate the check essential parameters method.
            3) Assert that outcome is as expected.

        :return: True if test passes, AssertionError otherwise.
        """

        email = Email(sender_address=MOCK_EMAIL_ADDRESS, sender_password=MOCK_EMAIL_PASSWORD,
                      recipients=[MOCK_EMAIL_ADDRESS], subject="", server_host=server_host)
        assert email._Email__check_essential_parameters() == expected_outcome
        return True

    @pytest.mark.parametrize(
        "port_number, expected_outcome",
        [(-MOCK_SERVER_PORT, False), (MOCK_SERVER_PORT, True)])
    def test_server_port_validity(self, port_number, expected_outcome):
        """
        Test type - Unit.
        Function under test - Email.__check_essential_parameters().
        Test purpose - Check that the function returns False when server port number is invalid, True otherwise.
        Test steps:
            1) Create an email object.
            2) Activate the check essential parameters method.
            3) Assert that outcome is as expected.

        :return: True if test passes, AssertionError otherwise.
        """

        email = Email(sender_address=MOCK_EMAIL_ADDRESS, sender_password=MOCK_EMAIL_PASSWORD,
                      recipients=[MOCK_EMAIL_ADDRESS], subject="", server_port=port_number)
        assert email._Email__check_essential_parameters() == expected_outcome
        return True

    @pytest.mark.parametrize(
        "email_address, expected_outcome",
        # Valid email addresses:
        [("niceandsimple@gmail.com", True),
         ("very.common@gmail.com", True),
         ("disposable.style.email.with+symbol@gmail.com", True),
         ("other.email-with-dash@gmail.com", True),
         # Invalid email addresses:
         ("invalid..email@gmail.com", False),  # Two dots in a row.
         ("-invalid-email@gmail.com", False),  # Starts with a dash.
         ("invalid--email@gmail.com", False),  # Two dashes in a row.
         ("niceandsimple@fakedomain.com", False)])  # Not Gmail domain.
    def test_email_address_validity(self, email_address, expected_outcome):
        """
        Test type - Unit.
        Function under test - Email.__check_email_address_validity().
        Test purpose - Check that the function returns False when email address is invalid, True otherwise.
        Test steps:
            1) Create an email object.
            2) Activate the check email address validity method.
            3) Assert that outcome is as expected.

        :return: True if test passes, AssertionError otherwise.
        """

        email = Email(sender_address=MOCK_EMAIL_ADDRESS, sender_password=MOCK_EMAIL_PASSWORD,
                      recipients=[MOCK_EMAIL_ADDRESS], subject="")
        assert email._Email__check_email_address_validity(email_address=email_address) == expected_outcome
        return True
