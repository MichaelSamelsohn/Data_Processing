# Imports #
from datetime import datetime
from Utilities.logger import Logger
log = Logger()

TIME = datetime.now().strftime("%Y-%m-%d_%H%M")

HOST = '127.0.0.1'

CHANNEL_HOST = '127.0.0.1'
CHANNEL_PORT = 65535

SHORT_RETRY_LIMIT = 7
