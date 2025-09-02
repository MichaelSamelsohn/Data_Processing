# Imports #

from NASA_API.Settings.api_settings import log
from NASA_API.Source.api_utilities import display_image
from NASA_API.Source.apod import APOD
from NASA_API.Source.epic import EPIC

log.info("APOD - Astronomy Picture Of the Day")
apod = APOD()
apod.date = "1999-04-27"
apod.astronomy_picture_of_the_day()
display_image(image_path=apod.apod_image)

log.info("EPIC - Earth Polychromatic Imaging Camera")
epic = EPIC()
epic.earth_polychromatic_imaging_camera()
display_image(image_path=epic.epic_image)