# Imports #
from Utilities.logger import Logger

# Logger settings #

verbosity_level = 3  # Setting the verbosity level.
log = Logger()       # Initiating the logger.

# Adding custom levels.
log.add_custom_log_level("success", 25, "\x1b[32;1m")       # Bright Green.

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

RAILROADS = [
    ("Reading Railroad", 5),
    ("Pennsylvania Railroad", 15),
    ("B&O Railroad", 25),
    ("Short Line", 35)
]

UTILITIES = [
    ("Electric Company", 12),
    ("Water Works", 28),
]

PROPERTIES = [
    # Brown
    ("Mediterranean Avenue", 1, 60, 2, "Brown"),
    ("Baltic Avenue", 3, 60, 4, "Brown"),
    # Light Blue
    ("Oriental Avenue", 6, 100, 6, "Light Blue"),
    ("Vermont Avenue", 8, 100, 6, "Light Blue"),
    ("Connecticut Avenue", 9, 120, 8, "Light Blue"),
    # Pink
    ("St. Charles Place", 11, 140, 10, "Pink"),
    ("States Avenue", 13, 140, 10, "Pink"),
    ("Virginia Avenue", 14, 160, 12, "Pink"),
    # Orange
    ("St. James Place", 16, 180, 14, "Orange"),
    ("Tennessee Avenue", 18, 180, 14, "Orange"),
    ("New York Avenue", 19, 200, 16, "Orange"),
    # Red
    ("Kentucky Avenue", 21, 220, 18, "Red"),
    ("Indiana Avenue", 23, 220, 18, "Red"),
    ("Illinois Avenue", 24, 240, 20, "Red"),
    # Yellow
    ("Atlantic Avenue", 26, 260, 22, "Yellow"),
    ("Ventnor Avenue", 27, 260, 22, "Yellow"),
    ("Marvin Gardens", 29, 280, 24, "Yellow"),
    # Green
    ("Pacific Avenue", 31, 300, 26, "Green"),
    ("North Carolina Avenue", 32, 300, 26, "Green"),
    ("Pennsylvania Avenue", 34, 320, 28, "Green"),
    # Dark Blue
    ("Park Place", 37, 350, 35, "Dark Blue"),
    ("Boardwalk", 39, 400, 50, "Dark Blue"),
]

HOUSE_PRICES = {
    "Brown": 50,
    "Light Blue": 50,
    "Pink": 100,
    "Orange": 100,
    "Red": 150,
    "Yellow": 150,
    "Green": 200,
    "Dark Blue": 200
}
