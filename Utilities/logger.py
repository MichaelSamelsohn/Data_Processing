"""
Script Name - logging.py (part of Utilities package).

Activation - Any script that imports the following - from Utilities.logger import Logger
Moreover, initiate the logger object using the call,
# Logger #
log = Logger()

Purpose - Logs provide valuable information/indication about the running process.
The different log levels are (from lowest to highest):
    1) DEBUG - Detailed information, typically of interest only when diagnosing problems.
    2) INFO - Confirmation that things are working as expected.
    3) WARNING - An indication that something unexpected happened, or indicative of some problem in the near future
    (e.g. ‘disk space low’). The software is still working as expected.
    4) ERROR - Due to a more serious problem, the software has not been able to perform some function.
    5) CRITICAL - A serious error, indicating that the program itself may be unable to continue running.

Logger:
Logger objects have a threefold job. First, they expose several methods to application code so that applications can
log messages at runtime. Second, logger objects determine which log messages to act upon based upon severity (the
default filtering facility) or filter objects. Third, logger objects pass along relevant log messages to all interested
log handlers.

Handler:
Handler objects are responsible for dispatching the appropriate log messages (based on the log messages’ severity) to
the handler’s specified destination. Logger objects can add zero or more handler objects to themselves with an
addHandler() method. As an example scenario, an application may want to send all log messages to a log file, all log
messages of error or higher to stdout, and all messages of critical to an email address. This scenario requires three
individual handlers where each handler is responsible for sending messages of a specific severity to a specific
location.

Formatters:
Formatter objects configure the final order, structure, and contents of the log message.
Note - CustomFormatter (adapted from - https://stackoverflow.com/a/56944256/3638629) is custom formatter which allows
the coloring of the log messages (implemented for a stream handler).

Created by - Michael Samelsohn, 08/04/2024
"""

# Imports #
import logging
import os
import sys
import re

from datetime import datetime


class MaskedFilter(logging.Filter):
    """
    This class provides an option to filter selected regular expressions.
    Especially useful for removing constant prefixes/suffixes or obfuscating passwords.
    """
    def __init__(self, masked_patterns: list):
        """
        Initialize the filtering class.

        :param masked_patterns: List of all the regular expressions to be filtered when logged.
        """
        super().__init__()
        self.masked_patterns = masked_patterns

    def filter(self, record):
        if self.masked_patterns is None:
            # No filters apply.
            return True

        for pattern, mask in self.masked_patterns:
            if re.search(pattern, record.getMessage()):
                record.msg = re.sub(pattern, mask, record.msg)
        return True


class Logger:
    def __init__(self, module=os.path.basename(__file__), log_level=logging.DEBUG, color_scheme=False,
                 format_string="%(asctime)s - %(levelname)s - %(message)s", format_time="%H:%M:%S",
                 masked_patterns=None, stream_handler=True, file_handler=True,
                 file_name=f"log_{datetime.now().strftime('%Y-%m-%d_%H%M')}.txt"):
        """
        Logger class used to define all the logging parameters and print log messages.

        :param module: Name or path of the script that calls the logger.
        :param log_level: The minimal log level that is displayed during the run.
        :param color_scheme: The color scheme to be used. False=Black, True=White.
        :param format_string: The log message format rubric (default: time - log_level - log_message).
        :param format_time: The log message format rubric for the time part.
        :param masked_patterns: Any regular expressions that need to be filtered form the logs.
        :param stream_handler: Boolean determining whether the log messages are displayed in the terminal output.
        :param file_handler: Boolean determining whether the log messages are written to a log file.
        Note - If both file_handler and stream_handler are set to False then the logger won't do anything besides
        accumulate all log messages to a string.
        :param file_name: The name of the log file. Relevant only if file_handler=True

        Usage examples:
        1) Simple use where the developer only wants to print a message,
        log = Logger()
        log.debug("TEST")
        >> 15:35:31 - DEBUG - TEST

        2) When the developer wants the user to see only high severity log messages,
        import logging
        log = Logger(log_level=logging.WARNING)
        log.debug("Debug message")
        log.warning("Warning message")
        >> 15:35:31 - WARNING - Warning message

        3) When the developer prefers to tone down some information as part of the rubric presented to the user, for
        instance, reduce the rubric to time and message only (exclude the log level),
        log = Logger(format_string="%(asctime)s - %(message)s")
        log.debug("TEST")
        >> 15:35:31 - TEST

        4) When the developer prefers a different time format, for instance, reduce the time to hours and minutes only
        (exclude the seconds),
        log = Logger(format_time="%H:%M")
        log.debug("TEST")
        >> 15:35 - DEBUG - TEST

        5) When there are re-occurring instances in the log messages (could be some prefix that runs in the background
        of SSH commands) and it needs to be filtered to avoid log flooding,
        log = Logger(masked_patterns=[(r'TEST')])
        log.debug("TEST")  # Filtered due to matching the masked pattern.
        log.debug("TEST2")
        >> 15:35:31 - DEBUG - TEST2

        Example for a combined usage of all the above:
        import logging
        log = Logger(log_level=logging.WARNING, format_string="%(asctime)s - %(message)s", format_time="%H:%M",
                masked_patterns=(r'Error message'))
        log.debug("Debug message")  # Filtered due to being below set log level.
        log.warning("Warning message")
        log.error("Error message")  # Filtered due to matching the masked pattern.
        log.critical("Critical message")
        >> 15:35 - Warning message
        >> 15:35 - Critical message
        """

        # Set class parameters.
        self.module = module
        self.log_level = log_level
        self.color_scheme = color_scheme
        self.format_string = format_string
        self.format_time = format_time
        self.stream_handler = stream_handler
        self.file_handler = file_handler
        self.file_name = file_name

        # Note - The accumulator saves log messages that are also below the set log level (which is fine as it is used
        # for internal purposes).
        self.accumulated_log = ""

        # Create logger object.
        self._logger = logging.getLogger(self.module)
        self._logger.setLevel(logging.DEBUG)

        # Create formatter.
        self._formatter = logging.Formatter(self.format_string, self.format_time)

        # Add handler to logger.
        if self.stream_handler:
            self.__add_stream_handler()
        if self.file_handler:
            self.__add_file_handler()

        # Add a filter to the logger.
        self._masked_patterns = masked_patterns
        self._logger.addFilter(MaskedFilter(masked_patterns))

    def __add_stream_handler(self):
        """Create console handler."""
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setLevel(self.log_level)
        # Set color formatter to the handler.
        stream_handler.setFormatter(ColorFormatter(self.format_string, self.color_scheme, self.format_time))
        self._logger.addHandler(stream_handler)

    def __add_file_handler(self):
        """Create file handler."""
        file_handler = logging.FileHandler(filename=self.file_name, mode="a", encoding=None, delay=False, errors=None)
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(self._formatter)  # Set formatter to the handler.
        self._logger.addHandler(file_handler)

    def debug(self, message: str):
        """Log debug level message."""
        self._logger.debug(message)
        self.accumulated_log += f"{message}\n"

    def info(self, message: str):
        """Log info level message."""
        self._logger.info(message)
        self.accumulated_log += f"{message}\n"

    def warning(self, message: str):
        """Log warning level message."""
        self._logger.warning(message)
        self.accumulated_log += f"{message}\n"

    def error(self, message: str):
        """Log error level message."""
        self._logger.error(message)
        self.accumulated_log += f"{message}\n"

    def critical(self, message: str):
        """Log critical level message."""
        self._logger.critical(message)
        self.accumulated_log += f"{message}\n"

    def raise_exception(self, message: str, exception: Exception):
        """Log critical level message and raise an exception."""
        self._logger.critical(message)
        self.accumulated_log += f"{message}\n"
        raise exception

    def exit(self, message: str, code: int):
        """Log critical level message and exit the program."""
        self._logger.critical(message)
        self.accumulated_log += f"{message}\n"
        exit(code=code)

    def print_data(self, data: str | list | dict, log_level="debug"):
        """
        Print relatively large data to logs.
        Note - Normally, the data comes from a document or terminal output, therefore, it is a list of strings with '\n'
        at the end of the line. In order to avoid empty lines in the logs, the '\n' character is removed.

        :param data: Data to be logged.
        :param log_level: The log level of the data to be logged.
        """

        if isinstance(data, list):
            for line in data:
                getattr(self._logger, log_level)(line.strip())
        if isinstance(data, dict):
            for key, value in data.items():
                getattr(self._logger, log_level)(f"{key} - {value}")
        if isinstance(data, str):
            lines = data.split("\n")
            for line in lines:
                getattr(self._logger, log_level)(f"{line}")


class ColorFormatter(logging.Formatter):
    """This class provides more coloring options other than the default."""
    def __init__(self, format_string, color_scheme, format_time):
        super().__init__()

        self._format_time = format_time
        self._color_scheme = color_scheme
        """
        ANSI escape codes for 8-color, 16-color and 256-color terminals may be found in,
        https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html.
        """
        debug_color = "\u001b[36m" if color_scheme else "\x1b[38;21m"  # Cyan/Grey.
        info_color = "\u001b[30m" if color_scheme else "\x1b[38;5;39m"  # Black/Blue.
        warning_color = "\u001b[33;1m" if color_scheme else "\x1b[38;5;226m"  # Bright Yellow/Yellow.
        error_color = "\x1b[38;5;196m"  # Red.
        critical_color = "\x1b[31;1m"  # Bold red.
        reset_color = "\x1b[0m"

        self._format_string = format_string
        self._FORMATS = {
            logging.DEBUG: debug_color + self._format_string + reset_color,
            logging.INFO: info_color + self._format_string + reset_color,
            logging.WARNING: warning_color + self._format_string + reset_color,
            logging.ERROR: error_color + self._format_string + reset_color,
            logging.CRITICAL: critical_color + self._format_string + reset_color
        }

    def format(self, record):
        log_fmt = self._FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, self._format_time)
        return formatter.format(record)
