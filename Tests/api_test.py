# Imports #
import time
import shutil
import os
import pytest
import requests

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.options import PageLoadStrategy
from webdriver_manager.chrome import ChromeDriverManager

from apod import APOD
from epic import EPIC
from mars_rovers import MARS
from nil import NIL
from Settings.settings import log

# Constants #
# TODO: Generalize the path.
IMAGE_DIRECTORY_PATH = "C:\\Users\\micha\\PycharmProjects\\Data_Processing\\Tests\\Test_Images"


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


@pytest.fixture()
def driver():
    """
    Pytest fixture which sets and creates a web driver for Selenium-based tests.
    """

    log.debug("Setting the browser options")
    # This option allows the browser to remain open once the script ends.
    options = Options()
    options.add_experimental_option("detach", True)
    options.page_load_strategy = PageLoadStrategy.none  # No need to wait until the page loads completely.

    log.debug("Opening the browser")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # An implicit wait tells WebDriver to poll the DOM for a certain amount of time when trying to find any element (or
    # elements) not immediately available.
    driver.implicitly_wait(5)  # Seconds.
    driver.maximize_window()
    log.info("Browser loaded successfully")

    return driver


class TestSystem:
    def test_apod_functionality(self, resource):
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

    def test_apod_image_correctness(self, resource, driver):
        """
        Purpose of the test is to assert that correct image is downloaded using the APOD class in comparison with the
        downloaded image from the APOD website.
        1) Download APOD image from the relevant website - https://apod.nasa.gov/apod/.
        2) Download APOD image using the REST API.
        3) Compare the downloaded images for bit-exactness.

        :return: True if image downloaded successfully, assertion otherwise.
        """

        downloaded_image_path = os.path.join(IMAGE_DIRECTORY_PATH, "downloaded_image.jpg")

        log.debug("Downloading the image from the web")
        # Loading the APOD home page.
        driver.get("https://apod.nasa.gov/apod/")
        time.sleep(2)  # Buffer time to allow the page to load.
        assert driver.title == "Astronomy Picture of the Day"

        image_element = driver.find_element(By.XPATH, "/html/body/center[1]/p[2]/a/img")
        image_data = requests.get(image_element.get_attribute(name="src")).content
        with open(downloaded_image_path, 'wb') as handler:
            handler.write(image_data)
        log.debug("Closing the browser")
        driver.close()

        log.debug("Downloading the image using the relevant API")
        apod_date = datetime.today().strftime('%Y-%m-%d')
        log.debug(f"Today's date - {apod_date}")
        apod = APOD(image_directory=IMAGE_DIRECTORY_PATH, date=apod_date)
        apod.astronomy_picture_of_the_day()

        log.debug("Comparing the images for bit exactness")
        assert (open(downloaded_image_path, "rb").read() ==
                open(os.path.join(IMAGE_DIRECTORY_PATH, f"APOD_{apod_date}.jpg"), "rb").read()), \
            "Images are not identical"
        log.info("Images are identical")
        return True

    def test_epic(self, resource):
        """
        System test for the EPIC class. The test process is as follows:
        1) Download the EPIC image using the relevant API.
        2) Assert image was downloaded successfully.

        :return: True if image downloaded successfully, assertion otherwise.
        """

        log.debug("Downloading the image using the relevant API")
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

        log.debug("Downloading the image using the relevant API")
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

        log.debug("Downloading the image using the relevant API")
        query = "Crab Nebula"
        nil = NIL(image_directory=IMAGE_DIRECTORY_PATH, query=query)
        nil.nasa_image_library_query()

        time.sleep(1)  # To prevent a race between image download and path confirmation.
        log.debug("Asserting the path of the downloaded image")
        assert os.path.exists(os.path.join(IMAGE_DIRECTORY_PATH, f"NIL_{query.replace(' ', '_')}.JPG"))
        log.info("Image downloaded successfully")
        return True

    def test_nil_image_correctness(self, resource, driver):
        """
        Purpose of the test is to assert that correct image is downloaded using the APOD class in comparison with the
        downloaded image from the APOD website.
        1) Download NIL image ("crab nebula") from the relevant website - https://www.nasa.gov/images/.
        2) Download NIL image ("crab nebula") using the REST API.
        3) Compare the downloaded images for bit-exactness.

        :return: True if image downloaded successfully, assertion otherwise.
        """

        downloaded_image_path = os.path.join(IMAGE_DIRECTORY_PATH, "downloaded_image.jpg")
        query = "Crab Nebula"

        log.debug("Downloading the image from the web")
        # Loading the NIL home page.
        driver.get("https://images.nasa.gov/")
        time.sleep(5)  # Buffer time to allow the page to load.
        assert driver.title == "NASA Image and Video Library"

        (driver.find_element(By.XPATH, "/html/body/app-root/div/div/div/landing/div/header/div/div["
                                       "2]/div/search-form/form/div/input").send_keys(query))
        driver.find_element(By.XPATH, "/html/body/app-root/div/div/div/landing/div/header/div/div["
                                      "2]/div/search-form/form/div/div/button").click()
        time.sleep(5)
        driver.find_element(By.XPATH, "/html/body/app-root/div/div/div/search/div/main/div/div/div/div[2]/div[5]/div["
                                      "1]/ngx-masonry/div[2]/a/div[1]/div").click()
        time.sleep(3)
        driver.find_element(By.XPATH, "/html/body/app-root/div/div/div/detail/div/main/div/div[2]/div[2]/div["
                                      "1]/button/div").click()
        time.sleep(2)
        driver.find_element(By.XPATH, "/html/body/app-root/div/div/div/detail/div/main/div/div[2]/div[2]/div["
                                      "1]/ul/li[1]/a").click()

        driver.switch_to.window(driver.window_handles[1])  # Shift focus to the image tab.
        image_data = requests.get(driver.current_url).content
        with open(downloaded_image_path, 'wb') as handler:
            handler.write(image_data)
        log.debug("Closing the browser")
        driver.close()

        log.debug("Downloading the image using the relevant API")
        nil = NIL(image_directory=IMAGE_DIRECTORY_PATH, query=query)
        nil.nasa_image_library_query()

        log.debug("Comparing the images for bit exactness")
        assert (open(downloaded_image_path, "rb").read() ==
                open(os.path.join(IMAGE_DIRECTORY_PATH, f"NIL_{query.replace(' ', '_')}.JPG"), "rb").read()), \
            "Images are not identical"
        log.info("Images are identical")
        return True
