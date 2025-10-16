# Imports #
from Monopoly.Settings.monopoly_settings import *


class Space:
    def __init__(self, name, position, tile_type):
        self.name = name
        self.position = position
        self.space_type = tile_type


class RealEstate(Space):
    def __init__(self, name, position, price, base_rent, color):
        super().__init__(name, position, "Property")
        self.price = price
        self.base_rent = base_rent
        self.color = color
        self.owner = None
        self.houses = 0
        self.hotel = False
        self.house_price = HOUSE_PRICES.get(color, 50)
        self.is_mortgaged = False

    def print_information(self):
        if self.is_mortgaged:
            buildings_string = ", mortgaged"
        elif self.hotel:
            buildings_string = ", hotel"
        elif self.houses > 0:  # Houses
            buildings_string = f", houses - {self.houses}"
        else:  # No buildings on the property.
            buildings_string = ""

        log.info(f"{self.name} ({self.color}), position - {self.position}, price - {self.price}, "
                 f"base rent - {self.base_rent}{buildings_string}")


class Railroad(Space):
    def __init__(self, name, position, price=200):
        super().__init__(name, position, "Railroad")
        self.price = price
        self.owner = None
        self.is_mortgaged = False

    def print_information(self):
        log.info(f"{self.name}, position - {self.position}, price - {self.price}"
                 f"{", mortgaged" if self.is_mortgaged else ""}")


class Utility(Space):
    def __init__(self, name, position, price=150):
        super().__init__(name, position, "Utility")
        self.price = price
        self.owner = None
        self.is_mortgaged = False

    def print_information(self):
        log.info(f"{self.name}, position - {self.position}, price - {self.price}"
                 f"{", mortgaged" if self.is_mortgaged else ""}")


class Board:
    def __init__(self):
        log.info("Generating game board")

        self.spaces = []  # List of spaces on the board.

        log.debug("Adding special spaces")
        self.spaces.append(Space("Go", 0, "Go"))
        self.spaces.append(Space("Community Chest", 2, "Community Chest"))
        self.spaces.append(Space("Income Tax", 4, "Tax"))
        self.spaces.append(Space("Chance", 7, "Chance"))
        self.spaces.append(Space("Jail / Just Visiting", 10, "Jail"))
        self.spaces.append(Space("Chance", 22, "Chance"))
        self.spaces.append(Space("Community Chest", 17, "Community Chest"))
        self.spaces.append(Space("Free Parking", 20, "Free Parking"))
        self.spaces.append(Space("Go To Jail", 30, "Go To Jail"))
        self.spaces.append(Space("Community Chest", 33, "Community Chest"))
        self.spaces.append(Space("Chance", 36, "Chance"))
        self.spaces.append(Space("Luxury Tax", 38, "Tax"))

        log.debug("Adding property spaces")
        for name, pos, price, rent, color in PROPERTIES:
            self.spaces.append(RealEstate(name, pos, price, rent, color))

        log.debug("Adding railroad spaces")
        for name, pos in RAILROADS:
            self.spaces.append(Railroad(name, pos))

        log.debug("Adding utility spaces")
        for name, pos in UTILITIES:
            self.spaces.append(Utility(name, pos))

        log.debug("Sorting all spaces according to position")
        self.spaces.sort(key=lambda s: s.position)

        for space in self.spaces:
            if isinstance(space, RealEstate):
                log.debug(f"({space.position}) {space.name} ({space.color}) - Price ${space.price}, "
                          f"Rent ${space.base_rent}, House price ${space.house_price}")
            elif isinstance(space, Utility) or isinstance(space, Railroad):
                log.debug(f"({space.position}) {space.name} - Price ${space.price}")
            else:  # Special card.
                log.debug(f"({space.position}) {space.name}")

        log.success("Game board is ready")

    def get_space(self, position):
        return self.spaces[position]

    def status(self):
        """TODO: Complete the docstring."""
        pass
