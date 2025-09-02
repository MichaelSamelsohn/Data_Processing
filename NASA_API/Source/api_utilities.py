"""
Script Name - NASA_API.py

Purpose - Super class for smaller NASA API requests.

Created by Michael Samelsohn, 07/05/22.
"""

# Imports #
import subprocess
import time
import requests

from PIL import Image
from NASA_API.Settings.api_settings import *


def get_request(url: str) -> dict | None:
    """
    Use API GET request with the specified URL.

    :param url: The URL used for the API GET request.
    :return: The response JSON in form of a dictionary.
    """

    log.debug(f"Requesting a GET API with the following URL - {url}")

    request = requests.get(url)
    if request.status_code != 200:
        log.error(f"Request failed with status code - {request.status_code}")
        return None
    log.success("Request is successful (status code - 200)")

    return request.json()


def download_image_url(image_directory: str, api_type: str, image_url_list: list, image_suffix="") -> str | None:
    """
    Download the images based on the compiled URLs list and the API type.

    :param image_directory: Path to the directory where the images are saved to.
    :param api_type: The API type used for the images.
    :param image_url_list: List with all image URLs.
    :param image_suffix: The suffix for the image name.

    :return: True if download is successful, otherwise False.
    """

    log.debug("Check if the image URL list is empty")
    if len(image_url_list) == 0:
        log.error("No images for download")
        return None

    image_path = None
    image_index = 1
    for url in image_url_list:
        # Preparing image path.
        image_path = os.path.join(image_directory, f"{api_type}{image_suffix}.{API_IMAGE_DOWNLOAD_FORMATS[api_type]}")

        # Trying to download the image(s) with retries.
        for attempt in range(MAX_RETRIES):
            log.debug(f"Attempting to download image {image_index} from URL - "
                      f"{url} (attempt {attempt + 1}/{MAX_RETRIES})")

            # Running the curl command to download the image.
            output = subprocess.run(f"curl -o {image_path} {url}", capture_output=True, text=True)

            # Checking if the download was successful (curl return code is 0).
            if output.returncode == 0:
                # Verifying the image was downloaded (check if the file exists).
                if os.path.exists(image_path):
                    log.success(f"Image downloaded successfully - {image_path}")
                    break
                else:
                    log.error(f"Image download failed - {image_path} (file not found after download)")
            else:
                # If curl failed, logging the error and retrying.
                log.error(f"Error downloading image, curl returned {output.returncode}")
                log.print_data(data=output.stderr, log_level="error")

                if attempt < MAX_RETRIES - 1:
                    log.debug(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)  # Buffer time before retrying.
                else:
                    log.error(f"Failed to download image after {MAX_RETRIES} attempts, moving to next image")

        image_index += 1  # Incrementing the index for the next image.

    return image_path


def display_image(image_path: str):
    """
    Display the most recently downloaded image using the default image viewer.

    This method checks if there is a downloaded image stored in the `_latest_image` attribute.
    If an image is available, it opens and displays the image using the system's default image viewer.
    """

    # Checking if there is a downloaded image.
    if image_path:
        log.debug("Displaying the latest downloaded image")
        img = Image.open(image_path)
        img.show()
    else:
        log.error("No image to display")