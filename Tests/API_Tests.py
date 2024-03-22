# Imports #
import time
import os
import shutil
import pytest

from APOD import APOD
from EPIC import EPIC
from MARS import MARS
from NIL import NIL
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)

# Constants #
IMAGE_DIRECTORY_PATH = "C:\\Users\\Michael\\PycharmProjects\\Data_Processing\\Tests\\Test_Images"


@pytest.fixture()
def resource():
    """
    Pytest fixture which cleans the contents of the test images directory and asserts it is clean.
    """

    log.debug("Cleaning the test images directory")
    clean_directory_contents(directory_path=IMAGE_DIRECTORY_PATH)
    log.debug("Asserting Test images directory is clean")
    assert not os.listdir(IMAGE_DIRECTORY_PATH)
    log.info("Tests images directory is clean")

    yield


class TestSystem:
    def test_apod(self, resource):
        """
        System test for the APOD class. The test process is as follows:
        1) Download the APOD image using the relevant API.
        2) Assert image was downloaded successfully.

        :return: True if image downloaded successfully, assertion otherwise.
        """

        apod_date = "1996-04-27"
        apod = APOD(image_directory=IMAGE_DIRECTORY_PATH, date=apod_date)
        apod.astronomy_picture_of_the_day()

        time.sleep(1)  # To prevent a race between image download and path confirmation.
        log.debug("Asserting the path of the downloaded image")
        assert os.path.exists(os.path.join(IMAGE_DIRECTORY_PATH, f"APOD_{apod_date}.JPG"))
        log.info("Image downloaded successfully")
        return True

    def test_epic(self, resource):
        """
        System test for the EPIC class. The test process is as follows:
        1) Download the EPIC image using the relevant API.
        2) Assert image was downloaded successfully.

        :return: True if image downloaded successfully, assertion otherwise.
        """

        epic = EPIC(image_directory=IMAGE_DIRECTORY_PATH, number_of_images=1)
        epic.earth_polychromatic_imaging_camera()

        time.sleep(1)  # To prevent a race between image download and path confirmation.
        log.debug("Asserting the path of the downloaded image")
        assert os.path.exists(os.path.join(IMAGE_DIRECTORY_PATH, "EPIC.png"))
        log.info("Image downloaded successfully")
        return True

    def test_mars(self, resource):
        """
        System test for the MARS class. The test process is as follows:
        1) Download the MARS image using the relevant API.
        2) Assert image was downloaded successfully.

        :return: True if image downloaded successfully, assertion otherwise.
        """

        mars = MARS(image_directory=IMAGE_DIRECTORY_PATH, rover="Opportunity", date="2012-01-01", number_of_images=1)
        mars.mars_rover_images()

        time.sleep(1)  # To prevent a race between image download and path confirmation.
        log.debug("Asserting the path of the downloaded image")
        assert os.path.exists(os.path.join(IMAGE_DIRECTORY_PATH, "MARS.JPG"))
        log.info("Image downloaded successfully")
        return True

    def test_nil(self, resource):
        """
        System test for the NIL class. The test process is as follows:
        1) Download the NIL image using the relevant API.
        2) Assert image was downloaded successfully.

        :return: True if image downloaded successfully, assertion otherwise.
        """

        query = "Crab Nebula"
        nil = NIL(image_directory=IMAGE_DIRECTORY_PATH, query=query)
        nil.nasa_image_library_query()

        time.sleep(1)  # To prevent a race between image download and path confirmation.
        log.debug("Asserting the path of the downloaded image")
        assert os.path.exists(os.path.join(IMAGE_DIRECTORY_PATH, f"NIL_{query.replace(' ', '_')}.JPG"))
        log.info("Image downloaded successfully")
        return True


def clean_directory_contents(directory_path: str):
    """
    Clean directory contents.

    :param directory_path: Path of the directory to be cleaned.
    :return: True if no exception occurred.
    """

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            log.error(f"Failed to delete {file_path} due to {e}")
            return False

    return True

