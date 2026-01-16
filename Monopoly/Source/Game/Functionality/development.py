from Monopoly.Settings.monopoly_settings import log
from Monopoly.Source.Game.board import RealEstate, Board
from Monopoly.Source.Game.player import Human, Player


def development_handler(player: Player, board: Board):
    """
    Handles development-related actions for the given player. This method allows the player to interactively choose
    one of the following actions:
    - 'build': Build a house/hotel.
    - 'sell': Sell a house/hotel.
    - 'end': Exit the mortgage handler.

    :param player: The player object that is performing the development-related actions.
    :param board: The game board object, which contains all spaces on the board.
    """

    while True:
        if isinstance(player, Human):
            choice = (input(f"{player.name} ({player.cash}$), Please choose action 'build', 'sell', or 'end': ")
                      .strip().lower())
        else:  # Bot.
            choice = player.development_choice()

        match choice:
            case "build":
                build(player, board)
                return
            case "sell":
                sell(player, board)
                return
            case "end":
                return
            case _:
                log.warning(f"'{choice}' is an unidentified action")


def build(player: Player, board: Board):
    """
    Allows a player to build houses or hotels on properties within full color sets they own. This method first
    identifies all full color groups (monopolies) owned by the player. If any are found, the player is prompted to
    choose properties within those groups to develop. The player may build houses evenly across the set and, after
    reaching four houses, can upgrade to a hotel. All development actions deduct the appropriate cost from the
    player's cash.

    :param player: The player attempting to build houses or hotels.
    :param board: The game board object, which contains all spaces on the board.
    """

    # Find all player owned valid spaces with option to build on.
    valid_spaces_to_build_on = find_valid_spaces_to_build_on(player=player, board=board)
    if not valid_spaces_to_build_on:
        log.warning(f"{player.name} has no spaces to build on")
        return

    # Present player with all valid options.
    log.info("Spaces to buy on:")
    for monopoly in valid_spaces_to_build_on:
        log.info(f"{monopoly} (build cost, {valid_spaces_to_build_on[monopoly][0].building_cost}) "
                 f"- {[space.name for space in valid_spaces_to_build_on[monopoly]]}")

    while True:
        # Player to choose valid monopoly.
        if isinstance(player, Human):
            choice = input(f"Enter monopoly color to build on ('end' to finish building): ").strip().lower()
            if choice == "end":
                return
        else:  # Bot.
            choice = player.monopoly_build_selection_choice()

        if choice not in valid_spaces_to_build_on.keys():
            log.warning("Invalid choice, try again")
            continue

        # Got to this point, choice is a valid monopoly color.
        selected_spaces_to_build_on = valid_spaces_to_build_on[choice]

        while True:
            # Player to choose which space to build house/hotel in.
            if isinstance(player, Human):
                choice = (input(f"Enter space index to build house/hotel ('end' to finish building): ").
                          strip().lower())
                if choice == "end":
                    return
            else:  # Bot.
                choice = player.space_build_selection_choice()

            if not choice.isdigit() or not (0 <= int(choice) <= len(selected_spaces_to_build_on) - 1):
                log.warning("Invalid choice, try again")
                continue

            # Got to this point, choice is a valid index number.
            space = selected_spaces_to_build_on[int(choice)]

            # Build building.
            if space.houses == 4:
                # Building hotel.
                space.houses = 0
                space.hotel = True
            else:
                # Building house.
                space.houses += 1
            # Deduct building cost from player.
            player.cash -= space.building_cost
            return


def sell(player: Player, board: Board):
    """
    Allows a player to sell houses or hotels from properties they own. This method facilitates the selling of houses
    or hotels in accordance with the Monopoly rules, including the even building/selling rule. The player must own a
    full color-set (monopoly) to have any buildings to sell, and may only sell buildings in a uniform manner across
    the properties in that color group.

    The function:
    - Identifies all monopolies owned by the player.
    - Filters only those monopolies that have at least one house or hotel.
    - Prompts the player to select a monopoly color group to sell from.
    - Displays properties within that group where selling is valid.
    - Prompts the player to select a property to sell a house or hotel from.
    - Updates the property state (removing hotel or house).
    - Adds the appropriate cash amount to the player.
    - Repeats the process until the player decides to stop selling.

    :param player: The player attempting to sell houses or hotels.
    :param board: The game board object, which contains all spaces on the board.
    """

    # Find all player owned valid spaces with option to sell from.
    valid_spaces_to_sell_from = find_valid_spaces_to_sell_from(player=player, board=board)
    if not valid_spaces_to_sell_from:
        log.warning(f"{player.name} does not own any spaces with houses/hotels to sell")
        return

    # Present player with all valid options.
    log.info("Spaces to sell from:")
    for monopoly, spaces in valid_spaces_to_sell_from.items():
        log.info(f"{monopoly} - {[space.name for space in spaces]}")

    while True:
        # Player to choose monopoly to sell houses/hotels.
        if isinstance(player, Human):
            choice = input(f"Enter monopoly number to sell from on ('end' to finish selling): ").strip().lower()
            if choice == "end":
                return
        else:  # Bot.
            choice = player.monopoly_sell_selection_choice()

        if choice not in valid_spaces_to_sell_from.keys():
            log.warning("Invalid choice, try again")
            continue

        # Got to this point, choice is a valid monopoly color.
        selected_spaces_to_sell_from = valid_spaces_to_sell_from[choice]

        while True:
            # Player to choose which space to sell houses/hotels in.
            if isinstance(player, Human):
                choice = (input(f"Enter space number to sell house/hotel ('end' to finish selling): ").
                          strip().lower())
                if choice == "end":
                    return
            else:  # Bot.
                choice = player.space_sell_selection_choice()

            if not choice.isdigit() or not (0 <= int(choice) <= len(selected_spaces_to_sell_from)):
                log.warning("Invalid choice, try again")
                continue

            # Got to this point, choice is a valid number.
            space = selected_spaces_to_sell_from[int(choice)]

            # Sell building.
            if space.hotel:
                # Selling hotel.
                space.hotel = False
                space.houses = 4
            else:
                # Selling house.
                space.houses -= 1
            # Compensate player.
            player.cash += space.building_sell
            return


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

        # Criteria (1) - Check that all spaces in the monopoly are owned by the player and at least one space without
        # a hotel.
        if (all(space.owner == player and not space.is_mortgaged for space in monopoly_spaces) and
            not all(space.hotel for space in monopoly_spaces)):
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

            # Criteria (3) - Check that space has any building to sell (precedence for hotels).
            spaces_with_hotels = [space for space in even_sell_monopoly_spaces if space.hotel]
            valid_spaces_to_sell_from[color] = spaces_with_hotels if spaces_with_hotels \
                else [space for space in even_sell_monopoly_spaces if space.houses > 0]

    # Filter any monopolies which have no available spaces to build on.
    return {k: v for k, v in valid_spaces_to_sell_from.items() if v != []}


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
