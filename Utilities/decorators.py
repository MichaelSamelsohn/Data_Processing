# Imports #
import time
import requests

from Settings import api_settings
from Settings.settings import log


def check_connection(func):
    def inner(*args, **kwargs):
        try:
            log.debug("Checking connection")
            request = requests.get(api_settings.CONNECTION_CHECK_URL, timeout=api_settings.CONNECTION_CHECK_TIMEOUT)
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


def book_reference(book, reference):
    def wrapper(func):
        def inner(*args, **kwargs):
            log.info(f"The following method is referenced from the book - {book}")
            log.info(f"Reference for the implementation - {reference}")
            return func(*args, **kwargs)
        return inner
    return wrapper


def article_reference(article):
    def wrapper(func):
        def inner(*args, **kwargs):
            log.info(f"The following method is referenced from the article - {article}")
            return func(*args, **kwargs)
        return inner
    return wrapper
