# Imports #
from collections import Counter
from Monopoly.Source.Game.game import *


class Easy(Player):
    """Purpose of this bot is to serve as an amateurish playing partner."""
    def __init__(self, name):
        super().__init__(name=name, role="Easy bot")

        # Cash buffers.
        self.safety_buffer = 500     # This buffer is defined for purchasing houses/hotels.
        self.emergency_buffer = 200  # This emergency buffer is used to pay fines and rent.

        # Action parameters.
        self.development_action = None
        self.management_action = None
        self.jail_action = None
        self.is_active_action_taken = False
        self.is_emergency_freeze = False
        self.is_trade_attempted = False

        # Trade parameters.
        self.trade_partner = None
        self.trade_cash = None
        self.trade_spaces = None

        # Build parameters.
        self.monopoly_build = None
        self.space_build = None

        # Sell parameters.
        self.monopoly_sell = None
        self.space_sell = None

        # Mortgage parameters.
        self.space_mortgage = None

        # Redeem parameters.
        self.space_redeem = None

    # Main logic #

    def play_turn_logic(self, board, players):
        # Check if we are in jail (before rolling the dice).
        if self.in_jail and not self.post_roll:
            # We are in jail and haven't rolled the dice yet (turn start).

            # JAIL #

            log.logic(f"{self.name} - In jail, trying to get as soon as possible")

            # Primary option - Use a 'Get out of jail free' card.
            if self.free_cards > 0:
                log.logic(f"{self.name} - Using a 'Get out of jail free' card to get out of jail")
                self.jail_action = "free"
                return "jail"

            # Secondary option - Pay to get out of jail.
            if self.cash - JAIL_FINE > self.emergency_buffer:
                log.logic(f"{self.name} - Paying jail fine ({JAIL_FINE}$) without breaching emergency buffer "
                          f"(cash balance after fine - {self.cash}$ - {JAIL_FINE}$ > {self.emergency_buffer})")
                self.jail_action = "pay"
                return "jail"

            # Got to this point, unable to free ourselves from jail this turn. Will try our luck with rolling a double.
            log.logic("Unable to forcibly get out of jail, will try rolling a double")

        # Check if we are able to make an active cash spending action.
        if self.cash >= self.emergency_buffer and not self.is_emergency_freeze:
            # We have enough cash, consider building a house/hotel (one per turn).
            if not self.is_active_action_taken:
                # Able to perform an active cash spending action - buy/redeem.

                # DEVELOPMENT - BUYING HOUSE/HOTEL #

                # Find valid spaces to build on.
                valid_spaces_to_build_on = find_valid_spaces_to_build_on(player=self, board=board)
                if valid_spaces_to_build_on:
                    cash_needed = []  # To track the cash lacking to buy, in case we can't buy anything.
                    for monopoly in valid_spaces_to_build_on:
                        # Check if we have enough cash to build without dropping below emergency buffer.
                        build_cost = valid_spaces_to_build_on[monopoly][0].building_cost
                        if self.cash - build_cost > self.emergency_buffer:
                            log.logic(f"{self.name} - Buying a building (cost - {build_cost}$) to gain higher "
                                      f"rent, without breaching emergency buffer (cash balance after purchase, "
                                      f"{self.cash}$ - {build_cost}$ > {self.emergency_buffer}$)")

                            # Not much thought over monopoly selection - First found that we are able to develop.
                            self.monopoly_build = monopoly
                            # Not much thought over space selection - Select a random space.
                            self.space_build = random.randint(0, len(valid_spaces_to_build_on[monopoly]) - 1)
                            self.is_active_action_taken = True
                            self.development_action = "build"
                            return "develop"
                        else:
                            # Lacking the cash to develop.
                            cash_needed.append(self.emergency_buffer - (self.cash - build_cost))

                    # Check if we lack the cash to develop.
                    if not self.monopoly_build and not self.space_build:
                        log.logic(f"{self.name} - Unable to develop an owned monopoly due to lack of cash, need at "
                                  f"least {min(cash_needed)}$ to develop without breaching emergency buffer")

                # Got to this point, no valid spaces to build on.

                # MANAGEMENT - REDEMPTION #

                # Find valid spaces to redeem.
                valid_spaces_to_redeem = find_valid_spaces_to_redeem(player=self)
                if valid_spaces_to_redeem:
                    cash_needed = []  # To track the cash lacking to redeem, in case we can't redeem anything.
                    for space in valid_spaces_to_redeem:
                        # Check if we have enough cash to redeem without dropping below emergency buffer.
                        if self.cash - space.redeem_value > self.emergency_buffer:
                            log.logic(f"{self.name} - Redeeming space (cost - {space.redeem_value}$) to gain "
                                      f"opportunity to build, without breaching emergency buffer "
                                      f"(cash balance after purchase, "
                                      f"{self.cash}$ - {space.redeem_value}$ > {self.emergency_buffer}$)")

                            # Not much thought over space selection - Select a random space.
                            self.space_redeem = random.randint(0, len(valid_spaces_to_redeem) - 1)
                            self.is_active_action_taken = True
                            self.management_action = "redeem"
                            return "manage"
                        else:
                            # Lacking the cash to develop.
                            cash_needed.append(self.emergency_buffer - (self.cash - space.redeem_value))

                    # Check if we lack the cash to redeem.
                    if not self.space_redeem:
                        log.logic(f"{self.name} - Unable to redeem an owned space due to lack of cash, need at "
                                  f"least {min(cash_needed)}$ to redeem without breaching emergency buffer")

                # Got to this point, no valid spaces to redeem.

                # TRADE #

                # Check that we haven't tried to trade this turn.
                if not self.is_trade_attempted:

                    # Find monopolies that are "missing" one space to completion.
                    monopoly_count = dict(Counter([space.color for space in self.spaces
                                                   if isinstance(space, RealEstate)]))
                    monopoly_count_difference = {k: MONOPOLY_COUNT.get(k, 0) - monopoly_count.get(k, 0)
                                                 for k in MONOPOLY_COUNT.keys() | monopoly_count.keys()}
                    close_monopolies = [key for key, value in monopoly_count_difference.items() if value == 1]

                    # Check if there are possible monopolies to complete.
                    if close_monopolies:
                        missing_spaces = []
                        # Scan all players and compile a dictionary of all "missing" spaces.
                        for player in players:
                            if player == self:
                                continue  # We cannot trade with ourselves.

                            # Find valid spaces to trade for the current player.
                            # Note - It is important that we use this function, to have the exact indices presented in
                            # the trade function.
                            valid_spaces_to_trade = find_valid_spaces_to_trade(player=player)
                            for space in valid_spaces_to_trade:
                                # Check if space is a "missing" space.
                                if space.color in close_monopolies:
                                    """
                                    Check that we can afford the space according to the following criteria:
                                    1) If the space is not mortgaged, original purchase price.
                                    2) If the space is mortgaged, 5% mortgage fee + 50% of original purchase price.
                                    Note - We evaluate 55% of the purchase price in case of a mortgage, but the offer 
                                    will be for 50% only! (the 5% is used to pay the mortgage fee, as we never redeem 
                                    post trade).
                                    """
                                    space_trade_value = space.purchase_price if not space.is_mortgaged \
                                        else 0.55 * space.purchase_price
                                    if self.cash - space_trade_value > self.emergency_buffer:
                                        missing_spaces.append([
                                            player.name,                                          # Name of the player.
                                            valid_spaces_to_trade.index(space),                   # Index of the space.
                                            space_trade_value - (0 if not space.is_mortgaged      # Cash offer.
                                                                 else 0.05 * space.purchase_price)])

                        # Check that any "missing" spaces exist that can be traded.
                        if missing_spaces:
                            # Offer to trade space for cash.

                            # Not much thought over space selection - Select a random space.
                            space_to_trade = random.choice(missing_spaces)
                            self.trade_partner = space_to_trade[0]
                            self.trade_spaces = {"initiator": "", "recipient": space_to_trade[1]}
                            self.trade_cash = {"initiator": str(space_to_trade[2]), "recipient": str(0)}
                            self.is_active_action_taken = True
                            self.is_trade_attempted = True
                            log.logic(f"{self.name} - Offering to trade space for cash ({space_to_trade[2]}$) to "
                                      f"complete a monopoly, without breaching emergency buffer "
                                      f"(cash balance after purchase, "
                                      f"{self.cash}$ - {space_to_trade[2]}$ > {self.emergency_buffer}$)")
                            return "trade"

        elif self.cash > self.emergency_buffer and self.is_emergency_freeze:
            # Unable to perform an active cash spending action - buy/redeem.
            log.logic(f"{self.name} - Since emergency buffer was breached this turn, avoid active spending")

        else:
            # Emergency buffer is breached, self.cash < self.emergency_buffer.
            log.logic(f"{self.name} - Emergency buffer ({self.emergency_buffer}$) breached, trying to raise cash")
            self.is_emergency_freeze = True

            # Check if there are any non-mortgaged spaces left.
            if all(space.is_mortgaged for space in self.spaces):
                log.logic(f"{self.name} - No houses to sell or spaces to mortgage, cannot raise cash")
            else:
                # At least a space to mortgage.

                # DEVELOPMENT - SELLING HOUSE/HOTEL #

                # Find valid spaces to sell from.
                valid_spaces_to_sell_from = find_valid_spaces_to_sell_from(player=self, board=board)
                if valid_spaces_to_sell_from:
                    for monopoly in valid_spaces_to_sell_from:
                        log.logic(f"{self.name} - Selling a building to reach emergency buffer - "
                                  f"{self.emergency_buffer}$ "
                                  f"(gain - {valid_spaces_to_sell_from[monopoly][0].building_sell}$)")

                        # Not much thought over monopoly selection - First found that we are able to develop.
                        self.monopoly_sell = monopoly
                        # Not much thought over space selection - Select a random space.
                        self.space_sell = random.randint(0, len(valid_spaces_to_sell_from[monopoly]) - 1)
                        self.development_action = "sell"
                        return "develop"

                else:
                    # No valid spaces to sell from, we can only mortgage.

                    # MANAGEMENT - MORTGAGE #

                    # Find valid spaces to mortgage.
                    valid_spaces_to_mortgage = find_valid_spaces_to_mortgage(player=self)
                    # We already checked there are spaces to mortgage above, no need to check again.

                    # Not much thought over space selection - Select a random space.
                    self.space_mortgage = random.randint(0, len(valid_spaces_to_mortgage) - 1)
                    self.management_action = "mortgage"
                    return "manage"

        # Got to this point -> No active action possible/required.
        if not self.post_roll:
            return "roll"
        else:
            # Reset action parameters.
            self.development_action = None
            self.management_action = None
            self.jail_action = None
            self.is_active_action_taken = False
            self.is_emergency_freeze = False
            self.is_trade_attempted = False

            # Reset trade parameters.
            self.trade_partner = None
            self.trade_cash = None
            self.trade_spaces = None

            # Reset build parameters.
            self.monopoly_build = None
            self.space_build = None

            # Reset sell parameters.
            self.monopoly_sell = None
            self.space_sell = None

            # Reset mortgage parameters.
            self.space_mortgage = None

            # Reset redeem parameters.
            self.space_redeem = None

            # End the turn.
            return "end"

    # Passive #

    def buy_space_logic(self, space):
        # Make sure that the space purchase leaves a safe buffer in the cash balance.
        balance_after_purchase = self.cash - space.purchase_price

        if balance_after_purchase < self.safety_buffer:
            log.logic(f"{self.name} - Will not buy space (price - {space.purchase_price}$) due to breach of safety "
                      f"buffer (cash balance after purchase, {balance_after_purchase}$ < {self.safety_buffer}$)")
            return "n"
        else:
            log.logic(f"{self.name} - Buying space (price - {space.purchase_price}$) without breaching safety buffer "
                      f"(cash balance after purchase, {balance_after_purchase}$ >= {self.safety_buffer}$)")
            return "y"

    def auction_logic(self, space, latest_bid):
        """
        The auction logic is based on three principals:
        1) Bid increments are fixed at 30$.
        2) Bid value doesn't exceed space purchase value.
        3) Bid value doesn't breach safety buffer in the cash balance.
        """

        potential_bid = latest_bid + 30  # Principal (1).

        # Principal (2) - Check that bid value doesn't exceed space purchase value.
        if potential_bid > space.purchase_price:
            log.logic(f"{self.name} - Pass this round as new potential bid ({potential_bid}$) "
                      f"will be greater than space purchase price ({space.purchase_price}$)")
            return "pass"
        # Principal (3) - Check that bid value doesn't breach safety buffer.
        elif self.cash - potential_bid < self.safety_buffer:
            log.logic(f"{self.name} - Pass this round as new potential bid ({potential_bid}$) will breach safety "
                      f"buffer (cash balance after purchase, {self.cash - potential_bid}$ < {self.safety_buffer}$")
            return "pass"
        else:
            log.logic(f"{self.name} - Making a new bid (fixed increment of 30$ to {potential_bid}$) that is less than "
                      f"purchase value ({space.purchase_price}$) and doesn't breach safety buffer")
            return str(potential_bid)

    def raise_cash_logic(self):
        """Automate cash raising."""
        return "automate"

    # Trade #

    def trade_partner_logic(self):
        return self.trade_partner

    def trade_spaces_logic(self):
        return self.trade_spaces

    def trade_cash_logic(self):
        return self.trade_cash

    def trade_cards_logic(self):
        """Easy bot doesn't trade 'Get out of jail free' cards."""
        return {"initiator": 0, "recipient": 0}

    def trade_acceptance_logic(self, trade_offer_initiator,
                               initiator_space_offer, initiator_cash_offer, initiator_free_cards_offer,
                               recipient_space_offer, recipient_cash_offer, recipient_free_cards_offer):
        """
        The following trade logic principals are applied:
        1) We don't care who is the trade offer initiator.
        2) Accept trade offer if value of what we get is higher than what we give.

        Trade offer evaluation:
        * Cash.
        * Spaces - Either 10% mortgage value fee if mortgaged else purchase price.
        * 'Get out of jail free' cards - Evaluated the same as paying a jail fine.
        """

        # Evaluate the offer value.
        offer_value = self.trade_evaluation(
            spaces=initiator_space_offer, cash=initiator_cash_offer, free_cards=initiator_free_cards_offer)

        # Evaluate the return value.
        return_value = self.trade_evaluation(
            spaces=recipient_space_offer, cash=recipient_cash_offer, free_cards=recipient_free_cards_offer)

        # If we get more than we give accept, decline otherwise.
        if offer_value >= return_value:
            log.logic(f"{self.name} - Accepting trade because offer value, {offer_value}$, "
                      f"is higher than return value, {return_value}$")
            return "y"
        else:
            log.logic(f"{self.name} - Declining trade because offer value, {offer_value}$, "
                      f"is lower than return value, {return_value}$")
            return "n"

    @staticmethod
    def trade_evaluation(spaces: list, cash: int, free_cards: int):
        # Add offer cash value.
        offer_value = cash

        # Add spaces value.
        for space in spaces:
            offer_value += space.purchase_price if not space.is_mortgaged else (0.1 * space.mortgage_value)

        # Add 'Get out of jail free' cards - Values as a jail fine.
        offer_value += JAIL_FINE * free_cards

        return offer_value

    def post_trade_redeem_logic(self):
        log.logic(f"{self.name} - Never redeeming a space post trade")
        return "n"

    # Development #

    def development_logic(self):
        return self.development_action

    def monopoly_build_selection_logic(self):
        return self.monopoly_build

    def space_build_selection_logic(self):
        return str(self.space_build)

    def monopoly_sell_selection_logic(self):
        return self.monopoly_sell

    def space_sell_selection_logic(self):
        return str(self.space_sell)

    # Management #

    def management_logic(self):
        return self.management_action

    def mortgage_logic(self):
        return str(self.space_mortgage)

    def redeem_logic(self):
        """Never redeem a space."""
        return str(self.space_redeem)

    # Jail #

    def jail_logic(self):
        return self.jail_action
