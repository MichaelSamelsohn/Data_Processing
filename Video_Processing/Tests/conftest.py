# Imports #
import sys
from pathlib import Path

# Add the Advanced source directory to sys.path so that bare imports inside
# Image_Processing source files (e.g. "from spatial_filtering import ...") resolve
# correctly during test collection.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'Image_Processing' / 'Source' / 'Advanced'))
