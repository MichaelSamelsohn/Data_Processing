"""
Script Name - epic.py

Purpose - Download the EPIC (Earth Polychromatic Imaging Camera) image(s).
For full API documentation - https://epic.gsfc.nasa.gov/about/api.

Created by Michael Samelsohn, 07/05/22.
"""

# Imports #
from NASA_API.Settings.api_settings import log, EPIC_URL_PREFIX, EPIC_URL_SUFFIX, DEFAULT_IMAGE_DIRECTORY
from NASA_API.Source.api_utilities import get_request, download_image_url


class EPIC:
    def __init__(self, image_directory=DEFAULT_IMAGE_DIRECTORY):
        log.epic("Initializing the EPIC class")

        self.image_directory = image_directory
        self._epic_image = None

    @property
    def epic_image(self):
        """Get the path of the most recently downloaded EPIC image."""
        return self._epic_image

    def earth_polychromatic_imaging_camera(self, date: str = None) -> bool:
        """
        Download a full-disk Earth image captured by the DSCOVR satellite's EPIC camera.

        :param date: Optional date string in 'YYYY-MM-DD' format. When provided, the first available image
                     from that date is downloaded. When omitted, the most recent available image is used.

        Notes:
        - Images are saved in PNG format.

        :return: True if the image was downloaded successfully, False otherwise.
        """

        log.epic("Retrieving EPIC (Earth Polychromatic Imaging Camera) image")

        # Step (1) - Build the API request URL.
        if date is not None:
            log.epic(f"Querying EPIC images for specific date - {date}")
            url = f"{EPIC_URL_PREFIX}api/natural/date/{date}"
        else:
            log.epic("Querying the most recent available EPIC image")
            url = f"{EPIC_URL_PREFIX}{EPIC_URL_SUFFIX}"

        # Step (2) - Perform the API request.
        json_object = get_request(url=url)
        if json_object is None:
            log.error("API request failed - check logs for details")
            return False

        # Step (3) - Verify the response contains at least one image.
        if not json_object:
            log.error("No EPIC images available for the requested date")
            return False

        # Step (4) - Build the archive URL from the first available image's metadata.
        log.epic("Processing image metadata from the API response")
        image = json_object[0]
        year, month, day = self.reformat_images_url(image["date"])
        image_url = f"{EPIC_URL_PREFIX}archive/natural/{year}/{month}/{day}/png/{image['image']}.png"
        log.epic(f"Resolved archive URL - {image_url}")

        # Step (5) - Download and save the image.
        self._epic_image = download_image_url(
            image_directory=self.image_directory,
            api_type="EPIC",
            image_url_list=[image_url]
        )

        return self._epic_image is not None

    @staticmethod
    def reformat_images_url(image_date: str) -> tuple[str, str, str]:
        """
        Parse an EPIC API date-time string into its year, month, and day components.

        The EPIC API returns dates in 'YYYY-MM-DD HH:MM:SS' format. This method extracts
        the date portion and splits it into individual components required for building
        the archive image URL.

        :param image_date: Date-time string from the EPIC API response (e.g., '2025-01-15 12:34:56').

        :return: Tuple of (year, month, day) strings.
        """

        log.epic("Extracting year, month, and day from EPIC image date string")

        date_part = image_date.split(" ")[0]   # Discard the time component.
        year, month, day = date_part.split("-")
        return year, month, day