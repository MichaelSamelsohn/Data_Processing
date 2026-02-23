"""
Script Name - api_utilities.py

Purpose - Shared utility functions for all NASA API clients (HTTP GET requests, image downloading, display).

Created by Michael Samelsohn, 07/05/22.
"""

# Imports #
import os
import time
import requests

from PIL import Image
from NASA_API.Settings.api_settings import log, MAX_RETRIES, RETRY_DELAY, REQUEST_TIMEOUT, API_IMAGE_DOWNLOAD_FORMATS


def get_request(url: str) -> dict | None:
    """
    Perform an HTTP GET request and return the parsed JSON response.

    :param url: The full URL for the GET request.

    :return: Response JSON as a dictionary, or None if the request failed.
    """

    log.debug(f"Performing GET request - {url}")

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        log.error(f"Request timed out after {REQUEST_TIMEOUT} seconds - {url}")
        return None
    except requests.exceptions.ConnectionError as e:
        log.error(f"Connection error during GET request - {e}")
        return None
    except requests.exceptions.RequestException as e:
        log.error(f"Unexpected error during GET request - {e}")
        return None

    if response.status_code != 200:
        log.error(f"Request failed with status code - {response.status_code}")
        return None

    log.success("Request successful (status code - 200)")
    return response.json()


def download_image_url(image_directory: str, api_type: str, image_url_list: list, image_suffix: str = "") -> str | None:
    """
    Download images from a list of URLs and save them to the specified directory.

    When downloading a single image the filename is: {api_type}{image_suffix}.{format}.
    When downloading multiple images each filename receives an additional numeric index:
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

        # Build the output filename (add index suffix when downloading multiple images).
        index_suffix = f"_{image_index}" if multiple else ""
        filename = f"{api_type}{image_suffix}{index_suffix}.{image_format}"
        image_path = os.path.join(image_directory, filename)

        # Attempt download with retries.
        download_succeeded = False
        for attempt in range(1, MAX_RETRIES + 1):
            log.debug(f"Download attempt {attempt}/{MAX_RETRIES}")
            try:
                response = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    os.makedirs(image_directory, exist_ok=True)
                    with open(image_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file.write(chunk)
                    log.success(f"Image saved successfully - {image_path}")
                    download_succeeded = True
                    break
                else:
                    log.error(f"Download failed with status code - {response.status_code}")
            except requests.exceptions.Timeout:
                log.error(f"Download timed out (attempt {attempt}/{MAX_RETRIES})")
            except requests.exceptions.RequestException as e:
                log.error(f"Network error during download - {e}")

            if attempt < MAX_RETRIES:
                log.debug(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                log.error(f"Failed to download image after {MAX_RETRIES} attempts - {url}")

        if not download_succeeded:
            image_path = None

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