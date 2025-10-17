# Imports #
from Monopoly.Settings.monopoly_settings import *


class Space:
    def __init__(self, name, position):
        self.name = name
        self.position = position


class RealEstate(Space):
    def __init__(self, name, position, color, purchase_price, base_rent, one_house_rent, two_house_rent,
                 three_house_rent, four_house_rent, hotel_rent, house_cost, hotel_cost):
        super().__init__(name=name, position=position)

        # General information.
        self.color = color
        self.owner = None

        # Property value.
        self.purchase_price = purchase_price
        self.is_mortgaged = False
        self.mortgage_value = self.purchase_price // 2
        self.redeem_value = self.mortgage_value * 1.1  # 10% interest.

        # Rent prices.
        self.base_rent = base_rent
        self.full_set_rent = self.base_rent * 2
        self.one_house_rent = one_house_rent
        self.two_house_rent = two_house_rent
        self.three_house_rent = three_house_rent
        self.four_house_rent = four_house_rent
        self.hotel_rent = hotel_rent

        # Real estate information.
        self.houses = 0
        self.hotel = False
        self.house_cost = house_cost
        self.hotel_cost = hotel_cost

    def print_information(self):
        if self.is_mortgaged:
            buildings_string = ", mortgaged"
        elif self.hotel:
            buildings_string = ", hotel"
        elif self.houses > 0:  # Houses
            buildings_string = f", houses - {self.houses}"
        else:  # No buildings on the property.
            buildings_string = ""

        log.info(f"{self.name} ({self.color}), position - {self.position}, price - {self.purchase_price}, "
                 f"base rent - {self.base_rent}{buildings_string}")


class Railroad(Space):
    def __init__(self, name, position, purchase_price):
        super().__init__(name=name, position=position)

        self.purchase_price = purchase_price
        self.owner = None
        self.is_mortgaged = False

    def print_information(self):
        log.info(f"{self.name}, position - {self.position}, price - {self.purchase_price}"
                 f"{", mortgaged" if self.is_mortgaged else ""}")


class Utility(Space):
    def __init__(self, name, position, purchase_price):
        super().__init__(name=name, position=position)

        self.purchase_price = purchase_price
        self.owner = None
        self.is_mortgaged = False

    def print_information(self):
        log.info(f"{self.name}, position - {self.position}, price - {self.purchase_price}"
                 f"{", mortgaged" if self.is_mortgaged else ""}")


class Board:
    def __init__(self):
        log.info("Generating game board")

        # List of spaces on the board.
        self.spaces = [
            Space(name="Go", position=0),
            RealEstate(name="Mediterranean Avenue", position=1, color="Brown", purchase_price=60, base_rent=2,
                       one_house_rent=10, two_house_rent=30, three_house_rent=90, four_house_rent=160, hotel_rent=250,
                       house_cost=50, hotel_cost=50),
            Space(name="Community Chest", position=2),
            RealEstate(name="Baltic Avenue", position=3, color="Brown", purchase_price=60, base_rent=4,
                       one_house_rent=20, two_house_rent=60, three_house_rent=180, four_house_rent=320, hotel_rent=450,
                       house_cost=50, hotel_cost=50),
            Space(name="Income Tax", position=4),
            Railroad(name="Reading Railroad", position=5, purchase_price=200),
            RealEstate(name="Oriental Avenue", position=6, color="Light Blue", purchase_price=100, base_rent=6,
                       one_house_rent=30, two_house_rent=90, three_house_rent=270, four_house_rent=400, hotel_rent=550,
                       house_cost=50, hotel_cost=50),
            Space(name="Chance", position=7),
            RealEstate(name="Vermont Avenue", position=8, color="Light Blue", purchase_price=100, base_rent=6,
                       one_house_rent=30, two_house_rent=90, three_house_rent=270, four_house_rent=400, hotel_rent=550,
                       house_cost=50, hotel_cost=50),
            RealEstate(name="Connecticut Avenue", position=9, color="Light Blue", purchase_price=120, base_rent=8,
                       one_house_rent=40, two_house_rent=100, three_house_rent=300, four_house_rent=450, hotel_rent=600,
                       house_cost=50, hotel_cost=50),
            Space(name="Jail / Just Visiting", position=10),
            RealEstate(name="St. Charles Place", position=11, color="Pink", purchase_price=140, base_rent=10,
                       one_house_rent=50, two_house_rent=150, three_house_rent=450, four_house_rent=625, hotel_rent=750,
                       house_cost=100, hotel_cost=100),
            Utility(name="Electric Company", position=12, purchase_price=150),
            RealEstate(name="States Avenue", position=13, color="Pink", purchase_price=140, base_rent=10,
                       one_house_rent=50, two_house_rent=150, three_house_rent=450, four_house_rent=625, hotel_rent=750,
                       house_cost=100, hotel_cost=100),
            RealEstate(name="Virginia Avenue", position=14, color="Pink", purchase_price=160, base_rent=12,
                       one_house_rent=60, two_house_rent=180, three_house_rent=500, four_house_rent=700, hotel_rent=900,
                       house_cost=100, hotel_cost=100),
            Railroad(name="Pennsylvania Railroad", position=15, purchase_price=200),
            RealEstate(name="St. James Place", position=16, color="Orange", purchase_price=180, base_rent=14,
                       one_house_rent=70, two_house_rent=200, three_house_rent=550, four_house_rent=750, hotel_rent=950,
                       house_cost=100, hotel_cost=100),
            Space(name="Community Chest", position=17),
            RealEstate(name="Tennessee Avenue", position=18, color="Orange", purchase_price=180, base_rent=14,
                       one_house_rent=70, two_house_rent=200, three_house_rent=550, four_house_rent=750, hotel_rent=950,
                       house_cost=100, hotel_cost=100),
            RealEstate(name="New York Avenue", position=19, color="Orange", purchase_price=200, base_rent=16,
                       one_house_rent=80, two_house_rent=220, three_house_rent=600, four_house_rent=800, hotel_rent=1000,
                       house_cost=100, hotel_cost=100),
            Space(name="Free Parking", position=20),
            RealEstate(name="Kentucky Avenue", position=21, color="Red", purchase_price=220, base_rent=18,
                       one_house_rent=90, two_house_rent=250, three_house_rent=700, four_house_rent=875, hotel_rent=1050,
                       house_cost=150, hotel_cost=150),
            Space(name="Chance", position=22),
            RealEstate(name="Indiana Avenue", position=23, color="Red", purchase_price=220, base_rent=18,
                       one_house_rent=90, two_house_rent=250, three_house_rent=700, four_house_rent=875, hotel_rent=1050,
                       house_cost=150, hotel_cost=150),
            RealEstate(name="Illinois Avenue", position=24, color="Red", purchase_price=240, base_rent=20,
                       one_house_rent=100, two_house_rent=300, three_house_rent=750, four_house_rent=925, hotel_rent=1100,
                       house_cost=150, hotel_cost=150),
            Railroad(name="B&O Railroad", position=25, purchase_price=200),
            RealEstate(name="Atlantic Avenue", position=26, color="Yellow", purchase_price=260, base_rent=22,
                       one_house_rent=110, two_house_rent=330, three_house_rent=800, four_house_rent=975, hotel_rent=1150,
                       house_cost=150, hotel_cost=150),
            RealEstate(name="Ventnor Avenue", position=27, color="Yellow", purchase_price=260, base_rent=22,
                       one_house_rent=110, two_house_rent=330, three_house_rent=800, four_house_rent=975, hotel_rent=1150,
                       house_cost=150, hotel_cost=150),
            Utility(name="Water Works", position=28, purchase_price=150),
            RealEstate(name="Marvin Gardens", position=29, color="Yellow", purchase_price=280, base_rent=24,
                       one_house_rent=120, two_house_rent=360, three_house_rent=850, four_house_rent=1025, hotel_rent=1275,
                       house_cost=150, hotel_cost=150),
            Space(name="Go To Jail", position=30),
            RealEstate(name="Pacific Avenue", position=31, color="Green", purchase_price=300, base_rent=26,
                       one_house_rent=130, two_house_rent=390, three_house_rent=900, four_house_rent=1100, hotel_rent=1275,
                       house_cost=200, hotel_cost=200),
            RealEstate(name="North Carolina Avenue", position=32, color="Green", purchase_price=300, base_rent=26,
                       one_house_rent=130, two_house_rent=390, three_house_rent=900, four_house_rent=1100, hotel_rent=1275,
                       house_cost=200, hotel_cost=200),
            Space(name="Community Chest", position=33),
            RealEstate(name="Pennsylvania Avenue", position=34, color="Green", purchase_price=320, base_rent=28,
                       one_house_rent=150, two_house_rent=450, three_house_rent=1000, four_house_rent=1200, hotel_rent=1400,
                       house_cost=200, hotel_cost=200),
            Railroad(name="Short Line", position=35, purchase_price=200),
            Space(name="Chance", position=36),
            RealEstate(name="Park Place", position=37, color="Dark Blue", purchase_price=350, base_rent=35,
                       one_house_rent=175, two_house_rent=500, three_house_rent=1100, four_house_rent=1300, hotel_rent=1500,
                       house_cost=200, hotel_cost=200),
            Space(name="Luxury Tax", position=38),
            RealEstate(name="Boardwalk", position=39, color="Dark Blue", purchase_price=400, base_rent=50,
                       one_house_rent=200, two_house_rent=600, three_house_rent=1400, four_house_rent=1700, hotel_rent=2000,
                       house_cost=200, hotel_cost=200),
        ]

        for space in self.spaces:
            if isinstance(space, RealEstate):
                log.debug(f"({space.position}) {space.name} ({space.color}) - Price ${space.purchase_price}, ")
            elif isinstance(space, Utility) or isinstance(space, Railroad):
                log.debug(f"({space.position}) {space.name} - Price ${space.purchase_price}")
            else:  # Special card.
                log.debug(f"({space.position}) {space.name}")

        log.success("Game board is ready")

    def get_space(self, position):
        return self.spaces[position]

    def status(self):
        """TODO: Complete the docstring."""
        pass
