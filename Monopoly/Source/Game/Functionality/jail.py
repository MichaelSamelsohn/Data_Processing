# Imports #
from Monopoly.Settings.monopoly_settings import *
from Monopoly.Source.Game.player import Player, Human


def jail_handler(player: Player):
    """
    Handles a player's turn while they are in jail. This function continuously prompts the player (human or bot) to
    choose one of several possible jail actions until a valid choice is made or the player ends their turn.

    Available actions:
    - "pay": The player pays the fine to get out of jail (via `pay_out_of_jail()`).
    - "free": The player uses a "Get Out of Jail Free" card to leave jail (via `use_free_card()`).
    - "end": The player ends their turn and remains in jail.

    :param player: The player object currently in jail. Can be an instance of either `Human` or a bot subclass.
    """

    while True:
        if isinstance(player, Human):
            choice = (input(f"{player.name} ({player.cash}$), Please choose action 'pay', 'free', or 'end': ")
                      .strip().lower())
        else:  # Bot.
            choice = player.jail_choice()

        match choice:
            case "pay":
                pay_out_of_jail(player=player)
                return
            case "free":
                use_free_card(player=player)
                return
            case "end":
                return
            case _:
                log.warning(f"'{choice}' is an unidentified action")


def pay_out_of_jail(player: Player):
    """
    Allows a player to pay a fine to get out of jail. This function lets a player leave jail by paying the predefined
    jail fine (`JAIL_FINE`). The player can only pay the fine at the start of their turn (before rolling), and must have
    enough cash to cover the cost. If successful, the player's jail status and related counters are reset.

    :param player: The player attempting to pay the fine to get out of jail.
    """

    # Make sure the player isn't trying to get out of jail after rolling.
    if player.post_roll:
        log.warning("Can pay fine to get out of jail only at the start of a turn!")
        return

    # Make sure the player can afford the fine.
    if player.cash >= JAIL_FINE:
        player.cash -= JAIL_FINE  # Pay the fine.
        # Reset the jail parameters.
        player.in_jail = False
        player.turns_in_jail = 0
        log.info(f"{player.name} payed {JAIL_FINE} to get out of jail")
    else:
        log.warning(f"{player.name} doesn't have enough cash to pay the jail fine")


def use_free_card(player: Player):
    """
    Allows a player to use a 'Get Out of Jail Free' card to leave jail. This function checks whether the player is
    eligible to use a 'Get Out of Jail Free' card — i.e., it must be used at the start of the player's turn (before
    rolling), and the player must have at least one such card available. If eligible, the player is freed from jail and
    their jail-related state is reset.

    :param player: The player attempting to use the 'Get Out of Jail Free' card.
    """

    # Make sure the player isn't trying to get out of jail after rolling.
    if player.post_roll:
        log.warning("Can use 'get out of jail free' card only at the start of a turn!")
        return
    # Make sure player has any 'get out of jail free' card(s).
    if player.free_cards == 0:
        log.warning("No free cards")
        return

    log.info(f"{player.name} used a 'Get out of jail free' card")
    # Free the player from jail.
    player.free_cards -= 1
    # Reset the jail parameters.
    player.in_jail = False
    player.turns_in_jail = 0
    # TODO: Put card at the bottom of the deck (which one?).
