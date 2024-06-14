"""
Script Name - log_tests.py (part of Tests directory).

Purpose - Unit tests for the logger class.

Created by - Michael Samelsohn, 31/05/2024
"""

# Imports #
import datetime
import os
import pytest
import pandas as pd

from Utilities.logger import Logger

# Constants #
LOG_LEVELS = ["debug", "info", "warning", "error", "critical"]
LOGGER_DICTIONARY = {
    "debug": {"MESSAGE": "Debug message", "LOG_LEVEL_INT": 10},
    "info": {"MESSAGE": "Info message", "LOG_LEVEL_INT": 20},
    "warning": {"MESSAGE": "Warning message", "LOG_LEVEL_INT": 30},
    "error": {"MESSAGE": "Error message", "LOG_LEVEL_INT": 40},
    "critical": {"MESSAGE": "Critical message", "LOG_LEVEL_INT": 50},
}
LOG_FILE_NAME = "test_log.txt"
INVALID_LOG_LEVEL = 'INVALID_LOG_LEVEL'
MOCK_LOG_ENTRY = [
    ["random_time", "INFO", "random_message1"],
    ["random_time", "DEBUG", "random_message2"]
                ]
MOCK_LOG_DF = pd.DataFrame(MOCK_LOG_ENTRY, columns=['asctime', 'levelname', 'message'])
FORMAT_STRING = "%(message)s"


@pytest.fixture
def log():
    """Stream logger object"""
    return Logger()


@pytest.fixture
def file_log():
    """File logger object"""
    return FileLogger()


class FileLogger:
    """An extension of the logger where the file handler is enabled."""
    def __init__(self):
        """
        Initialization of the file handler, which is simply initiating the default logger while setting the name and
        enabling the file handler.
        Note - If the file handler is enabled before the file name is set, it will generate a file with default value
        for its name, therefore, it is important to first determine the file name and then enable the file handler.
        """

        self.log = Logger()

        # Set the log file settings.
        self.log.file_name = LOG_FILE_NAME
        # Enabling the file handler.
        self.log.file_handler = True

    def print_log_messages(self, format_string_prefix="") -> list:
        """
        Print log messages with selected prefix (useful for format string changes/tests).

        :param format_string_prefix: Prefix for the message printed to the log file.

        :return: The printed log messages (in the written order).
        """

        # Printing the messages.
        log_messages = []
        for log_level in LOG_LEVELS:
            # Get a named attribute from an object; getattr(x, 'y') is equivalent to x.y.
            getattr(self.log, log_level)(LOGGER_DICTIONARY[log_level]["MESSAGE"])
            log_messages.append(
                f"{format_string_prefix}{log_level.upper()} - {LOGGER_DICTIONARY[log_level]['MESSAGE']}\n")

        return log_messages

    def assert_log_file(self, log_messages) -> bool | AssertionError:
        """
        Read the log file lines and assert it includes all the expected log messages.
        Regardless of the outcome, the log file is deleted at the end.

        :param log_messages: List of log messages to be found in the log file.

        :return: True if file content is the same as the provided log messages, assertion error otherwise.
        """

        # Read the log file lines and assert it includes all the messages.
        try:
            with open(LOG_FILE_NAME, mode='r') as log_file:
                lines = log_file.readlines()
            assert lines == log_messages
        finally:
            # Delete the log file.
            self.log.file_handler = False  # Disabling the file handler, otherwise there is a permission error.
            os.remove(LOG_FILE_NAME)

        return True


class TestClass:
    @pytest.mark.parametrize("log_level", LOG_LEVELS)
    def test_basic_log_message(self, log, caplog, log_level):
        """
        Test type - Unit.
        Function under test - Logger.debug()/Logger.info()/Logger.warning()/Logger.error()/Logger.critical().
        Test purpose - Check that the function outputs the expected level message to the sys.stdout.
        Test steps:
            1) Log a message.
            2) Assert that outcome is as expected.

        :param log: Logger object with default parameters.
        :param caplog: sys.stdout output.

        :return: True if test passes, AssertionError otherwise.
        """

        message_parameters = LOGGER_DICTIONARY[log_level]

        # Get a named attribute from an object; getattr(x, 'y') is equivalent to x.y.
        getattr(log, log_level)(message_parameters["MESSAGE"])
        assert caplog.record_tuples == \
               [('logger.py', message_parameters["LOG_LEVEL_INT"], message_parameters["MESSAGE"])]
        return True

    def test_multiple_log_messages(self, log, caplog):
        """
        Test type - Unit.
        Function under test - Logger.debug()/Logger.info()/Logger.warning()/Logger.error()/Logger.critical().
        Test purpose - Check that when multiple messages are output, all traffic reaches to sys.stdout.
        Test steps:
            1) Log several messages.
            2) Assert that outcome is as expected.

        :param log: Logger object with default parameters.
        :param caplog: sys.stdout output.

        :return: True if test passes, AssertionError otherwise.
        """

        log_messages = []

        for log_level in LOG_LEVELS:
            # Get a named attribute from an object; getattr(x, 'y') is equivalent to x.y.
            getattr(log, log_level)(LOGGER_DICTIONARY[log_level]["MESSAGE"])
            log_messages.append(
                ('logger.py', LOGGER_DICTIONARY[log_level]["LOG_LEVEL_INT"], LOGGER_DICTIONARY[log_level]["MESSAGE"]))

        assert caplog.record_tuples == log_messages
        return True

    @pytest.mark.parametrize("exception", [ZeroDivisionError, FileNotFoundError, Exception])
    def test_exception_log_message(self, log, caplog, exception):
        """
        Test type - Unit.
        Function under test - Logger.exception().
        Test purpose - Check that the function outputs the expected level message to the sys.stdout and raises the
        specified exception.
        Test steps:
            1) Log a message.
            2) Assert that outcome is as expected.

        :param log: Logger object with default parameters.
        :param caplog: sys.stdout output.
        :param exception: Exception type.

        :return: True if both message and raised exception are as expected, AssertionError or another exception
        otherwise.
        """

        critical_message_parameters = LOGGER_DICTIONARY["critical"]

        try:
            log.exception(critical_message_parameters["MESSAGE"], exception=exception)
        except exception:
            assert caplog.record_tuples == \
                   [('logger.py', critical_message_parameters["LOG_LEVEL_INT"], critical_message_parameters["MESSAGE"])]
            return True

    @pytest.mark.parametrize("data, output", [
        (1, [('logger.py', 10, "1")]),
        (1.0, [('logger.py', 10, "1.0")]),
        ("string", [('logger.py', 10, "string")]),
        (["List", "of", "strings"], [('logger.py', 10, "List"), ('logger.py', 10, "of"), ('logger.py', 10, "strings")]),
        ({"key1": "string1", "key2": "string2"},
         [('logger.py', 10, "key1 - string1"), ('logger.py', 10, "key2 - string2")]),
    ])
    def test_pretty_print(self, log, caplog, data, output):
        """
        Test type - Unit.
        Function under test - Logger.print_data().
        Test purpose - Check that pretty-printing the data works properly for all supported types.
        Test steps:
            1) Log a message for data printing.
            2) Assert that outcome is as expected.

        :param log: Logger object with default parameters.
        :param caplog: sys.stdout output.
        :param data: Data to be output.
        :param output: Pretty print of the data.

        :return: True if test passes, AssertionError otherwise.
        """

        log.print_data(data=data)
        assert output == caplog.record_tuples
        return True

    def test_file_handler_enabled(self, file_log):
        """
        Test type - Unit.
        Function under test - Logger.file_handler() and its extensions.
        Test purpose - Check the file handler functionality. Also, this tests format string changes (it is easier and
        more robust to test file handler without exact time stamps, therefore, the format string excludes it).
        Test steps:
            1) Change the format string.
            2) Log messages.
            2) Assert that log file was generated and printed with all log messages.

        :param file_log: Logger object with file handler enabled.

        :return: True if test passes, AssertionError otherwise.
        """

        file_log.log.format_string = "%(levelname)s - %(message)s"

        return file_log.assert_log_file(log_messages=file_log.print_log_messages())

    def test_format_time(self, file_log):
        """
        Test type - Unit.
        Function under test - Logger.format_time().
        Test purpose - Check that format time changes affect the log messages accordingly.
        Test steps:
            1) Change the format time.
            2) Log messages.
            2) Assert that log file was generated and printed with all log messages.

        :param file_log: Logger object with file handler enabled.

        :return: True if test passes, AssertionError otherwise.
        """

        # Set the time format (using only the date).
        format_time = "%Y-%m-%d"
        file_log.log.format_time = format_time
        date = datetime.datetime.now().strftime(format_time)

        log_messages = file_log.print_log_messages(format_string_prefix=f"{date} - ")
        return file_log.assert_log_file(log_messages=log_messages)

    def test_log_level(self, file_log):
        """
        Test type - Unit.
        Function under test - Logger.log_level().
        Test purpose - Check that changing the log level filters messages with lower log levels.
        Test steps:
            1) Change the log level.
            2) Log messages.
            2) Assert that log file was generated and printed with non-filtered log messages.

        :param file_log: Logger object with file handler enabled.

        :return: True if test passes, AssertionError otherwise.
        """

        file_log.log.format_string = "%(levelname)s - %(message)s"
        file_log.log.log_level = LOGGER_DICTIONARY["critical"]["LOG_LEVEL_INT"]

        log_messages = file_log.print_log_messages()
        # Since the log level is set to the critical message, only critical messages should be printed.
        # Therefore, the assertion method is provided with the critical message only, which is the last.
        return file_log.assert_log_file(log_messages=[log_messages[-1]])

    def test_masked_filter(self, file_log):
        """
        Test type - Unit.
        Class under test - MaskedFilter.
        Test purpose - Check that when applying the masked patterns, messages with the selected patterns, are masked.
        Test steps:
            1) Apply a masked pattern.
            2) Log messages.
            2) Assert that log file was generated and printed with all log messages applied with masks where necessary.

        :param file_log: Logger object with file handler enabled.

        :return: True if test passes, AssertionError otherwise.
        """

        try:
            file_log.log.format_string = "%(levelname)s - %(message)s"
            critical_mask = "CRITICAL_MASK"
            file_log.log.masked_patterns = [(LOGGER_DICTIONARY['critical']['MESSAGE'], critical_mask)]

            log_messages = file_log.print_log_messages()
            # Adjusting the log messages by applying the relevant mask on the relevant message.
            log_messages[-1] = f"CRITICAL - {critical_mask}\n"
            file_log.assert_log_file(log_messages=log_messages)
        finally:
            # Reset the masked patterns attribute, otherwise it might affect other tests.
            file_log.log.masked_patterns = None
