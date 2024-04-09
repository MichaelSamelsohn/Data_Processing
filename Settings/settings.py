"""
Script Name - settings.py (part of Settings package).

Usage - Any script that imports the following,
    * from Settings.settings import *

Created by - Michael Samelsohn, 08/04/2024
"""

# Imports #
from datetime import datetime
from Utilities.logger import Logger
log = Logger()

TIME = datetime.now().strftime("%Y-%m-%d_%H%M")
