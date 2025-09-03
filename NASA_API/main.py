# Imports #

from NASA_API.Settings.api_settings import log
from NASA_API.Source.api_utilities import display_image
from NASA_API.Source.apod import APOD
from NASA_API.Source.epic import EPIC
from NASA_API.Source.mars import MARS
from NASA_API.Source.nil import NIL

log.info("APOD - Astronomy Picture Of the Day")
apod = APOD()
apod.date = "1999-04-27"
apod.astronomy_picture_of_the_day()
display_image(image_path=apod.apod_image)

log.info("EPIC - Earth Polychromatic Imaging Camera")
epic = EPIC()
epic.earth_polychromatic_imaging_camera()
display_image(image_path=epic.epic_image)

log.info("MARS ROVERS")
mars = MARS()
mars.rover = "Curiosity"
mars.date = "2015-04-27"
mars.mars()
# display_image(image_path=mars.mars_image)

log.info("NIL - NASA Image Library")
nil = NIL()
nil.query = "Crab nebula"
nil.search_years = [2000, 2020]
nil.media_type = "image"
nil.nasa_image_library_query()
display_image(image_path=nil.nil_image)