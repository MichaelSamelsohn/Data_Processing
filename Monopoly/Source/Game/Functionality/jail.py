# Imports #
from Monopoly.Settings.monopoly_settings import *
from Monopoly.Source.Game.player import Player


def jail_handler(player: Player, action: str):
    """
    Handles player actions related to getting out of jail. Options:
    * "pay" - The player pays a fine and is released from jail. Can only be done before rolling the dice.
    * "free" - The player can only use a 'Get out of jail free' card (if they have one). Can only be done before
      rolling the dice.

    :param player: The player who is currently in jail.
    :param action: The action the player wants to take to get out of jail. Valid values are:
    - "pay": Pay a fine to get out of jail.
    - "free": Use a 'get out of jail free' card.
    """

    if action == "pay":
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

    elif action == "free":
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
