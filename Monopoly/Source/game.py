# Imports #
from Monopoly.Source.Bots.dummy import Dummy
from Monopoly.Source.cards import *
from Monopoly.Source.player import Player, Human
from Monopoly.Source.service_functions import *


class Game:
    def __init__(self, players: list[Player]):
        log.info("Initializing a game of monopoly")

        self.board = Board()
        self.current_turn = 0  # Index of the current turn player.
        self.chance_deck = create_chance_deck()
        self.community_chest_deck = create_community_chest_deck()
        self.players = players

        log.info("Game initialized")
        log.info("")

    def play_turn(self):
        """
        Executes a single turn for the current player. This method determines which player's turn it is, prompts them to
        choose an action, and then executes the corresponding method based on the input. Valid actions include:
            * 'status' - Information on the current player.
            * 'roll' (only if the player hasn't rolled this turn yet) - The player rolls the dice and progresses
              accordingly.
            * 'trade' - The player initiates a trade with another player.
            * 'develop' - The player attempts to develop properties.
            * 'mortgage' - The player attempts to mortgage/un-mortgage property.
            * 'pay' (only if the player is in jail) - The player pays the fine to get out of jail.
            * 'free' (only if the player is in jail and has a 'get out of jail free' card) - Player uses theirs 'get out
              of jail free' card to get out of jail.
            * 'end' (only if the player has already rolled this turn) - The player ends their turn.
        """

        # Identify the player whose turn is current.
        player = self.players[self.current_turn]

        # Check if player is in jail for three turns.
        if player.turns_in_jail == 3:
            self.pay_debt(debtor=player, debt=JAIL_FINE)
            if player.is_bankrupt:
                self.bankruptcy_handler(player=player)
            # Reset the jail parameters.
            player.in_jail = False
            player.turns_in_jail = 0
            log.info(f"{player.name} payed {JAIL_FINE} to get out of jail")

        # Prompt the player for their input.
        while True:
            if isinstance(player, Human):
                jail_string = " / pay" + (" / free" if player.free_cards > 0 else "") \
                    if player.in_jail and not player.post_roll else ""
                action = input(f"{player.name} ({player.cash}$), Please choose action - status / {"roll / " 
                               if not player.post_roll else ""}trade / develop / manage{jail_string}"
                               f"{" / end" if player.post_roll else ""}: ").strip().lower()
            else:  # Bot.
                action = player.play_turn_logic(board=self.board, players=self.players)

            match action:
                # Main options.
                case "status":
                    player.status()
                case "roll":
                    if player.post_roll:
                        log.warning(f"{player.name} already rolled the dice on this turn")
                    else:
                        self.roll_handler(player)
                        # Check if player became bankrupt after the roll.
                        if player.is_bankrupt:
                            self.bankruptcy_handler(player=player)
                            return  # Turn ends for bankrupt player.
                case "trade":
                    self.trade_handler(player)
                case "develop":
                    self.development_handler(player)
                case "manage":
                    self.management_handler(player)

                # Handling jail.
                case "pay" | "free":
                    self.jail_handler(player, action=action)

                # Ending the turn.
                case "end":
                    if not player.post_roll:
                        log.warning(f"{player.name} hasn't rolled their dice this turn")
                    else:
                        log.info(f"{player.name} has ended their turn")
                        player.status()

                        player.post_roll = False  # Resetting so that next time player can roll the dice on their turn.
                        # If player in jail, increment their counter.
                        if player.in_jail:
                            player.turns_in_jail += 1
                        # Updating the turn number.
                        self.current_turn = (self.current_turn + 1) % len(self.players)

                        return  # Turn ends.

                # Unidentified action was prompted.
                case _:
                    log.warning(f"'{action}' is an unidentified action")

    # Roll functionality #

    def roll_handler(self, player: Player):
        """
        Simulates a player's roll by two six-sided dice, updating their position, and handling the outcome of
        the space they land on. The function performs the following steps:
            1. Rolls two dice and calculates the total.
            2. Moves the player forward by the total rolled steps.
            3. Triggers any effects associated with the new space.
            4. Checks if the player's cash has fallen below zero and handles bankruptcy if so.

        :param player: The player object representing the current player taking their turn.
        """

        # Roll dice.
        die1, die2 = random.randint(1, 6), random.randint(1, 6)
        steps = die1 + die2
        log.info(f"{player.name} rolled {die1} + {die2} = {steps}")
        # Check if roll was a double or not.
        if die1 != die2:
            player.post_roll = True  # Player has rolled the dice for this turn.
            player.consecutive_double_rolls = 0
        else:  # Rolled a double, player deserves another turn.
            log.info(f"Rolled a double, {player.name} gets another roll")
            player.consecutive_double_rolls += 1

        # Handle case where player rolled three consecutive doubles.
        if player.consecutive_double_rolls == 3:
            log.warning(f"{player.name} rolled three doubles in a row, goes to jail!")
            player.in_jail = True
            player.position = 10  # Jail position on the board.
            player.post_roll = True  # No more rolls allowed for this turn.
            player.consecutive_double_rolls = 0  # Reset the counter.
            return  # No point to continue for all other checks (handled above).

        # Update player position.
        self.move_player(player, steps)
        # Handle new position space.
        self.handle_space(player, dice_roll=steps)

    def move_player(self, player: Player, steps: int):
        """
        Moves the given player forward by a specified number of steps on the board. If the move causes the player to
        pass the 'GO' space (i.e., position 0), the player receives the 'GO' salary.
        Note - The player's new position is calculated modulo 40 to wrap around the board.

        :param player: The player object to move.
        :param steps: The number of spaces to move the player forward.
        """

        # Update player position.
        previous_position = player.position  # Save previous position (used for handling 'GO' passage).
        player.position = (player.position + steps) % 40  # Update player position.

        # Handle case where player passes 'GO' space.
        if player.position < previous_position:
            log.info(f"{player.name} passed 'GO' and collects 200$")
            player.cash += GO_SALARY

        log.info(f"{player.name} lands on {self.board.get_space(player.position).name}")

    def handle_space(self, player: Player, dice_roll=None):
        """
        Handles the logic when a player lands on a board space. This method determines the type of space the player has
        landed on and applies the corresponding game rules. It covers purchasing unowned properties, paying rent, and
        triggering effects from special board spaces such as Chance, Community Chest, and Jail.

        Behavior:
        - If the space is a Property, Railroad, or Utility:
            - If unowned, the player is given the option to purchase.
            - If owned by another player, rent is paid to the owner.
        - If the space is a special type (e.g. Go, Tax, Chance, etc.):
            - Executes the effect specific to that space.

        :param player: The player whose turn is currently being handled.
        :param dice_roll: The total rolled on the dice for this turn, used to calculate rent on utilities.
        """

        # Identify the new space of the player whose turn is current.
        space = self.board.spaces[player.position]

        # Handle non-special spaces - Property, railroad and utility.
        if isinstance(space, RealEstate) or isinstance(space, Railroad) or isinstance(space, Utility):
            while True:
                # Check the ownership status of the space.
                if space.owner is None:
                    # Space has no owner.

                    # Check if player has enough money to buy space.
                    if player.cash < space.purchase_price:
                        # Player can't afford the purchasing price, going to auction it.
                        self.auction(space=space)
                        return

                    if isinstance(player, Human):
                        decision = input(f"Purchase {space.name} for ${space.purchase_price}? (y/n): ").strip().lower()
                    else:  # Bot.
                        decision = player.buy_space_logic(space=space)

                    if decision == "y":
                        # Player decided to buy the property.
                        player.cash -= space.purchase_price
                        space.owner = player
                        player.spaces.append(space)
                        log.info(f"{player.name} bought {space.name} for {space.purchase_price}$")
                        return
                    elif decision == "n":
                        log.info(f"{player.name} declined to buy the space. An auction will determine the new owner")
                        self.auction(space=space)
                        return
                    else:
                        log.warning("Invalid choice, please choose again")
                        continue
                elif space.owner != player:
                    # Space has an owner and it is not the current turn player.

                    rent = self.calculate_rent(space, dice_roll)
                    log.info(f"{player.name} needs to pay rent of {rent}$ to {space.owner.name}")
                    self.pay_debt(debtor=player, debt=rent, creditor=space.owner)

                    return
                else:
                    # Space owner is the player.
                    return

        # Handle special spaces.
        match space.name:
            case "Go":
                log.info(f"{player.name} collects 200$ on GO")
                player.cash += GO_SALARY
            case "Luxury Tax":
                log.info(f"{player.name} pays 100$ in luxury tax")
                self.pay_debt(debtor=player, debt=100)
            case "Income Tax":
                log.info(f"{player.name} pays 200$ in income tax")
                self.pay_debt(debtor=player, debt=200)
            case "Chance":
                self.chance_deck.draw().apply(player, self)
            case "Community Chest":
                self.community_chest_deck.draw().apply(player, self)
            case "Go To Jail":
                log.info(f"{player.name} goes to jail!")
                player.in_jail = True
                player.position = 10  # Jail position on the board.
                player.post_roll = True  # Player has rolled the dice for this turn and landed in jail.
                player.consecutive_double_rolls = 0  # Reset the counter.
            case "Jail / Just Visiting":
                log.info(f"{player.name} is just visiting jail")
            case "Free Parking":
                log.info(f"{player.name} is resting at free parking")

    def calculate_rent(self, space: Space, dice_roll=None):
        """
        Calculates the rent owed by a player who lands on a given space.

        :param space: The board space the player has landed on. This can be an instance of RealEstate, Railroad, or
        Utility.
        :param dice_roll: The result of the player's dice roll. This is required only for Utility rent calculations.

        :return: The amount of rent owed. Returns 0 if the property is mortgaged.
        """

        # Check that property isn't mortgaged.
        # Note - dice_roll == None only when a chance card sends the player to a utility/railroad with special rent
        # fee override.
        if space.is_mortgaged and dice_roll is not None:
            return 0

        # Handle real estate property.
        if isinstance(space, RealEstate):
            # Handle basic rent, full set rent, houses and hotel cases.
            if space.hotel:
                return space.hotel_rent
            elif space.houses > 0:
                return {
                    1: space.one_house_rent,
                    2: space.two_house_rent,
                    3: space.three_house_rent,
                    4: space.four_house_rent,
                }.get(space.houses)
            elif is_monopoly_owned_by_player(player=space.owner, color=space.color, board=self.board):
                return 2 * space.base_rent
            else:  # Owner doesn't own the monopoly.
                return space.base_rent

        # Handle railroad property.
        elif isinstance(space, Railroad):
            # Count how many railroads the owner has and multiply the rent accordingly.
            owner = space.owner
            rent = 25 * sum(1 for s in self.board.spaces if isinstance(s, Railroad) and s.owner == owner)
            # Check if we got here through a chance card.
            rent *= 2 if dice_roll is None else 1
            return rent

        # Handle utility property.
        elif isinstance(space, Utility):
            # Check if we got here through a chance card.
            if dice_roll is None:
                log.info(f"Rolling dice to determine rent")
                die1, die2 = random.randint(1, 6), random.randint(1, 6)
                dice_roll = die1 + die2
                log.debug(f"Rolled {die1} + {die2} = {dice_roll}")
                return 10 * dice_roll  # Chance card overrides normal rent rules.

            # Utilities rent based on dice roll and how many utilities owned.
            owner = space.owner
            count = sum(1 for s in self.board.spaces if isinstance(s, Utility) and s.owner == owner)
            multiplier = 4 if count == 1 else 10 if count == 2 else 0
            return multiplier * dice_roll

    def auction(self, space: Space):
        """
        Conducts an auction for a property space among all players. Each player is prompted in turn to place a bid
        higher than the current highest bid or to pass. The auction starts with a default minimum bid of 10. If a player
        places a valid bid (numeric and greater than the current highest), they become the current highest bidder. If
        all players pass in the first round, the property remains unsold. The auction ends when all players except the
        latest bidder have passed in a single round.

        :param space: The property space being auctioned.
        """

        log.info("")  # Empty line to start the auction print.
        log.info("~~~ Auction ~~~")
        log.info(f"Auction is held for {space.name} with initial bid of 10$")

        latest_bid = 10
        auction_winner = None
        no_bid_counter = -1  # Accounts for the first round, where everyone can pass the round (no auction winner).

        while True:
            # Bidding round of all active players.
            for player in self.players:
                # Check that current player can even participate in the bidding (has enough cash).
                if player.cash < latest_bid:
                    log.info(f"{player.name} passed this round since bid is higher than cash balance")
                    no_bid_counter += 1
                else:
                    # Current player has enough cash to make a higher bid.
                    while True:
                        # Allow player to make a new bid.
                        if isinstance(player, Human):
                            new_bid = input(f"{player.name}, offer new bid: ")
                        else:  # Bot.
                            new_bid = player.auction_logic(space=space, latest_bid=latest_bid)

                        if new_bid.isdigit() and latest_bid < int(new_bid):
                            # Check that new bid is within the player ability to pay.
                            if int(new_bid) > player.cash:
                                log.warning("New bid is higher than player can pay")
                            else:
                                # Valid bid was made
                                log.info(f"{player.name} made a new bid for {new_bid}$")
                                latest_bid = int(new_bid)
                                auction_winner = player
                                no_bid_counter = 0
                                break
                        elif new_bid.isdigit() and latest_bid >= int(new_bid):
                            # Invalid bid was made.
                            log.warning(f"New bid, {new_bid}, is equal or smaller then latest bid, {latest_bid}")
                        elif not new_bid.isdigit():
                            # Player passes current bidding round.
                            log.info(f"{player.name} passed this bidding round")
                            no_bid_counter += 1
                            break

                # Check for auction end.
                if no_bid_counter == len(self.players) - 1:
                    # No bids were made for an entire round since last one was made.

                    # Relevant for first round only - Check if first round held no bids.
                    if not auction_winner:
                        log.warning("No player made a bid, space returns to bank ownership")
                    else:
                        # Relevant for rest of the auction - All players (except last bidder) held no bids.
                        space.owner = auction_winner
                        auction_winner.spaces.append(space)
                        auction_winner.cash -= latest_bid
                        log.info(f"{auction_winner.name} won the auction with highest bid - {latest_bid}$")

                    log.info("")  # Empty line to end the auction print.
                    return  # Auction ended.

    def pay_debt(self, debtor: Player, debt: int, creditor=None):
        """
        Attempts to settle a debt for a given player. The method handles both direct cash payments and asset liquidation
        when necessary.

        If the debtor has enough cash to cover the debt, the amount is directly deducted from their cash and optionally
        added to the creditor’s balance.

        If the debtor lacks sufficient cash:
        - The method evaluates if the debtor can raise enough by selling or
          mortgaging their assets (properties, houses, hotels).
        - If they cannot raise enough, they are declared bankrupt:
            - If a creditor is specified, their assets (spaces and free cards)
              are transferred to the creditor.
            - If no creditor is specified (i.e., the bank), properties are
              unmortgaged and sent to auction.
        - If they can raise enough, the player is prompted (or automated, for bots)
          to sell or mortgage assets until they can pay the debt.

        :param debtor: The player who owes the debt.
        :param debt: The amount the debtor must pay.
        :param creditor: The recipient of the payment. If None, the bank is considered the creditor.
        """

        # Check if the debtor has cash to pay the debt immediately.
        if debtor.cash > debt:
            debtor.cash -= debt
            if creditor:
                log.info(f"Direct payment of {debt}$ was made from {debtor.name} to {creditor.name}")
                creditor.cash += debt  # Creditor gets their due.

        else:
            # Player lacks the necessary cash to pay the debt directly.

            # Asses how much cash can the player raise in total.
            total_cash = 0
            for space in debtor.spaces:
                # Add mortgage value (if not already mortgaged).
                if not space.is_mortgaged:
                    total_cash += space.mortgage_value
                # Add house/hotel sell values (if space has any).
                if isinstance(space, RealEstate):
                    total_cash += (space.houses + (1 if space.hotel else 0)) * space.building_sell

            if total_cash < debt:
                # Player can't repay his debt.

                # Selling/mortgaging everything the player owns.
                for space in debtor.spaces:
                    space.is_mortgaged = True if creditor else False  # Bank immediately auctions unmortgaged spaces.
                    space.hotel = False
                    space.houses = 0

                # Non-bank creditor gets all assets.
                if creditor:
                    # Transfer cash.
                    creditor.cash += total_cash
                    # Transfer 'Get out of jail free' cards.
                    creditor.free_cards += debtor.free_cards
                    # Transfer all (mortgaged) spaces.
                    self.transfer_spaces(sender=debtor, recipient=creditor, spaces_to_transfer=debtor.spaces)
                else:
                    # Bank is the creditor. Auction all spaces (unmortgaged).
                    for space in debtor.spaces:
                        space.owner = None
                        self.auction(space=space)

                # Declaring bankruptcy.
                debtor.spaces = []
                debtor.cash = 0
                debtor.free_cards = 0
                debtor.is_bankrupt = True

            else:
                log.warning(f"{debtor} lacks cash to pay debt, will have to sell or mortgage")

                while True:
                    # Let the player choose the cash raising method.
                    if isinstance(debtor, Human):
                        choice = input("Choose one of the following: sell / mortgage: ")
                    else:  # Bot.
                        choice = debtor.raise_cash_logic()

                    match choice:
                        case "sell":
                            self.sell(player=debtor)
                        case "mortgage":
                            self.mortgage(player=debtor)
                        case "automate":
                            # Relevant only for dummy bot.
                            if not isinstance(debtor, Dummy):
                                log.warning("This option can only be used by dummy bots!")
                                continue

                            # Dummy bot logic doesn't allow to have houses, only spaces (unmortgaged or mortgaged via
                            # trade).
                            for space in debtor.spaces:
                                if not space.is_mortgaged:
                                    # Mortgage space.
                                    debtor.cash += space.mortgage_value
                                    space.is_mortgaged = True

                                # Check if enough cash was raised.
                                if debtor.cash > debt:
                                    break
                        case _:
                            log.warning("Invalid choice")
                            continue

                    # Check if player raised enough to pay debt.
                    if debtor.cash > debt:
                        debtor.cash -= debt
                        if creditor:
                            # Creditor gets their due.
                            creditor.cash += debt
                        return  # Debtor paid their debt.

    def bankruptcy_handler(self, player: Player):
        """
        Handles the removal of a player from the game due to bankruptcy. This method performs the following actions:
        - Releases all properties owned by the bankrupt player.
        - Removes the player from the game's active player list.
        - Adjusts the current turn index if necessary to ensure turn order remains valid.
        - Logs the player's removal and announces the winner if only one player remains.

        :param player:The player who has gone bankrupt and is to be removed from the game.
        """

        # Remove player from game.
        self.players.remove(player)

        # Adjust current turn if necessary.
        self.current_turn -= 1
        if self.current_turn < 0:
            self.current_turn = 0

        log.info(f"{player.name} has been removed from the game")

        # Check for game end.
        if len(self.players) == 1:
            winner = self.players[0]
            log.success(f"🏆 {winner.name} is the last player standing and wins the game!")
            exit()

    # Trade functionality #

    def trade_handler(self, trade_offer_initiator: Player):
        """
        Handles the process of initiating and executing a trade between two players. Prompts the initiator to specify
        another player to trade with, gathers the trade offers (properties and cash) from both parties, presents a trade
        summary, and asks the recipient to accept or decline the offer. If the recipient agrees, the trade is executed
        and the appropriate assets (properties and cash) are exchanged between the two players.

        :param trade_offer_initiator: The player who initiates the trade.
        """

        # Get trade recipient.
        trade_offer_recipient_name = input("Enter the name of the player you want to trade with: ").strip()
        trade_offer_recipient = next((player for player in self.players if player.name == trade_offer_recipient_name),
                                     None)
        # Make sure the recipient exists and is not the same player as the initiator.
        if trade_offer_recipient_name == trade_offer_initiator.name or trade_offer_recipient is None:
            log.warning("Invalid player name")
            return

        initiator_space_offer, initiator_cash_offer, initiator_free_cards_offer = (
            self.make_offer(trade_offer_initiator))
        recipient_space_offer, recipient_cash_offer, recipient_free_cards_offer = (
            self.make_offer(trade_offer_recipient))

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
                    self.execute_trade(
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

    @staticmethod
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

    def execute_trade(self, player1: Player, player1_spaces: list, player1_cash: int, player1_free_cards: int,
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
        self.transfer_spaces(sender=player1, recipient=player2, spaces_to_transfer=player1_spaces)
        self.transfer_spaces(sender=player2, recipient=player1, spaces_to_transfer=player2_spaces)

    @staticmethod
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
                        action = recipient.redeem_logic()

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

    # Development functionality #

    def development_handler(self, player):
        """
        Handles development-related actions for the given player. This method allows the player to interactively choose
        one of the following actions:
        - 'build': Build a house/hotel.
        - 'sell': Sell a house/hotel.
        - 'end': Exit the mortgage handler.

        :param player: The player object that is performing the development-related actions.
        """

        while True:
            if isinstance(player, Human):
                choice = (input(f"{player.name} ({player.cash}$), Please choose action 'build', 'sell', or 'end': ")
                          .strip().lower())
            else:  # Bot.
                choice = player.development_logic()

            match choice:
                case "build":
                    self.build(player)
                    return
                case "sell":
                    self.sell(player)
                    return
                case "end":
                    return
                case _:
                    log.warning(f"'{choice}' is an unidentified action")

    def build(self, player: Player):
        """
        Allows a player to build houses or hotels on properties within full color sets they own. This method first
        identifies all full color groups (monopolies) owned by the player. If any are found, the player is prompted to
        choose properties within those groups to develop. The player may build houses evenly across the set and, after
        reaching four houses, can upgrade to a hotel. All development actions deduct the appropriate cost from the
        player's cash.

        :param player: The player attempting to build houses or hotels.
        """

        # Find all player owned valid spaces with option to build on.
        valid_spaces_to_build_on = find_valid_spaces_to_build_on(player=player, board=self.board)
        if not valid_spaces_to_build_on:
            log.warning(f"{player.name} has no spaces to build on")
            return

        # Present player with all valid options.
        log.info("Spaces to buy on:")
        log.print_data(data=valid_spaces_to_build_on, log_level="info")

        while True:
            # Player to choose valid monopoly.
            if isinstance(player, Human):
                choice = input(f"Enter monopoly color to build on ('end' to finish building): ").strip().lower()
                if choice == "end":
                    return
            else:  # Bot.
                choice = player.monopoly_build_selection_logic()

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
                    choice = player.space_build_selection_logic()

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

    def sell(self, player: Player):
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
        """

        # Find all player owned valid spaces with option to sell from.
        valid_spaces_to_sell_from = find_valid_spaces_to_sell_from(player=player, board=self.board)
        if not valid_spaces_to_sell_from:
            log.warning(f"{player.name} does not own any spaces with houses/hotels to sell")
            return

        # Present player with all valid options.
        log.info("Spaces to sell from:")
        log.print_data(data=valid_spaces_to_sell_from, log_level="info")

        while True:
            # Player to choose monopoly to sell houses/hotels.
            if isinstance(player, Human):
                choice = input(f"Enter monopoly number to sell from on ('end' to finish selling): ").strip().lower()
                if choice == "end":
                    return
            else:  # Bot.
                choice = player.monopoly_sell_selection_logic()

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
                    player.space_sell_selection_logic()

                if not choice.isdigit() or not (1 <= int(choice) <= len(selected_spaces_to_sell_from)):
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

    # Management functionality #

    def management_handler(self, player: Player):
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
                choice = player.management_logic()

            match choice:
                case "mortgage":
                    self.mortgage(player=player)
                case "redeem":
                    self.redeem(player=player)
                case "done":
                    break  # Stopping condition.
                case _:
                    log.warning(f"'{choice}' is an unidentified action")

    @staticmethod
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
        log.info(valid_spaces_to_mortgage)

        while True:
            # Player to choose which space to mortgage.
            if isinstance(player, Human):
                choice = input(f"Enter space number to mortgage ('end' to finish): ").strip().lower()
                if choice == "end":
                    return
            else:  # Bot.
                choice = player.mortgage_logic()

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

    @staticmethod
    def redeem(player: Player):
        """
        Allows the player to redeem (unmortgage) eligible properties. This method checks all properties owned by the
        given player and presents a list of mortgaged properties that the player can afford to redeem based on their
        current cash. The player is prompted to select which property to redeem by entering its number. After each
        redemption, the method recursively calls itself to allow the player to continue redeeming additional properties
        if they wish.

        :param player: The player attempting to redeem mortgaged properties.
        """

        while True:
            # Find any spaces the player owns that are mortgaged and player has enough cash to redeem.
            spaces_to_redeem = [space for space in player.spaces if space.is_mortgaged and
                                player.cash > space.redeem_value]
            # Make sure there are spaces to redeem.
            if not spaces_to_redeem:
                log.warning(f"No spaces available to redeem")
                return

            # Present the player with all the relevant spaces to redeem.
            log.info(f"Properties you can redeem:")
            for i, prop in enumerate(spaces_to_redeem, 1):
                log.info(f"{i}. {prop.name} ({prop.redeem_value}$ cash)")

            # Player to choose which space to redeem.
            if isinstance(player, Human):
                choice = input(f"Enter space number to redeem ('end' to finish): ").strip().lower()
            else:  # Bot.
                choice = player.redeem_logic()

            if choice == "end":
                return
            else:
                if not choice.isdigit() or not (1 <= int(choice) <= len(spaces_to_redeem)):
                    log.warning("Invalid choice, try again")
                    continue

            # Got to this point, choice is a valid number.

            # Redeem space.
            space_to_redeem = spaces_to_redeem[int(choice) - 1]
            space_to_redeem.is_mortgaged = False
            player.cash -= space_to_redeem.redeem_value
            log.info(f"{player.name} redeemed {space_to_redeem.name} for {space_to_redeem.redeem_value}$")

    # Jail functionality #

    @staticmethod
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
