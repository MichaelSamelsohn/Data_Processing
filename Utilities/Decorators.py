# Imports #
import requests
import os

from Common import scale_image
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


def book_implementation(book, reference):
    def wrapper(func):
        def inner(*args, **kwargs):
            log.info(f"The following method is referenced from the book - {book}")
            log.info(f"Reference for the implementation - {reference}")
            return func(*args, **kwargs)
        return inner
    return wrapper


def scale_pixel_values(scale_factor=Settings.DEFAULT_SCALING_FACTOR):
    def wrapper(func):
        def inner(*args, **kwargs):
            log.debug(f"Scaling image by a factor of {scale_factor}")
            kwargs["image"] = scale_image(image=kwargs["image"], scale_factor=scale_factor)
            return_image = func(*args, **kwargs)
            log.debug("Scaling image back")
            return scale_image(image=return_image, scale_factor=1/scale_factor)
        return inner
    return wrapper



