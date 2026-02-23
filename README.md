# Data Processing

A multi-domain Python project covering digital image processing, NASA API integration, IEEE 802.11 WiFi simulation, and shared utilities. Each module is self-contained with its own settings, source, tests, and documentation.

---

## Modules

| Module | Description | Documentation |
|---|---|---|
| [Image_Processing](Image_Processing/) | Classical digital image processing algorithms (intensity, filtering, segmentation, morphology, thinning) | [README](Image_Processing/README.md) |
| [NASA_API](NASA_API/) | Client for APOD, EPIC, Mars Rover Photos, and NASA Image Library APIs | [README](NASA_API/README.md) |
| [WiFi](WiFi/) | Full IEEE 802.11 PHY + MAC simulation over TCP sockets | [README](WiFi/README.md) |
| [Utilities](Utilities/) | Shared Logger, decorators, and Email class used across all modules | [README](Utilities/README.md) |

---

## Quick Start

### Image Processing
```python
from Image_Processing.Source.Basic.image import Image

image = Image(image_path="Image_Processing/Images/Lena.png")
image.convert_to_grayscale()
image.negative()
image.display_all_images()
```

### NASA API
```python
from NASA_API.Source.apod import APOD

apod = APOD(image_directory="NASA_API/Images")
apod.date = "2025-04-15"
apod.hd = True
apod.astronomy_picture_of_the_day()
```

### WiFi Simulation
```python
from WiFi.Source.channel import Channel
from WiFi.Source.chip import CHIP

channel = Channel(channel_response=[1], snr_db=25)
ap = CHIP(role="AP", identifier="MyNetwork")
sta = CHIP(role="STA", identifier="MyNetwork")
ap.activation()
sta.activation()
```

### Utilities
```python
from Utilities.logger import Logger
from Utilities.decorators import measure_runtime, book_reference

log = Logger(name="my_module")
log.info("Processing started")
```

---

## Author

Created by Michael Samelsohn (2022–present).