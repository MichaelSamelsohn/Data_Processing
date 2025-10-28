# Imports #
from Monopoly.Settings.monopoly_settings import log
from Monopoly.Source.Game.board import RealEstate
from Monopoly.Source.Game.player import Player, Human


def trade_handler(trade_offer_initiator: Player, players: list):
    """
    Handles the trade interaction between two players in the game. This function manages the full trade flow between a
    trade initiator and a recipient. It allows a player to propose a trade, validates that both parties exist and can
    afford the trade, logs the proposed offers, asks both players to confirm, and, if accepted, executes the trade.
    The trade may include:
    - Space exchanges.
    - Cash exchanges.
    - "Get out of jail free" card exchanges.

    Behavior:
    1. The initiator selects another player to trade with.
    2. Both the initiator and the recipient specify what they are offering
       (spaces, cash, free cards).
    3. The system checks if either player would become bankrupt after the trade.
    4. If valid, both players confirm or reject the trade.
    5. If accepted, the trade is executed via `execute_trade()`.

    Validation is performed to ensure that neither player goes bankrupt as a result of the trade, including accounting
    for mortgage fees.

    :param trade_offer_initiator: The player who initiates the trade.
    :param players: A list of all active players in the game. Used to verify that the chosen recipient exists and is
    valid.
    """

    while True:
        # Get trade recipient.
        if isinstance(trade_offer_initiator, Human):
            trade_offer_recipient_name = input("Enter the name of the player you want to trade with "
                                               "('end' to finish): ").strip()
            if trade_offer_recipient_name == "end":
                return
        else:  # Bot.
            trade_offer_recipient_name = trade_offer_initiator.trade_partner_selection_logic()
        trade_offer_recipient = next((player for player in players if player.name == trade_offer_recipient_name),
                                     None)
        # Make sure the recipient exists and is not the same player as the initiator.
        if trade_offer_recipient_name == trade_offer_initiator.name or trade_offer_recipient is None:
            log.warning(f"Either {trade_offer_recipient_name} doesn't exist or is the initiator")
            continue

        # Got to this point, trade offer recipient name is valid.

        initiator_space_offer, initiator_cash_offer, initiator_free_cards_offer = (
            make_offer(trade_master=trade_offer_initiator, trade_partner=trade_offer_initiator))
        recipient_space_offer, recipient_cash_offer, recipient_free_cards_offer = (
            make_offer(trade_master=trade_offer_initiator, trade_partner=trade_offer_recipient))

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
        # Initiator -> Recipient.
        log.info(f"{trade_offer_initiator.name} gives to {trade_offer_recipient.name}:")
        log.info(f"Spaces - {[space.name for space in initiator_space_offer]}")
        log.info(f"Cash - {initiator_cash_offer}$")
        log.info(f"'Get out of jail free' cards - {initiator_free_cards_offer}")
        # Recipient -> Initiator.
        log.info(f"{trade_offer_recipient.name} gives to {trade_offer_initiator.name}:")
        log.info(f"Spaces - {[space.name for space in recipient_space_offer]}")
        log.info(f"Cash - {recipient_cash_offer}$")
        log.info(f"'Get out of jail free' cards - {recipient_free_cards_offer}")

        while True:
            # Initiator to confirm the trade offer.
            if isinstance(trade_offer_recipient, Human):
                confirm = input(f"Does {trade_offer_recipient.name} accept the trade? (y/n): ")
                if confirm == "y":
                    log.warning(f"Trade confirmed by {trade_offer_initiator.name}")
                    break  # Initiator confirms the deal.
                else:
                    log.warning(f"Trade declined by {trade_offer_initiator.name}")
                    return  # Initiator rejects the deal.
            else:  # Bot.
                break  # Bot shouldn't be asked to double-check itself.

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
                    log.warning(f"Trade confirmed by {trade_offer_initiator.name}")

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
                    log.warning(f"Trade declined by {trade_offer_recipient.name}")
                    return
                case _:
                    log.warning("Invalid choice")
                    continue


def make_offer(trade_master: Player, trade_partner: Player):
    """
    Facilitates a trade offer between two players in a property-trading game. This function allows the `trade_master`
    (the player initiating the trade) to propose an offer to the `trade_partner`. The offer can include:
    - Selected properties (spaces) owned by the trade partner.
    - A specified amount of cash.
    - A number of "Get Out of Jail Free" cards.

    Steps:
        1. Identify the valid spaces available for trade.
        2. Allow the trade master to select which spaces to offer.
        3. Allow the trade master to specify how much cash to offer.
        4. Allow the trade master to specify how many "Get Out of Jail Free" cards to offer.
        5. Return the final offer details as a tuple.

    :param trade_master : The player initiating the trade.
    :param trade_partner : The player receiving the trade offer.

    :return: A tuple of the form `(offer_spaces, offer_cash, offer_free_cards)` where:
    - `offer_spaces` (list): A list of property objects selected for trade.
    - `offer_cash` (int): The amount of cash offered.
    - `offer_free_cards` (int): The number of "Get Out of Jail Free" cards offered.
    """

    # Find valid spaces to trade.
    valid_spaces_to_trade = find_valid_spaces_to_trade(player=trade_partner)

    # Present the player with the spaces available for trade.
    log.info("Spaces available for trade:")
    log.info(valid_spaces_to_trade)

    while True:
        # Offer spaces.
        offer_spaces = []

        if isinstance(trade_master, Human):
            offer_spaces_selection = input("Enter indices of properties to offer (comma separated): ")
        else:  # Bot.
            offer_spaces_selection = trade_master.trade_spaces_logic()
        try:
            indices = [int(i.strip()) for i in offer_spaces_selection.split(",") if i.strip()]
            offer_spaces = [valid_spaces_to_trade[i] for i in indices if 0 <= i < len(valid_spaces_to_trade)]
            break  # Got here -> Valid spaces were selected.
        except AttributeError:
            log.warning("Invalid selection")
            continue

    # Present the player with how much cash can be offered.
    log.info(f"Cash to offer - {trade_partner.cash}$")

    while True:
        # Offer cash.
        if isinstance(trade_master, Human):
            offer_cash = input("Enter cash to offer (in $): ")
        else:  # Bot.
            offer_cash = trade_master.trade_cash_logic()

        if not offer_cash.isdigit() or not (0 <= int(offer_cash) <= trade_partner.cash):
            log.warning("Invalid amount")
            continue
        else:
            break  # Got to this point, choice is a valid number.

    # Present the player with how many cards can be offered.
    log.info(f"'Get out of jail free' cards to offer - {trade_partner.free_cards}")

    while True:
        # Check that there are any cards to offer.
        if trade_partner.free_cards == 0:
            offer_free_cards = 0
            break
        else:
            # Player has free cards to potentially offer.

            if isinstance(trade_master, Human):
                offer_free_cards = input("Enter 'Get out of jail free' card(s) to offer: ")
            else:  # Bot.
                offer_free_cards = trade_master.trade_cards_logic()

            if not offer_free_cards.isdigit() or not (0 <= offer_free_cards <= trade_partner.free_cards):
                log.warning("Invalid amount")
                continue
            else:
                break  # Got to this point, choice is a valid number.

    return offer_spaces, int(offer_cash), int(offer_free_cards)


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
    # Transfer spaces from player 2 to player 1.
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
    for space in spaces_to_transfer:
        sender.spaces.remove(space)
        space.owner = recipient
        recipient.spaces.append(space)

        # Check that space is mortgaged.
        if space.is_mortgaged:
            # Check that recipient has enough cash to redeem the space.
            if space.redeem_value < recipient_cash_buffer:
                # Recipient to choose between redeeming or paying mortgage fee for mortgaged properties.

                if isinstance(recipient, Human):
                    action = input("Redeem property or pay mortgage fee (10%): ")
                else:  # Bot.
                    action = recipient.post_trade_redeem_logic()

                while True:
                    match action:
                        case "y":
                            # Redeem space.
                            recipient.cash -= space.redeem_value
                            space.is_mortgaged = False
                            recipient_cash_buffer += (- space.redeem_value) + 0.1 * space.mortgage_value
                            break
                        case "n":
                            # Pay mortgage fee (10%).
                            recipient.cash -= 0.1 * space.mortgage_value
                            break
                        case _:
                            log.warning("Invalid option, choose again")
                            continue
            else:
                # Recipient doesn't have enough cash to redeem. Pays mortgage fee (10%).
                recipient.cash -= 0.1 * space.mortgage_value


def find_valid_spaces_to_trade(player: Player):
    """
    Determine which of a player's owned spaces are eligible for trading. A space is considered valid for trade if:
    - It is a RealEstate space (e.g., a property) and it has no houses or hotels.
    - It is a non-RealEstate space (e.g., a Railroad or Utility).

    :param player: The player whose owned spaces will be evaluated.
    """

    valid_spaces_to_trade = []
    for space in player.spaces:
        # Check if space is of type real-estate.
        if isinstance(space, RealEstate):
            # Check that space has no buildings on it.
            if space.houses == 0 and not space.hotel:
                valid_spaces_to_trade.append(space)
        else:
            # Railroad or utility.
            valid_spaces_to_trade.append(space)

    return valid_spaces_to_trade
