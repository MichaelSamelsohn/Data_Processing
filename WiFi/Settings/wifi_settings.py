# Imports #
from Utilities.logger import Logger

# Logger settings.
log = Logger()
log.add_custom_log_level("success", 25, "\x1b[32;1m")       # Bright Green.
log.add_custom_log_level("traffic", 11, "\x1b[38;5;208m")   # Deep Violet / Grape.
log.add_custom_log_level("channel", 12, "\x1b[38;5;5m")     # Magenta.
log.log_level = 20

HOST = '127.0.0.1'

CHANNEL_HOST = '127.0.0.1'
CHANNEL_PORT = 65535

SHORT_RETRY_LIMIT = 7
