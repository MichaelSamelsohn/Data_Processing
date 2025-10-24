# Imports #
from Monopoly.Source.board import *


# Roll functionality #


def is_monopoly_owned_by_player(player, color: str, board: Board):
    """
    Checks whether the specified player owns all spaces of a given color monopoly on the board.

    :param player: The player object to check ownership against.
    :param color: The color group (e.g., "blue", "red") to check for monopoly.
    :param board: The game board containing all property spaces.

    :return: True if the player owns all properties in the specified color group, False otherwise.
    """

    monopoly = [s for s in board.spaces if isinstance(s, RealEstate) and s.color == color]
    return True if all(space.owner == player for space in monopoly) else False


# Development functionality #


def find_valid_spaces_to_build_on(player, board: Board):
    """
    Determines valid real estate spaces where the given player can build houses or hotels, based on the game's building
    rules. A space is considered valid for building if all the following conditions are met:
    1. The player owns all properties of the same color group (i.e., has a monopoly).
    2. The space does not already have a hotel built.
    3. The space follows the 'even build/sell' rule (i.e., player must build evenly across the monopoly).
    4. The player has enough cash to afford the building cost for that space.

    :param player: The player object, which contains owned spaces and current cash.
    :param board: The game board object, which contains all spaces on the board.

    :return: A dictionary where each key is a color group (str or enum) and each value is a list of RealEstate spaces
    (objects) that are valid to build on. Only color groups with at least one valid space to build on are included.
    """

    # Dictionary used to mark available spaces to build on for the current player.
    valid_spaces_to_build_on = {}

    # Find all colors spaces a player owns.
    colors = set(space.color for space in player.spaces if isinstance(space, RealEstate))

    # Find all valid spaces that follow the criteria for building.
    for color in colors:
        # Find all spaces of the current monopoly color.
        monopoly_spaces = [space for space in board.spaces if isinstance(space, RealEstate) and space.color == color]

        # Criteria (1) - Check that all spaces in the monopoly are owned by the player.
        if all(space.owner == player and not space.is_mortgaged for space in monopoly_spaces):
            # Found a monopoly owned by the player.

            # Criteria (2)+(3) - Find spaces which don't have hotels and comply with the 'Even build/sell' rule.
            min_houses = min(space.houses for space in monopoly_spaces if not space.hotel)
            even_build_monopoly_spaces = [space for space in monopoly_spaces if not space.hotel
                                          and space.houses == min_houses]

            # Criteria (4) - Find spaces that player can afford the build cost.
            valid_spaces_to_build_on[color] = [space for space in even_build_monopoly_spaces
                                               if player.cash > space.building_cost]

    # Filter any monopolies which have no available spaces to build on.
    return {k: v for k, v in valid_spaces_to_build_on.items() if v != []}


def find_valid_spaces_to_sell_from(player, board: Board):
    """
    Determines valid real estate spaces where the given player can sell houses or hotels, based on the game's selling
    rules. A space is considered valid for selling buildings if all the following conditions are met:
    1. The player owns all properties of the same color group (i.e., has a monopoly).
    2. The space follows the 'even build/sell' rule (i.e., player must build evenly across the monopoly).
    3. The space has at least one house to sell.

    :param player: The player object, which contains owned spaces and current cash.
    :param board: The game board object, which contains all spaces on the board.

    :return: A dictionary where each key is a color group (str or enum) and each value is a list of RealEstate spaces
    (objects) that are valid to sell from. Only color groups with at least one valid space to sell from are included.
    """

    # Dictionary used to mark available spaces to sell from for the current player.
    valid_spaces_to_sell_from = {}

    # Find all colors spaces a player owns.
    colors = set(space.color for space in player.spaces if isinstance(space, RealEstate))

    # Find all valid spaces that follow the criteria for selling.
    for color in colors:
        # Find all spaces of the current monopoly color.
        monopoly_spaces = [space for space in board.spaces if isinstance(space, RealEstate) and space.color == color]

        # Criteria (1) - Check that all spaces in the monopoly are owned by the player.
        if all(p.owner == player for p in monopoly_spaces):
            # Found a monopoly owned by the player.

            # Criteria (2) - Find spaces that comply with the 'Even build/sell' rule.
            max_houses = max(space.houses for space in monopoly_spaces)
            even_sell_monopoly_spaces = [space for space in monopoly_spaces if space.hotel
                                         or space.houses == max_houses]

            # Criteria (3) - Check that space has any building to sell.
            valid_spaces_to_sell_from[color] = [space for space in even_sell_monopoly_spaces if space.houses > 0]

    # Filter any monopolies which have no available spaces to build on.
    return {k: v for k, v in valid_spaces_to_sell_from.items() if v != []}


# Management functionality #


def find_valid_spaces_to_mortgage(player):
    """
    Returns a list of the player's properties that are eligible to be mortgaged. A property (space) is considered valid
    for mortgaging if:
    - It is not already mortgaged, and
    - One of the following is true:
      * It is a non-RealEstate property (e.g., a Railroad or Utility), or
      * It is a RealEstate property that has no houses and no hotel built on it.

    :param player: The player whose owned spaces are to be checked. The player is expected to have an attribute
    `spaces` which is an iterable of property objects.

    :return: A list of property objects that the player can legally mortgage.
    """

    spaces_to_mortgage = []
    for space in player.spaces:
        if not space.is_mortgaged:
            # Space is not already mortgaged.
            if not isinstance(space, RealEstate):
                # Either railroad or utility.
                spaces_to_mortgage.append(space)
            elif space.houses == 0 and not space.hotel:
                # Real estate space with no houses or hotels.
                spaces_to_mortgage.append(space)

    return spaces_to_mortgage
