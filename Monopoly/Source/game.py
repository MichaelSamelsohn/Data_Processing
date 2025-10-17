# Imports #
import random

from Monopoly.Settings.monopoly_settings import *
from Monopoly.Source.board import RealEstate, Board, Railroad, Utility, Space
from Monopoly.Source.cards import create_chance_deck, create_community_chest_deck
from Monopoly.Source.player import Player, Human


class Game:
    def __init__(self, players: list[Player]):
        log.info("Initializing a game of monopoly")

        self.board = Board()
        self.current_turn = 0  # Index of the current turn player.
        self.chance_deck = create_chance_deck()
        self.community_chest_deck = create_community_chest_deck()
        self.players = players

        log.success("Game initialized")

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
            player.cash -= JAIL_FINE  # Pay the fine.
            # Reset the jail parameters.
            player.in_jail = False
            player.turns_in_jail = 0
            log.debug(f"{player.name} payed {JAIL_FINE} to get out of jail")

            if player.cash < 0:
                if not self.raise_emergency_cash():
                    self.handle_bankruptcy(player)
                    return

        # Prompt the player for their input.
        while True:
            if isinstance(player, Human):
                jail_string = " / pay" + (" / free" if player.free_cards > 0 else "") \
                    if player.in_jail and not player.post_roll else ""
                action = input(f"{player.name} ({player.cash}$), Please choose action - status / {"roll / " 
                               if not player.post_roll else ""}trade / develop / mortgage{jail_string}"
                               f"{" / end" if player.post_roll else ""}: ").strip().lower()
            else:  # Bot.
                action = player.play_turn_logic()

            match action:
                # Main options.
                case "status":
                    player.status()
                case "roll":
                    if player.post_roll:
                        log.warning(f"{player.name} already rolled the dice on this turn")
                    else:
                        self.roll_handler(player)

                        # Check for bankruptcy.
                        if player.cash < 0:
                            if not self.raise_emergency_cash():
                                self.handle_bankruptcy(player)
                                return
                case "trade":
                    self.trade_handler(player)
                case "develop":
                    self.development_handler(player)
                case "mortgage":
                    self.mortgage_handler(player)

                # Handling jail.
                case "pay" | "free":
                    self.jail_handler(player, action=action)

                # Ending the turn.
                case "end":
                    if not player.post_roll:
                        log.warning(f"{player.name} hasn't rolled their dice this turn")
                    else:
                        log.info(f"{player.name} has ended their turn")

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

        log.debug(f"{player.name} is rolling the dice")
        die1, die2 = random.randint(1, 6), random.randint(1, 6)
        steps = die1 + die2
        log.debug(f"{player.name} rolled {die1} + {die2} = {steps}")
        # Check if roll was a double or not.
        if die1 != die2:
            player.post_roll = True  # Player has rolled the dice for this turn.
            player.consecutive_double_rolls = 0
        else:  # Rolled a double, player deserves another turn.
            player.consecutive_double_rolls += 1

        # Handle case where player rolled three consecutive doubles.
        if player.consecutive_double_rolls == 3:
            log.warning(f"{player.name} rolled three doubles in a row, goes to jail!")
            player.in_jail = True
            player.position = JAIL_POSITION
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
        prev_position = player.position  # Save previous position (used for handling 'GO' passage).
        player.position = (player.position + steps) % 40  # Update player position.

        # Handle case where player passes 'GO' space.
        if player.position < prev_position:
            log.debug(f"{player.name} passed 'GO' and collects 200$")
            player.cash += GO_SALARY

        log.debug(f"{player.name} lands on {self.board.get_space(player.position).name}")

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
            if space.owner is None:
                # Space has no owner, provide the player a choice to buy it.
                if isinstance(player, Human):
                    decision = input(f"Buy {space.name} for ${space.purchase_price}? (y/n): ").strip().lower()
                else:  # Bot.
                    decision = player.position

                if decision == 'y':
                    # Player decided to buy the property.
                    player.cash -= space.purchase_price
                    space.owner = player
                    player.properties.append(space)
                    log.debug(f"{player.name} bought {space.name}")
            elif space.owner != player:
                # Space has an owner and it is not the current turn player.
                rent = self.calculate_rent(space, dice_roll)
                # Transfer rent from current turn player to space owner.
                player.cash -= rent
                space.owner.cash += rent
                log.debug(f"{player.name} pays ${rent} rent to {space.owner.name}")

        # Handle special spaces.
        match space.name:
            case "Go":
                player.cash += GO_SALARY
                log.debug(f"{player.name} collects $200 on GO")
            case "Luxury Tax":
                player.cash -= 100
                log.debug(f"{player.name} pays 100$ in luxury tax")
            case "Income Tax":
                player.cash -= 200
                log.debug(f"{player.name} pays 200$ in income tax")
            case "Chance":
                card = self.chance_deck.draw().apply(player, self)
                # TODO: Add debug line of which card was selected?
            case "Community Chest":
                card = self.community_chest_deck.draw().apply(player, self)
                # TODO: Add debug line of which card was selected?
            case "Go To Jail":
                log.debug(f"{player.name} goes to jail!")
                player.position = JAIL_POSITION
                player.in_jail = True
            case "Jail / Just Visiting":
                log.debug(f"{player.name} is just visiting jail")
            case "Free Parking":
                log.debug(f"{player.name} is resting at Free Parking")

    def calculate_rent(self, space: Space, dice_roll=None):
        """
        Calculates the rent owed by a player who lands on a given space.

        :param space: The board space the player has landed on. This can be an instance of RealEstate, Railroad, or
        Utility.
        :param dice_roll: The result of the player's dice roll. This is required only for Utility rent calculations.

        :return: The amount of rent owed. Returns 0 if the property is mortgaged.
        """

        # Handle real estate property.
        if isinstance(space, RealEstate):
            # Check that property isn't mortgaged.
            if space.is_mortgaged:
                return 0

            # Handle basic rent, houses and hotel cases.
            if space.hotel:
                return space.base_rent * 5  # TODO: Should be some other calculation.
            elif space.houses > 0:
                return space.base_rent * (1 + space.houses)  # TODO: Should be some other calculation.
            else:
                return space.base_rent

        # Handle railroad property.
        elif isinstance(space, Railroad):
            # Check that property isn't mortgaged.
            if space.is_mortgaged:
                return 0

            # Count how many railroads the owner has and multiply the rent accordingly.
            owner = space.owner
            return 25 * sum(1 for s in self.board.spaces if isinstance(s, Railroad) and s.owner == owner)

        # Handle utility property.
        elif isinstance(space, Utility):
            # Check that property isn't mortgaged.
            if space.is_mortgaged:
                return 0

            # Utilities rent based on dice roll and how many utilities owned.
            owner = space.owner
            count = sum(1 for s in self.board.spaces if isinstance(s, Utility) and s.owner == owner)
            if dice_roll is None:  # TODO: Is this necessary?
                raise ValueError("dice_roll needed for utility rent calculation")
            multiplier = 4 if count == 1 else 10 if count == 2 else 0
            return multiplier * dice_roll

    def raise_emergency_cash(self):
        # TODO: To be implemented.
        return True  # lead to bankruptcy if no cash left.

    def handle_bankruptcy(self, player: Player):
        """
        Handles the removal of a player from the game due to bankruptcy. This method performs the following actions:
        - Releases all properties owned by the bankrupt player.
        - Removes the player from the game's active player list.
        - Adjusts the current turn index if necessary to ensure turn order remains valid.
        - Logs the player's removal and announces the winner if only one player remains.

        :param player:The player who has gone bankrupt and is to be removed from the game.
        """

        # Release owned properties.
        for prop in player.properties:
            prop.owner = None
        player.properties.clear()

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

        initiator_property_offer, initiator_cash_offer, initiator_free_cards_offer = (
            self.make_offer(trade_offer_initiator))
        recipient_property_offer, recipient_cash_offer, recipient_free_cards_offer = (
            self.make_offer(trade_offer_recipient))

        log.info("--- TRADE SUMMARY ---")
        log.info(f"{trade_offer_initiator.name} offers to {trade_offer_recipient.name}: "
                 f"{[p.name for p in initiator_property_offer]} + {initiator_cash_offer}$")
        log.info(f"{trade_offer_initiator.name} wants from {trade_offer_recipient.name}: "
                 f"{[p.name for p in recipient_property_offer]} + {recipient_cash_offer}$")

        # Recipient to confirm trade offer.
        if isinstance(trade_offer_recipient, Human):
            confirm = input(f"Does {trade_offer_recipient.name} accept the trade? (y/n): ")
        else:  # Bot.
            confirm = trade_offer_recipient.trade_acceptance_logic()
        if confirm.lower() != 'y':
            log.warning("Trade declined")
            return

        # Perform trade.
        self.execute_trade(
            # Player 1.
            p1=trade_offer_initiator, p1_properties=initiator_property_offer,
            p1_cash=initiator_cash_offer, p1_free_cards=initiator_free_cards_offer,
            # Player 2.
            p2=trade_offer_recipient, p2_properties=recipient_property_offer,
            p2_cash=recipient_cash_offer, p2_free_cards=recipient_free_cards_offer)
        log.success("Trade completed successfully")

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
        log.debug(f"{player.name}'s properties:")
        for i, p in enumerate(player.properties):
            log.debug(f"  [{i}] {p.name}")
        offer_props_selection = input("Enter indices of properties to offer (comma separated): ")
        try:
            indices = [int(i.strip()) for i in offer_props_selection.split(",") if i.strip()]
            offer_props = [player.properties[i] for i in indices if 0 <= i < len(player.properties)]
        except Exception:
            log.warning("Invalid selection")
            offer_props = []

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

        return offer_props, offer_cash, offer_free_cards

    @staticmethod
    def execute_trade(p1, p1_properties, p1_cash, p1_free_cards, p2, p2_properties, p2_cash, p2_free_cards):
        """
        Executes a trade between two players involving properties, cash and 'Get out of jail free' cards. This method
        transfers ownership of the specified properties and adjusts the cash/cards balances of both players according to
        the trade agreement.

        :param p1: The first player involved in the trade.
        :param p1_properties: List of Property objects to transfer from p1 to p2.
        :param p1_cash: Amount of cash p1 gives to p2.
        :param p1_free_cards: Amount of 'Get out of jail free' cards p1 gives to p2.
        :param p2: The second player involved in the trade.
        :param p2_properties: List of Property objects to transfer from p2 to p1.
        :param p2_cash: Amount of cash p2 gives to p1.
        :param p2_free_cards: Amount of 'Get out of jail free' cards p2 gives to p1.
        """

        # Transfer properties.
        for prop in p1_properties:
            p1.properties.remove(prop)
            prop.owner = p2
            p2.properties.append(prop)

        for prop in p2_properties:
            p2.properties.remove(prop)
            prop.owner = p1
            p1.properties.append(prop)

        # Transfer cash.
        p1.cash -= p1_cash
        p2.cash += p1_cash

        p2.cash -= p2_cash
        p1.cash += p2_cash

        # Transfer 'Get out of jail free' cards.
        p1.free_cards -= p1_free_cards
        p2.free_cards += p1_free_cards

        p2.free_cards -= p2_free_cards
        p1.free_cards += p2_free_cards

    # Development functionality #

    def development_handler(self, player: Player):
        """
        Allows a player to build houses or hotels on properties within full color sets they own. This method first
        identifies all full color groups (monopolies) owned by the player. If any are found, the player is prompted to
        choose properties within those groups to develop. The player may build houses evenly across the set and, after
        reaching four houses, can upgrade to a hotel. All development actions deduct the appropriate cost from the
        player's cash.

        :param player: The player attempting to build houses or hotels.
        """

        player_owned_full_sets = self.find_full_sets_owned_by_player(player)

        if not player_owned_full_sets:
            log.warning(f"{player.name} does not own any full color groups to build houses")
            return

        log.debug(f"{player.name} can build houses/hotels on these color groups: {', '.join(player_owned_full_sets)}")

        for color in player_owned_full_sets:
            # Extract the set of the given color.
            properties_to_develop = [s for s in self.board.spaces if isinstance(s, RealEstate) and s.color == color]

            # Display current houses/hotels on each property.
            log.debug(f"{color} properties:")
            for idx, property_to_develop in enumerate(properties_to_develop, 1):
                status = "Hotel" if property_to_develop.hotel else f"{property_to_develop.houses} houses"
                log.debug(f"{idx}. {property_to_develop.name}: {status}")

            while True:
                choice = input(
                    f"Enter property number to build on {color} (or 'done' to finish this color): ").strip().lower()
                if choice == 'done':
                    break

                if not choice.isdigit() or not (1 <= int(choice) <= len(properties_to_develop)):
                    log.warning("Invalid choice, try again")
                    continue

                property_to_develop = properties_to_develop[int(choice) - 1]
                if not self.check_development_possibility(player, properties_to_develop, choice):
                    continue

                if property_to_develop.houses < 4:
                    # Build a house.
                    property_to_develop.houses += 1
                    player.cash -= property_to_develop.house_cost
                    log.debug(f"Built 1 house on {property_to_develop.name} for ${property_to_develop.house_price}")
                elif property_to_develop.houses == 4:
                    # Build a hotel.
                    property_to_develop.houses = 0
                    property_to_develop.hotel = True
                    player.cash -= property_to_develop.hotel_cost
                    log.debug(f"Built hotel on {property_to_develop.name} for {property_to_develop.house_price}$")

    def find_full_sets_owned_by_player(self, player):
        """
        Returns a list of property color sets for which the given player owns all associated properties. This function
        identifies full color groups (monopolies) the player owns, which typically makes those properties eligible for
        development (e.g., building houses or hotels).

        :param player: The player whose property ownership is being evaluated.

        :return: A list of color names (strings) representing the full sets (e.g., 'blue', 'red') the player owns
        completely.
        """

        # Find all unique real estate property colors a player owns.
        player_owned_colors = set(p.color for p in player.properties if isinstance(p, RealEstate))
        player_owned_full_sets = []
        for color in player_owned_colors:
            # Find the color set properties.
            color_full_set = [s for s in self.board.spaces if isinstance(s, RealEstate) and s.color == color]
            # Check that all color set properties are owned by the player.
            if all(p.owner == player for p in color_full_set):
                # Add color set as an option for development.
                player_owned_full_sets.append(color)

        return player_owned_full_sets

    @staticmethod
    def check_development_possibility(player: Player, properties_to_develop, choice):
        """
        Determines whether a player can develop a selected property by building a house or hotel. This method checks the
        following conditions:
        - The selected property does not already have a hotel.
        - Houses are built evenly across the color group (cannot build more than one house above the property with the
          fewest houses).
        - The player has enough cash to afford the development.

        :param player: The player attempting to build on the property.
        :param properties_to_develop: The list of properties within the same color group that can be developed.
        :param choice: The index (1-based) of the property in the list that the player wants to develop.

        :return: True if the property can be developed under the current rules and player's resources, False otherwise.
        """

        property_to_develop = properties_to_develop[int(choice) - 1]

        # Check if building hotel on a property that already has a hotel.
        if property_to_develop.hotel:
            log.warning(f"{property_to_develop.name} already has a hotel")
            return False

        # Check that houses are built evenly.
        min_houses = min(p.houses for p in properties_to_develop)
        if property_to_develop.houses > min_houses:
            log.warning("You must build houses evenly across properties")
            return False

        # Check that player has enough cash to build house/hotel.
        if player.cash < property_to_develop.house_price:
            log.warning(f"Not enough cash to build house ({property_to_develop.house_price}$)")
            return False

        return True

    # Mortgage functionality #

    def mortgage_handler(self, player: Player):
        """
        Handles mortgage-related actions for the given player. This method allows the player to interactively choose one
        of the following actions:
        - 'mortgage': Mortgage a property to receive cash.
        - 'redeem': Redeem a previously mortgaged property by paying its mortgage value plus interest.
        - 'done': Exit the mortgage handler.

        :param player: The player object that is performing the mortgage-related actions.
        """

        while True:
            choice = (input(f"{player.name} ({player.cash}$), Please choose action 'mortgage', 'redeem', or 'done': ")
                      .strip().lower())
            match choice:
                case "mortgage":
                    self.property_asset_management(player, action="mortgage")
                case "redeem":
                    self.property_asset_management(player, action="redeem")
                case "done":
                    break  # Stopping condition.
                case _:
                    log.warning(f"'{choice}' is an unidentified action")

    @staticmethod
    def property_asset_management(player: Player, action: str):
        """
        Allows a player to either mortgage or redeem one of their properties based on the given action. Behavior:
        - If action is "mortgage":
            - Lists all unmortgaged properties owned by the player.
            - Allows the player to select one to mortgage (only if it has no houses or hotels).
            - Adds half the property's value to the player's cash and marks the property as mortgaged.

        - If action is "redeem":
            - Lists all mortgaged properties owned by the player.
            - Allows the player to select one to redeem.
            - Deducts the mortgage value plus 10% interest from the player's cash and marks the property as unmortgaged.

        :param player: The player object whose properties will be considered.
        :param action: Either "mortgage" or "redeem". Determines whether the player is attempting to mortgage an
        unmortgaged property or redeem a mortgaged one.
        """

        debug_string = "mortgage" if action == "mortgage" else "redeem"

        # Determine the relevant properties based on the mortgage direction.
        relevant_properties = [space for space in player.properties if
                               (not space.is_mortgaged if action == "mortgage" else space.is_mortgaged)]
        # If mortgaging, filter real estate properties with houses/hotels (they have to be sold first).
        if action == "mortgage":
            for space in relevant_properties:
                if isinstance(space, RealEstate):
                    if space.hotel or space.houses > 0:
                        relevant_properties.remove(space)

        # Make sure there are relevant properties to mortgage/redeem.
        if not relevant_properties:
            log.debug(f"No properties available to {debug_string}")
            return

        # Present the player with all the relevant properties and let them choose which one to mortgage/redeem.
        log.debug(f"Properties you can {debug_string}:")
        for i, prop in enumerate(relevant_properties, 1):
            value = prop.mortgage_value if action == "mortgage" else prop.redeem_value
            log.debug(f"{i}. {prop.name} ({value}$ cash)")
        idx = input(f"Enter property number to {debug_string}: ").strip()
        if idx.isdigit() and 1 <= int(idx) <= len(relevant_properties):
            # User selected a valid choice.
            property_to_handle = relevant_properties[int(idx) - 1]

            if action == "mortgage":
                # Provide player with mortgage cash and mark the property accordingly.
                property_to_handle.is_mortgaged = True
                player.cash += property_to_handle.mortgage_value
                log.debug(f"{player.name} mortgaged {property_to_handle.name} for {property_to_handle.mortgage_value}$")
            elif action == "redeem":
                # Check that player has enough cash to redeem the property.
                if player.cash < property_to_handle.redeem_value:
                    log.warning(f"Not enough cash to redeem {property_to_handle.name} "
                                f"({property_to_handle.redeem_value}$ required)")
                    return

                # Redeem the property and deduct the cash from the player.
                player.cash -= property_to_handle.redeem_value
                property_to_handle.is_mortgaged = False
                log.debug(f"{player.name} redeemed {property_to_handle.name} by paying "
                          f"{property_to_handle.redeem_value}$")
        else:
            log.warning("Invalid choice")

    # Jail functionality #

    def jail_handler(self, player: Player, action: str):
        """
        TODO: Complete the docstring.
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
                log.debug(f"{player.name} payed {JAIL_FINE} to get out of jail")
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
