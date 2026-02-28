"""
Script Name - api_utilities.py

Purpose - Shared utility functions for all NASA API clients (HTTP GET requests, image downloading, display).

Created by Michael Samelsohn, 07/05/22.
"""

# Imports #
import os
import requests

from PIL import Image
from NASA_API.Settings.api_settings import log, MAX_RETRIES, RETRY_DELAY, REQUEST_TIMEOUT, API_IMAGE_DOWNLOAD_FORMATS
from Utilities.decorators import retry


@retry(max_attempts=MAX_RETRIES, delay=RETRY_DELAY,
       exceptions=(requests.exceptions.Timeout, requests.exceptions.ConnectionError),
       default=None)
def get_request(url: str) -> dict | None:
    """
    Perform an HTTP GET request and return the parsed JSON response.

    Transient network failures (timeouts, connection errors) are retried automatically
    up to MAX_RETRIES times with a RETRY_DELAY second pause between attempts.
    Any other request error or a non-200 status code returns None immediately.

    :param url: The full URL for the GET request.

    :return: Response JSON as a dictionary, or None if the request failed.
    """

    log.debug(f"Performing GET request - {url}")

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        raise  # propagate to @retry
    except requests.exceptions.RequestException as e:
        log.error(f"Unexpected error during GET request - {e}")
        return None

    if response.status_code != 200:
        log.error(f"Request failed with status code - {response.status_code}")
        return None

    log.success("Request successful (status code - 200)")
    return response.json()


@retry(max_attempts=MAX_RETRIES, delay=RETRY_DELAY,
       exceptions=(requests.exceptions.RequestException,),
       default=None)
def _download_single_image(url: str, image_path: str) -> str:
    """
    Download one image URL and write it to disk, raising on any failure.

    Raises ``requests.exceptions.HTTPError`` for non-200 responses so that
    @retry treats them the same as network errors and retries them.

    :param url:        Source URL of the image.
    :param image_path: Absolute path where the image file will be saved.
    :return:           ``image_path`` on success.
    """

    response = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        raise requests.exceptions.HTTPError(
            f"Download failed with status code {response.status_code} - {url}")

    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    with open(image_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

    log.success(f"Image saved successfully - {image_path}")
    return image_path


def download_image_url(image_directory: str, api_type: str, image_url_list: list, image_suffix: str = "") -> str | None:
    """
    Download images from a list of URLs and save them to the specified directory.

    Each URL is attempted up to MAX_RETRIES times (via @retry on the private
    helper).  When downloading a single image the filename is:
        {api_type}{image_suffix}.{format}
    When downloading multiple images each filename receives an additional index:
        {api_type}{image_suffix}_{index}.{format}

    :param image_directory: Directory where downloaded images will be saved.
    :param api_type: API identifier used to determine filename and format (e.g., 'APOD', 'MARS').
    :param image_url_list: List of image URLs to download.
    :param image_suffix: Optional suffix appended to the base filename (e.g., '_2025-01-01').

    :return: Path to the last successfully downloaded image, or None if all downloads fail.
    """

    log.debug("Checking if the image URL list is empty")
    if not image_url_list:
        log.error("No image URLs provided for download")
        return None

    image_format = API_IMAGE_DOWNLOAD_FORMATS[api_type]
    multiple = len(image_url_list) > 1
    image_path = None

    for image_index, url in enumerate(image_url_list, start=1):
        log.debug(f"Processing image {image_index}/{len(image_url_list)} - {url}")

        index_suffix = f"_{image_index}" if multiple else ""
        filename = f"{api_type}{image_suffix}{index_suffix}.{image_format}"
        image_path = _download_single_image(
            url=url,
            image_path=os.path.join(image_directory, filename))

    return image_path


def display_image(image_path: str):
    """
    Open and display a downloaded image using the system's default image viewer.

    :param image_path: Absolute path to the image file.
    """

    if not image_path:
        log.error("No image path provided")
        return

    if not os.path.exists(image_path):
        log.error(f"Image file not found - {image_path}")
        return

    log.debug(f"Displaying image - {image_path}")
    img = Image.open(image_path)
    img.show()