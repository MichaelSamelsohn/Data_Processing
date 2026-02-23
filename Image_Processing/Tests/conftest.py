# Imports #
import sys
from pathlib import Path

# Add the Advanced source directory to sys.path so that segmentation.py's bare import
# "from spatial_filtering import ..." can be resolved during test collection.
sys.path.insert(0, str(Path(__file__).parent.parent / 'Source' / 'Advanced'))