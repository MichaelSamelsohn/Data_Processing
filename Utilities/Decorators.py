# Imports #
import time
import requests
import os

from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


def check_connection(func):
    def inner(*args, **kwargs):
        try:
            log.debug("Checking connection")
            request = requests.get(Settings.CONNECTION_CHECK_URL, timeout=Settings.CONNECTION_CHECK_TIMEOUT)
            log.info("Connection found")
        except (requests.ConnectionError, requests.Timeout):
            log.error("No internet connection")
            return False
        return func(*args, **kwargs)
    return inner


def measure_runtime(func):
    def inner(*args, **kwargs):
        log.debug(f"Beginning time measurement for method - {func.__name__}")
        start_time = time.time()
        result = func(*args, **kwargs)
        log.info(f"The runtime of the function, {func.__name__}, is - {round(time.time() - start_time, 3)} seconds")
        return result
    return inner


def book_implementation(book, reference):
    def wrapper(func):
        def inner(*args, **kwargs):
            log.info(f"The following method is referenced from the book - {book}")
            log.info(f"Reference for the implementation - {reference}")
            return func(*args, **kwargs)
        return inner
    return wrapper
