# Imports #
from Utilities.logger import Logger

# Logger settings #

verbosity_level = 2  # Setting the verbosity level.
log = Logger()       # Initiating the logger.

# Adding custom levels.
log.add_custom_log_level("success", 25, "\x1b[32;1m")       # Bright Green.
log.add_custom_log_level("logic", 12, "\x1b[38;5;5m")     # Magenta.

# Handling verbosity levels.
match verbosity_level:
    case 1:
        log.format_string = "%(asctime)s - %(levelname)s - %(message)s"
        log.log_level = 20
    case 2:
        log.format_string = "%(asctime)s - %(levelname)s - %(message)s"
        log.log_level = 12
    case 3:
        log.format_string = "%(asctime)s - %(levelname)s (%(module)s:%(funcName)s:%(lineno)d) - %(message)s"
        log.log_level = 10

GO_SALARY = 200
JAIL_FINE = 50
