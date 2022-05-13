# Imports #
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
