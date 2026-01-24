# Imports #
from Monopoly.Settings.monopoly_settings import log
from Monopoly.Source.Game.board import RealEstate
from Monopoly.Source.Game.player import Player, Human


def management_handler(player: Player):
    """
    Handles mortgage-related actions for the given player. This method allows the player to interactively choose one
    of the following actions:
    - 'mortgage': Mortgage a property to receive cash.
    - 'redeem': Redeem a previously mortgaged property by paying its mortgage value plus interest.
    - 'done': Exit the mortgage handler.

    :param player: The player object that is performing the mortgage-related actions.
    """

    while True:
        if isinstance(player, Human):
            choice = (input(f"{player.name} ({player.cash}$), Please choose action 'mortgage', 'redeem', "
                            f"or 'done': ").strip().lower())
        else:  # Bot.
            choice = player.management_choice()

        match choice:
            case "mortgage":
                mortgage(player=player)
                return
            case "redeem":
                redeem(player=player)
                return
            case "done":
                return
            case _:
                log.warning(f"'{choice}' is an unidentified action")


def mortgage(player: Player):
    """
    Allows a player to mortgage one or more of their eligible properties in exchange for cash. A property is
    eligible for mortgaging if:
    - It is owned by the player.
    - It is not already mortgaged.
    - If it is a RealEstate property, it must not have any houses or hotels built on it.

    The function presents the player with a list of mortgageable properties and allows them to select one at a time.
    After each selection, the property is mortgaged (flagged as such), and the mortgage value is added to the
    player's cash.

    :param player: The player attempting to mortgage properties.
    """

    # Find any spaces the player owns that are not mortgaged and don't have houses or hotels on them.
    valid_spaces_to_mortgage = find_valid_spaces_to_mortgage(player=player)
    # Make sure there are any spaces to mortgage.
    if not valid_spaces_to_mortgage:
        log.warning(f"No spaces available to mortgage")
        return

    # Present player with all valid options.
    log.info("Spaces to mortgage:")
    log.info([f"{space.name} (mortgage value - {space.mortgage_value})" for space in valid_spaces_to_mortgage])

    while True:
        # Player to choose which space to mortgage.
        if isinstance(player, Human):
            choice = input(f"Enter space number to mortgage ('end' to finish): ").strip().lower()
            if choice == "end":
                return
        else:  # Bot.
            choice = player.mortgage_choice()

        if not choice.isdigit() or not (0 <= int(choice) <= len(valid_spaces_to_mortgage) - 1):
            log.warning("Invalid choice, try again")
            continue

        # Got to this point, choice is a valid number.

        # Mortgage space.
        space_to_mortgage = valid_spaces_to_mortgage[int(choice)]
        space_to_mortgage.is_mortgaged = True
        player.cash += space_to_mortgage.mortgage_value
        log.info(f"{player.name} mortgaged {space_to_mortgage.name} for {space_to_mortgage.mortgage_value}$")
        return


def redeem(player: Player):
    """
    Allows the player to redeem (unmortgage) eligible properties. This method checks all properties owned by the
    given player and presents a list of mortgaged properties that the player can afford to redeem based on their
    current cash. The player is prompted to select which property to redeem by entering its number. After each
    redemption, the method recursively calls itself to allow the player to continue redeeming additional properties
    if they wish.

    :param player: The player attempting to redeem mortgaged properties.
    """

    # Find any spaces the player owns that are mortgaged and player has enough cash to redeem.
    valid_spaces_to_redeem = find_valid_spaces_to_redeem(player=player)
    # Make sure there are spaces to redeem.
    if not valid_spaces_to_redeem:
        log.warning(f"No spaces available to redeem")
        return

    # Present player with all valid options.
    log.info("Spaces to redeem:")
    log.info([space.name for space in valid_spaces_to_redeem])

    while True:
        # Player to choose which space to redeem.
        if isinstance(player, Human):
            choice = input(f"Enter space number to redeem ('end' to finish): ").strip().lower()
            if choice == "end":
                return
        else:  # Bot.
            choice = player.redeem_choice()

        if not choice.isdigit() or not (0 <= int(choice) <= len(valid_spaces_to_redeem) - 1):
            log.warning("Invalid choice, try again")
            continue

        # Got to this point, choice is a valid number.

        # Redeem space.
        space_to_redeem = valid_spaces_to_redeem[int(choice)]
        space_to_redeem.is_mortgaged = False
        player.cash -= space_to_redeem.redeem_value
        log.info(f"{player.name} redeemed {space_to_redeem.name} for {space_to_redeem.redeem_value}$")
        return


def find_valid_spaces_to_mortgage(player: Player) -> list:
    """
    Returns a list of the player's properties that are eligible to be mortgaged. A property (space) is considered valid
    for mortgaging if:
    - It is not already mortgaged, and
    - One of the following is true:
      * It is a non-RealEstate property (e.g., a Railroad or Utility), or
      * It is a RealEstate property that the monopoly it is part of has no houses and no hotel built on it.

    :param player: The player whose owned spaces are to be checked. The player is expected to have an attribute
    `spaces` which is an iterable of property objects.

    :return: A list of property objects that the player can legally mortgage.
    """

    spaces_to_mortgage = []
    for space in player.spaces:
        if not space.is_mortgaged:
            # Space is not already mortgaged.
            if isinstance(space, RealEstate):
                # Filter all spaces a player has that are of type real-estate.
                realestate_spaces = [space_ for space_ in player.spaces if isinstance(space_, RealEstate)]
                # Filter all real-estate spaces that belong to the same monopoly.
                monopoly_spaces = [space_ for space_ in realestate_spaces if space_.color == space.color]
                # Filter all real-estate spaces that belong to the same monopoly and have a building.
                monopoly_spaces_with_buildings = [space_ for space_ in monopoly_spaces if
                                                  space_.houses > 0 or space_.hotel]
                # Check that there are no buildings on the associated monopoly.
                if not monopoly_spaces_with_buildings:
                    # Real estate is part of a monopoly with no houses or hotels at all.
                    spaces_to_mortgage.append(space)
            else:
                # Either railroad or utility.
                spaces_to_mortgage.append(space)

    return spaces_to_mortgage


def find_valid_spaces_to_redeem(player):
    """
    Returns a list of the player's mortgaged spaces that can be redeemed based on available cash.

    A space is considered valid for redemption if:
    - The space is currently mortgaged.
    - The player has enough cash to cover the redemption cost.

    :param player: The player whose properties are being checked.

    :return: A list of space objects that the player can afford to redeem.
    """

    return [space for space in player.spaces if space.is_mortgaged and player.cash > space.redeem_value]
