# Imports #
from NASA_API.Source.apod import APOD

# APOD - Astronomy Picture Of the Day.
apod = APOD()
apod.date = "1999-04-27"
apod.astronomy_picture_of_the_day()
apod.display_image()
