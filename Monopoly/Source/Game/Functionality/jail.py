# Imports #
from Monopoly.Settings.monopoly_settings import *
from Monopoly.Source.Game.player import Player, Human


def jail_handler(player: Player):
    """
    TODO: Complete the docstring.
    """

    while True:
        if isinstance(player, Human):
            choice = (input(f"{player.name} ({player.cash}$), Please choose action 'pay', 'free', or 'end': ")
                      .strip().lower())
        else:  # Bot.
            choice = player.jail_logic()

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
    TODO: Complete the docstring.
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
    TODO: Complete the docstring.
    """

    # Make sure the player isn't trying to get out of jail after rolling.
    if player.post_roll:
        log.warning("Can use 'get out of jail free' card only at the start of a turn!")
        return
    # Make sure player has any 'get out of jail free' card(s).
    if player.free_cards == 0:
        log.warning("No free cards")
        return

    # Free the player from jail.
    player.free_cards -= 1
    # Reset the jail parameters.
    player.in_jail = False
    player.turns_in_jail = 0
    # TODO: Put card at the bottom of the deck (which one?).
