"""
Script Name - Logging.py

Purpose - Logs provide valuable information/indication about the running process:
The different log levels are:
DEBUG - Detailed information, typically of interest only when diagnosing problems.
INFO - Confirmation that things are working as expected.
WARNING - An indication that something unexpected happened, or indicative of some problem in the near future (e.g.
'disk space low'). The software continues to work.
ERROR - Due to a more serious issue, the software has not been able to perform some function.
CRITICAL - A serious error, indicating that the program itself may be unable to continue running.

Logger:
Logger objects have a threefold job. First, they expose several methods to application code so that applications can log
messages at runtime. Second, logger objects determine which log messages to act upon based upon severity (the default
filtering facility) or filter objects. Third, logger objects pass along relevant log messages to all interested log
handlers.

Handler:
Handler objects are responsible for dispatching the appropriate log messages (based on the log messages’ severity) to
the handler’s specified destination. Logger objects can add zero or more handler objects to themselves with an
addHandler() method. As an example scenario, an application may want to send all log messages to a log file, all log
messages of error or higher to stdout, and all messages of critical to an email address. This scenario requires three
individual handlers where each handler is responsible for sending messages of a specific severity to a specific
location.

Formatter:
Formatter objects configure the final order, structure, and contents of the log message. Unlike the base logging.Handler
class, application code may instantiate formatter classes, although you could likely subclass the formatter if your
application needs special behavior. The constructor takes three optional arguments – a message format string, a date
format string and a style indicator.

Created by Michael Samelsohn, 05/05/22
"""

# Imports #
import logging
import sys

# Constants #
DEBUG_COLOR = "\x1b[38;21m"  # Grey.
INFO_COLOR = "\x1b[38;5;39m"  # Blue.
WARNING_COLOR = "\x1b[38;5;226m"  # Yellow.
ERROR_COLOR = "\x1b[38;5;196m"  # Red.
CRITICAL_COLOR = "\x1b[31;1m"  # Bold red.
RESET = "\x1b[0m"


class Logger:
    def __init__(self, module, file_name, log_level=logging.DEBUG, format_string="%(asctime)s - %(levelname)s - %(name)s - %(message)s"):
        # Set class parameters.
        self.__module = module
        self.__file_name = file_name
        self.__log_level = log_level
        self.__format_string = format_string

        # Create logger object.
        self.__logger = logging.getLogger(name=self.__module)
        self.__logger.setLevel(level=logging.DEBUG)

        # Create formatter.
        self.__formatter = logging.Formatter(format_string)

        # Add handler to logger.
        self.__add_stream_handler()

    def __add_stream_handler(self):
        # Create console handler and set level according to specified value.
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setLevel(level=self.__log_level)
        stream_handler.setFormatter(ColorFormatter(self.__format_string))
        self.__logger.addHandler(stream_handler)

    def __add_file_handler(self):
        # Create file handler and set level according to specified value.
        file_handler = logging.FileHandler(filename=self.__file_name, mode="w")
        file_handler.setLevel(self.__log_level)
        file_handler.setFormatter(self.__formatter)
        self.__logger.addHandler(file_handler)

    def debug(self, message):
        self.__logger.debug(message)

    def info(self, message):
        self.__logger.info(message)

    def warning(self, message):
        self.__logger.warning(message)

    def error(self, message):
        self.__logger.error(message)

    def critical(self, message):
        self.__logger.critical(message)

    def raise_exception(self, message, exception):
        self.__logger.critical(message)
        raise exception(message)

    def exit(self, message, code):
        self.__logger.critical(message)
        exit(code=code)

    def print_data(self, data):
        """
        Log relatively large data.
        Note - Normally, the data comes from a document or terminal output, therefore, it is a list of strings with '\n'
        at the end of the line. In order to avoid empty spaces in the log, the '\n' character is removed.

        :param data: The data to be printed.
        """

        if isinstance(data, list):
            for line in data:
                self.__logger.debug(line.replace("\n", ""))
        if isinstance(data, dict):
            for key, value in data.items():
                self.__logger.debug(f"{key} - {value}")


class ColorFormatter(logging.Formatter):
    def __init__(self, format_string):
        super().__init__()
        self.__format_string = format_string
        self.__FORMATS = {
            logging.DEBUG: DEBUG_COLOR + self.__format_string + RESET,
            logging.INFO: INFO_COLOR + self.__format_string + RESET,
            logging.WARNING: WARNING_COLOR + self.__format_string + RESET,
            logging.ERROR: ERROR_COLOR + self.__format_string + RESET,
            logging.CRITICAL: CRITICAL_COLOR + self.__format_string + RESET,
        }

    def format(self, record):
        log_format = self.__FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_format)
        return formatter.format(record=record)
