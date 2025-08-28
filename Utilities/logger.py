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
    This class provides an option to mask selected regular expressions.
    Especially useful for removing constant prefixes/suffixes or obfuscating passwords.
    """
    def __init__(self, masked_patterns: list):
        """
        Initialize the filtering class.

        :param masked_patterns: List of tuples. The tuple is constructed of the following values:
            1) The pattern (regular expression) for masking.
            2) The mask (string).
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


class Logger(logging.Logger):
    def __init__(self, log_level=logging.DEBUG, color_scheme=False,
                 format_string="%(asctime)s - %(levelname)s (%(module)s:%(funcName)s:%(lineno)d) - %(message)s",
                 format_time="%H:%M:%S", masked_patterns=None, stream_handler=True,
                 file_handler=False, file_name=f"log_{datetime.now().strftime('%Y-%m-%d_%H%M')}.txt",
                 level_name_only=True):
        """
        Logger class used to define all the logging parameters and print log messages.

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
        :param level_name_only: Boolean indicating whether the entire line is colored (False) or only the level name
        (True).

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
        log = Logger(masked_patterns=[(r'TEST', 'MASK')])
        log.debug("TEST")  # Masked due to matching the pattern.
        log.debug("TEST2")
        >> 15:35:31 - DEBUG - MASK
        >> 15:35:31 - DEBUG - TEST2

        Example for a combined usage of all the above:
        import logging
        log = Logger(log_level=logging.WARNING, format_string="%(asctime)s - %(message)s", format_time="%H:%M",
                masked_patterns=(r'Error message', 'Error mask'))
        log.debug("Debug message")  # Filtered due to being below set log level.
        log.warning("Warning message")
        log.error("Error message")  # Masked due to matching the pattern.
        log.critical("Critical message")
        >> 15:35 - Warning message
        >> 15:35 - Error mask
        >> 15:35 - Critical message
        """

        # Super call.
        super().__init__(name="Logger")

        # Set class parameters.
        self._log_level = log_level
        self._color_scheme = color_scheme
        self._format_string = format_string
        self._format_time = format_time
        self._stream_handler = stream_handler
        self._file_handler = file_handler
        self._file_name = file_name
        self._level_name_only = level_name_only
        self._custom_colors = {}  # Track custom log levels and their colors

        # Set formatter.
        self._formatter = logging.Formatter(self._format_string, self._format_time)

        # Adding the handlers.
        self.__set_handlers()

        # Add a filter to the logger.
        self._masked_patterns = masked_patterns
        self.addFilter(MaskedFilter(self._masked_patterns))

    @property
    def log_level(self): return self._log_level

    @log_level.setter
    def log_level(self, log_level: int):
        """
        Set the log level of the logger.
        :param log_level: Determines the log level (levels below the one set won't be added to the log).
        This is an integer value according to the native Python logger definitions:
            * CRITICAL = 50
            * ERROR = 40
            * WARNING = 30
            * INFO = 20
            * DEBUG = 10
        """

        self._log_level = log_level
        self.__set_handlers()

    @property
    def color_scheme(self): return self._color_scheme

    @color_scheme.setter
    def color_scheme(self, color_scheme: bool):
        """
        Set the color scheme of the logger.
        :param color_scheme: The color scheme used for the stream handler. The color schemes are adjusted for viewing on
        different Pycharm IDE settings:
        False=Black ("Dracula") IDE setting, True=White standard IDE setting.
        """

        self._color_scheme = color_scheme
        self.__set_handlers()

    @property
    def stream_handler(self): return self._stream_handler

    @stream_handler.setter
    def stream_handler(self, stream_handler: bool):
        """
        Decide on the status of the stream handler.
        :param stream_handler: Boolean value determining whether the log output is printed to the terminal.
        """

        self._stream_handler = stream_handler
        self.__set_handlers()

    @property
    def file_handler(self): return self._file_handler

    @file_handler.setter
    def file_handler(self, file_handler: bool):
        """
        Decide on the status of the file handler.
        :param file_handler: Boolean value determining whether the log output is printed to the log file.
        """

        self._file_handler = file_handler
        self.__set_handlers()

    @property
    def file_name(self): return self._file_name

    @file_name.setter
    def file_name(self, file_name: bool):
        """
        Set the logger file name.
        Note - Relevant only if file handler is added.
        :param file_name: Name of the log file.
        """

        self._file_name = file_name
        self.__set_handlers()

    @property
    def format_string(self): return self._format_string

    @format_string.setter
    def format_string(self, format_string: str):
        """
        Set the format string of the logger. This attribute defines the rubric of the print. Here is an overview of the
        basic rubric:
        %(asctime)s - The time of the log message. Can be further modified by the format_time attribute.
        %(levelname)s - The log level of the message.
        %(message)s - The message itself.
        :param format_string: The format string rubric of the logger.
        """

        self._format_string = format_string
        self._formatter = logging.Formatter(self._format_string, self._format_time)
        self.__set_handlers()

    @property
    def format_time(self): return self._format_time

    @format_time.setter
    def format_time(self, format_time: str):
        """
        Set the format time of the logger. See usage examples of non-default options in the __init__ docstring.
        Note - Relevant only if %(asctime)s is defined in the format_string attribute.
        :param format_time: The time rubric of the logger.
        """

        self._format_time = format_time
        self._formatter = logging.Formatter(self._format_string, self._format_time)
        self.__set_handlers()

    @property
    def masked_patterns(self): return self._masked_patterns

    @masked_patterns.setter
    def masked_patterns(self, masked_patterns: list):
        self._masked_patterns = masked_patterns

        # Reset the masked patterns.
        self.filters.clear()

        # Add a filter to the logger.
        self.addFilter(MaskedFilter(self._masked_patterns))

    @property
    def level_name_only(self):
        return self._level_name_only

    @level_name_only.setter
    def level_name_only(self, level_name_only: bool):
        self._level_name_only = level_name_only
        self.__set_handlers()

    def __set_handlers(self):
        """
        Method for setting the handlers. The two available handlers are file and stream.
        This version ensures that custom log level colors persist across handler resets.
        """

        # Clear existing handlers
        self.handlers.clear()

        # Add stream handler if enabled
        if self._stream_handler:
            stdout_stream_handler = logging.StreamHandler(stream=sys.stdout)
            stdout_stream_handler.setLevel(self._log_level)

            # Create color formatter
            color_formatter = ColorFormatter(
                format_string=self._format_string,
                color_scheme=self._color_scheme,
                format_time=self._format_time,
                level_name_only=self._level_name_only
            )

            # Reapply custom log level colors
            if hasattr(self, "_custom_colors"):
                for level_num, color in self._custom_colors.items():
                    color_formatter._COLORS[level_num] = color

            # Set formatter
            stdout_stream_handler.setFormatter(color_formatter)

            # Add handler
            self.addHandler(stdout_stream_handler)

        # Add file handler if enabled
        if self._file_handler:
            file_handler = logging.FileHandler(
                filename=self._file_name, mode="a", encoding=None, delay=False, errors=None
            )
            file_handler.setLevel(self._log_level)

            # Use plain (non-colored) formatter for file logging
            file_formatter = logging.Formatter(self._format_string, self._format_time)
            file_handler.setFormatter(file_formatter)

            # Add handler
            self.addHandler(file_handler)

    def add_custom_log_level(self, level_name: str, level_num: int, color: str = None):
        level_name = level_name.upper()

        # Check for conflicts
        if hasattr(logging, level_name):
            raise ValueError(f"Log level '{level_name}' already exists.")
        if level_num in logging._levelToName:
            raise ValueError(f"Log level number '{level_num}' already exists.")

        # Add to logging module
        logging.addLevelName(level_num, level_name)
        setattr(logging, level_name, level_num)

        # Define log method with correct stacklevel
        def log_for_level(self, message, *args, **kwargs):
            self._log(level_num, message, args, stacklevel=2, **kwargs)

        setattr(self.__class__, level_name.lower(), log_for_level)

        # Store custom color
        if color:
            self._custom_colors[level_num] = color

        # Add color to all formatters
        for handler in self.handlers:
            formatter = handler.formatter
            if isinstance(formatter, ColorFormatter) and color:
                formatter._COLORS[level_num] = color

    def exit(self, message: str, exit_code=1):
        """Log critical level message and end program execution."""
        self.critical(message)
        exit(exit_code)

    def print_data(self, data: int | float | str | list | dict, log_level="debug"):
        """
        Print relatively large data to logs.
        Note - Normally, the data comes from a document or terminal output, therefore, it is a list of strings with '\n'
        at the end of the line. In order to avoid empty lines in the logs, the '\n' character is removed.

        :param data: Data to be logged.
        :param log_level: The log level of the data to be logged.
        """

        if isinstance(data, list):
            for line in data:
                getattr(self, log_level)(str(line).strip())
        if isinstance(data, dict):
            for key, value in data.items():
                getattr(self, log_level)(f"{key} - {value}")
        if isinstance(data, str):
            lines = data.split("\n")
            for line in lines:
                getattr(self, log_level)(f"{line}")
        if isinstance(data, int | float):
            getattr(self, log_level)(f"{data}")


class ColorFormatter(logging.Formatter):
    """This class provides more coloring options other than the default."""
    def __init__(self, format_string: str, color_scheme: bool, format_time: str, level_name_only: bool):
        """
        TODO: Complete the docstring.
        """

        super().__init__(format_string, format_time)

        self._format_string = format_string
        self._format_time = format_time
        self._color_scheme = color_scheme
        self._level_name_only = level_name_only
        """
        ANSI escape codes for 8-color, 16-color and 256-color terminals may be found in,
        https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html.
        """
        self._COLORS = {
            logging.DEBUG: "\u001b[36m" if self._color_scheme else "\x1b[38;21m",         # Cyan/Grey.
            logging.INFO: "\u001b[30m" if self._color_scheme else "\x1b[38;5;39m",        # Black/Blue.
            logging.WARNING: "\u001b[33;1m" if self._color_scheme else "\x1b[38;5;226m",  # Bright Yellow/Yellow.
            logging.ERROR: "\x1b[38;5;196m",                                              # Red.
            logging.CRITICAL: "\x1b[31;1m",                                               # Bold red.
        }
        self._RESET_COLOR = "\x1b[0m"

    def format(self, record):
        """
        Format the message for the log. There are two supported modes:
        1) Level name is the only colored part of the message.
        2) The whole line is colored.
        """

        if self._level_name_only:
            log_color = self._COLORS.get(record.levelno)
            record.levelname = f"{log_color}{record.levelname}{self._RESET_COLOR}"
            return super().format(record)
        else:
            log_color = self._COLORS.get(record.levelno)
            log_fmt = log_color + self._format_string + self._RESET_COLOR
            formatter = logging.Formatter(log_fmt, self._format_time)
            return formatter.format(record)
