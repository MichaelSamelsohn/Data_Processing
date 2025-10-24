# Imports #
from Monopoly.Settings.monopoly_settings import log
from Monopoly.Source.Game.player import Player, Human


def trade_handler(trade_offer_initiator: Player, players: list):
    """
    Handles the process of initiating and executing a trade between two players. Prompts the initiator to specify
    another player to trade with, gathers the trade offers (properties and cash) from both parties, presents a trade
    summary, and asks the recipient to accept or decline the offer. If the recipient agrees, the trade is executed
    and the appropriate assets (properties and cash) are exchanged between the two players.

    :param trade_offer_initiator: The player who initiates the trade.
    :param players: List of all players participating in the game.
    """

    # Get trade recipient.
    trade_offer_recipient_name = input("Enter the name of the player you want to trade with: ").strip()
    trade_offer_recipient = next((player for player in players if player.name == trade_offer_recipient_name),
                                 None)
    # Make sure the recipient exists and is not the same player as the initiator.
    if trade_offer_recipient_name == trade_offer_initiator.name or trade_offer_recipient is None:
        log.warning("Invalid player name")
        return

    initiator_space_offer, initiator_cash_offer, initiator_free_cards_offer = (
        make_offer(trade_offer_initiator))
    recipient_space_offer, recipient_cash_offer, recipient_free_cards_offer = (
        make_offer(trade_offer_recipient))

    # Check that initiator of the trade doesn't become bankrupt after it.
    initiator_cash_after_trade = trade_offer_initiator.cash - initiator_cash_offer + recipient_cash_offer
    initiator_mortgage_fee = sum([0.1 * space.mortgage_value for space in recipient_space_offer
                                  if space.is_mortgaged])
    if initiator_cash_after_trade - initiator_mortgage_fee < 0:
        log.warning(f"Bank declined trade offer as it will put the {trade_offer_initiator.name} in bankruptcy")
        return
    # Check that recipient of the trade doesn't become bankrupt after it.
    recipient_cash_after_trade = trade_offer_recipient.cash - recipient_cash_offer + initiator_cash_offer
    recipient_mortgage_fee = sum([0.1 * space.mortgage_value for space in initiator_space_offer
                                  if space.is_mortgaged])
    if recipient_cash_after_trade - recipient_mortgage_fee < 0:
        log.warning(f"Bank declined trade offer as it will put the {trade_offer_recipient.name} in bankruptcy")
        return

    log.info("--- TRADE SUMMARY ---")
    log.info(f"{trade_offer_initiator.name} offers to {trade_offer_recipient.name}: "
             f"{[p.name for p in initiator_space_offer]} + {initiator_cash_offer}$")
    log.info(f"{trade_offer_initiator.name} wants from {trade_offer_recipient.name}: "
             f"{[p.name for p in recipient_space_offer]} + {recipient_cash_offer}$")

    while True:
        # Recipient to confirm trade offer.
        if isinstance(trade_offer_recipient, Human):
            confirm = input(f"Does {trade_offer_recipient.name} accept the trade? (y/n): ")
        else:  # Bot.
            confirm = trade_offer_recipient.trade_acceptance_logic(
                trade_offer_initiator,
                initiator_space_offer, initiator_cash_offer, initiator_free_cards_offer,
                recipient_space_offer, recipient_cash_offer, recipient_free_cards_offer
            )

        match confirm:
            case "y":
                # Perform trade.
                execute_trade(
                    # Player 1.
                    player1=trade_offer_initiator, player1_spaces=initiator_space_offer,
                    player1_cash=initiator_cash_offer, player1_free_cards=initiator_free_cards_offer,
                    # Player 2.
                    player2=trade_offer_recipient, player2_spaces=recipient_space_offer,
                    player2_cash=recipient_cash_offer, player2_free_cards=recipient_free_cards_offer)
                log.info("Trade completed successfully")
                return
            case "n":
                log.warning("Trade declined")
                return
            case _:
                log.warning("Invalid choice")


def make_offer(player: Player):
    """
    Allows the user to create a trade offer by selecting properties and specifying an amount of cash. This method
    displays the player's current properties and prompts the user to choose which properties to include in the offer
    (by index) and how much cash to include. It validates the selections to ensure that the indices and cash amount
    are within valid bounds.

    :param player: The player making the offer.
    """

    # Offer properties.
    log.info(f"{player.name}'s properties:")
    for i, p in enumerate(player.spaces):
        log.debug(f"  [{i}] {p.name}")
    offer_spaces_selection = input("Enter indices of properties to offer (comma separated): ")
    try:
        indices = [int(i.strip()) for i in offer_spaces_selection.split(",") if i.strip()]
        offer_spaces = [player.spaces[i] for i in indices if 0 <= i < len(player.spaces)]
    except Exception:
        log.warning("Invalid selection")
        offer_spaces = []

    # Offer cash.
    try:
        amount = int(input("Enter cash to offer (in $): "))
        if 0 <= amount <= player.cash:
            offer_cash = amount
        else:
            log.warning("Invalid amount")
            offer_cash = 0
    except ValueError:
        offer_cash = 0

    # Offer 'Get out of jail free' cards it player has them.
    offer_free_cards = 0
    if player.free_cards > 0:
        try:
            free_cards = int(input(f"Enter 'Get out of jail free' card(s) to offer "
                                   f"({player.free_cards} available): "))
            if 1 <= free_cards <= player.free_cards:
                offer_free_cards = free_cards
            else:
                log.warning("Invalid amount")
                offer_free_cards = 0
        except ValueError:
            offer_free_cards = 0

    return offer_spaces, offer_cash, offer_free_cards


def execute_trade(player1: Player, player1_spaces: list, player1_cash: int, player1_free_cards: int,
                  player2: Player, player2_spaces: list, player2_cash: int, player2_free_cards: int):
    """
    Executes a trade between two players involving properties, cash and 'Get out of jail free' cards. This method
    transfers ownership of the specified properties and adjusts the cash/cards balances of both players according to
    the trade agreement.

    :param player1: The first player involved in the trade.
    :param player1_spaces: List of Property objects to transfer from player1 to player2.
    :param player1_cash: Amount of cash player1 gives to player2.
    :param player1_free_cards: Amount of 'Get out of jail free' cards player1 gives to player2.
    :param player2: The second player involved in the trade.
    :param player2_spaces: List of Property objects to transfer from player2 to player1.
    :param player2_cash: Amount of cash player2 gives to player1.
    :param player2_free_cards: Amount of 'Get out of jail free' cards player2 gives to player1.
    """

    # Transfer cash.

    # From player 1 to player 2.
    player1.cash -= player1_cash
    player2.cash += player1_cash
    # From player 2 to player 1.
    player2.cash -= player2_cash
    player1.cash += player2_cash

    # Transfer 'Get out of jail free' cards.

    # From player 1 to player 2.
    player1.free_cards -= player1_free_cards
    player2.free_cards += player1_free_cards
    # From player 2 to player 1.
    player2.free_cards -= player2_free_cards
    player1.free_cards += player2_free_cards

    # Transfer spaces.

    # Transfer spaces from player 1 to player 2.
    transfer_spaces(sender=player1, recipient=player2, spaces_to_transfer=player1_spaces)
    transfer_spaces(sender=player2, recipient=player1, spaces_to_transfer=player2_spaces)


def transfer_spaces(sender: Player, recipient: Player, spaces_to_transfer: list):
    """
    Transfers ownership of a list of properties from one player to another. For each property being transferred:
    - Ownership is moved from `sender` to `recipient`.
    - If the property is mortgaged:
        - The recipient is prompted to either:
            - Redeem the mortgage by paying the redeem value, or
            - Pay a 10% mortgage fee to keep it mortgaged.
        - If the recipient cannot afford to redeem, they must pay the 10% fee.

    :param sender: The player giving up the properties.
    :param recipient: The player receiving the properties.
    :param spaces_to_transfer: A list of Property instances to transfer.
    """

    # Calculate cash buffer (to redeem mortgaged properties).
    recipient_mortgage_fee = sum([0.1 * space.mortgage_value for space in spaces_to_transfer if space.is_mortgaged])
    recipient_cash_buffer = recipient.cash - recipient_mortgage_fee

    # Transfer properties from sender to recipient.
    for prop in spaces_to_transfer:
        sender.spaces.remove(prop)
        prop.owner = recipient
        recipient.spaces.append(prop)

        # Recipient to choose between redeeming or paying mortgage fee for mortgaged properties.
        if prop.is_mortgaged:
            if prop.redeem_value < recipient_cash_buffer:
                if isinstance(recipient, Human):
                    action = input("Redeem property or pay mortgage fee (10%): ")
                else:  # Bot.
                    action = recipient.post_trade_redeem_logic()

                while True:
                    match action:
                        case "y":
                            # Redeem space.
                            recipient.cash -= prop.redeem_value
                            prop.is_mortgaged = False
                            recipient_cash_buffer += (- prop.redeem_value) + 0.1 * prop.mortgage_value
                        case "n":
                            # Pay mortgage fee (10%).
                            recipient.cash -= 0.1 * prop.mortgage_value
                        case _:
                            log.warning("Invalid option, choose again")
            else:
                # Recipient doesn't have enough cash to redeem. Pays mortgage fee (10%).
                recipient.cash -= 0.1 * prop.mortgage_value
