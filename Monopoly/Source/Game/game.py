# Imports #
from Monopoly.Source.Game.Functionality.development import *
from Monopoly.Source.Game.Functionality.jail import *
from Monopoly.Source.Game.Functionality.management import *
from Monopoly.Source.Game.Functionality.trade import *
from Monopoly.Source.Game.board import *
from Monopoly.Source.Game.cards import *
from Monopoly.Source.Game.player import *


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
                action = input(f"{player.name} ({player.cash}$), Please choose action - status / {"roll / " 
                               if not player.post_roll else ""}trade / develop / manage"
                               f"{" / jail" if player.in_jail and not player.post_roll else ""}"
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
                        self.roll_handler(player=player)
                        # Check if player became bankrupt after the roll.
                        if player.is_bankrupt:
                            self.bankruptcy_handler(player=player)
                            return  # Turn ends for bankrupt player.
                case "trade":
                    trade_handler(board=self.board, players=self.players, trade_offer_initiator=player)
                case "develop":
                    development_handler(board=self.board, players=self.players, player=player)
                case "manage":
                    management_handler(board=self.board, players=self.players, player=player)

                # Handling jail.
                case "jail":
                    jail_handler(board=self.board, players=self.players, player=player)

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

            # Check if player is in jail.
            if player.in_jail:
                # Player didn't roll double, stays in jail, no move allowed.
                log.info(f"{player.name} didn't roll a double, remains in jail")
                return  # Player remains in jail.
        else:
            # Rolled a double.

            # Check if player is in jail.
            if player.in_jail:
                # Player gets out of jail, but doesn't get another turn.
                log.info(f"{player.name} rolled a double, gets out of jail")
                player.in_jail = False
                player.post_roll = True  # No more rolls allowed for this turn (regardless of double).
                player.consecutive_double_rolls = 0  # Reset the counter.
            else:
                # Player not in jail, deserves another turn.
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
                        choice = input(f"Purchase {space.name} for ${space.purchase_price}? (y/n): ").strip().lower()
                    else:  # Bot.
                        choice = player.buy_space_choice(board=self.board, players=self.players, space=space)

                    if choice == "y":
                        # Player decided to buy the property.
                        player.cash -= space.purchase_price
                        space.owner = player
                        player.spaces.append(space)
                        log.info(f"{player.name} bought {space.name} for {space.purchase_price}$")
                        return
                    elif choice == "n":
                        log.info(f"{player.name} declined to buy the space. An auction will determine the new owner")
                        self.auction(space=space)
                        return
                    else:
                        log.warning("Invalid choice, please choose again")
                        continue
                elif space.owner != player:
                    # Space has an owner and it is not the current turn player.

                    rent = calculate_rent(board=self.board, space=space, dice_roll=dice_roll)
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
        log.info("~~~ AUCTION ~~~")
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
                            new_bid = player.auction_choice(board=self.board, players=self.players,
                                                            space=space, latest_bid=latest_bid)

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
                    transfer_spaces(board=self.board, players=self.players,
                                    sender=debtor, recipient=creditor, spaces_to_transfer=debtor.spaces)
                else:
                    # Bank is the creditor. Auction all spaces (unmortgaged).
                    for space in debtor.spaces:
                        space.owner = None
                        self.auction(space=space)

                # Declaring bankruptcy.
                log.warning(f"{debtor.name} is unable to pay debt, declared bankrupt!")
                debtor.spaces = []
                debtor.cash = 0
                debtor.free_cards = 0
                debtor.is_bankrupt = True

            else:
                log.warning(f"{debtor.name} lacks cash to pay debt, will have to sell or mortgage")

                while True:
                    # Let the player choose the cash raising method.
                    if isinstance(debtor, Human):
                        choice = input("Choose one of the following: sell / mortgage: ")
                    else:  # Bot.
                        choice = debtor.raise_cash_choice(board=self.board, players=self.players, )

                    match choice:
                        case "sell":
                            sell(board=self.board, players=self.players, player=debtor)
                        case "mortgage":
                            mortgage(board=self.board, players=self.players, player=debtor)
                        case "automate":
                            # Relevant only for dummy bot.
                            if isinstance(debtor, Human):
                                log.warning("This option can only be used by bots!")
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
