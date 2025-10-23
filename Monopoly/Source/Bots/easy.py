# Imports #
import random

from Monopoly.Settings.monopoly_settings import *
from Monopoly.Source.Bots.bot import Bot
from Monopoly.Source.game import *


class Easy(Bot):
    """Purpose of this bot is to serve as an amateurish playing partner."""
    def __init__(self, name):
        super().__init__(name=name, role="Easy bot")

        # Cash buffers.
        self.safety_buffer = 500          # This buffer is defined for purchasing houses/hotels.
        self.emergency_buffer = 200       # This emergency buffer is used to pay fines and rent.
        self.is_emergency_freeze = False  # If emergency buffer was breached this turn (to avoid spending cash).

        # Action parameters.
        self.current_development_action = None

        # Build parameters.
        self.monopoly_build = None
        self.space_build = None
        self.house_built_this_turn = False

        # Sell parameters.
        self.monopoly_sell = None
        self.space_sell = None

    # Main logic #

    def play_turn_logic(self, board, players):
        if self.cash >= self.emergency_buffer and not self.is_emergency_freeze:
            # We have enough cash, consider building a house/hotel (one per turn).
            if not self.house_built_this_turn:
                valid_spaces_to_build_on = find_valid_spaces_to_build_on(player=self, board=board)
                if valid_spaces_to_build_on:
                    cash_needed = []  # To track the cash lacking to develop in case we can't develop anything.
                    for monopoly in valid_spaces_to_build_on:
                        # Check if we have enough cash to build without dropping below emergency buffer.
                        build_cost = valid_spaces_to_build_on[monopoly][0].building_cost
                        if self.cash - build_cost > self.emergency_buffer:
                            # Developing (buying house/hotel) monopoly.
                            log.logic(f"{self.name} - Buying a building (cost - {build_cost}$) to gain higher rent, "
                                      f"without breaching emergency buffer (cash balance after purchase, "
                                      f"{self.cash}$ - {build_cost}$ > {self.emergency_buffer}$)")

                            # Not much thought over monopoly selection - First found that we are able to develop.
                            self.monopoly_build = monopoly
                            # Not much thought over space selection - Select a random space.
                            self.space_build = random.randint(0, len(valid_spaces_to_build_on[monopoly]) - 1)
                            self.house_built_this_turn = True
                            self.current_development_action = "build"
                            return "develop"
                        else:
                            # Lacking the cash to develop.
                            cash_needed.append(self.emergency_buffer - (self.cash - build_cost))

                    # Check if we lack the cash to develop.
                    if not self.monopoly_build and not self.space_build:
                        log.logic(f"{self.name} - Unable to develop an owned monopoly due to lack of cash, need at "
                                  f"least {min(cash_needed)}$ to develop without breaching emergency buffer")
                else:
                    # No valid spaces to build on.
                    pass # TODO: redeem logic to acquire a monopoly (to later build houses).

        elif self.cash > self.emergency_buffer and self.is_emergency_freeze:
            log.logic(f"{self.name} - Since emergency buffer was breached this turn, avoid active spending")

        else:
            # Emergency buffer is breached, self.cash < self.emergency_buffer.
            self.is_emergency_freeze = True

            # Check if there are houses to sell.
            valid_spaces_to_sell_from = find_valid_spaces_to_sell_from(player=self, board=board)
            if valid_spaces_to_sell_from:
                for monopoly in valid_spaces_to_sell_from:
                    # Developing (selling house/hotel) monopoly.
                    log.logic(f"{self.name} - Selling a building to reach emergency buffer - {self.emergency_buffer}$ "
                              f"(gain - {valid_spaces_to_sell_from[monopoly][0].building_sell}$)")

                    # Not much thought over monopoly selection - First found that we are able to develop.
                    self.monopoly_sell = monopoly
                    # Not much thought over space selection - Select a random space.
                    self.space_sell = random.randint(0, len(valid_spaces_to_sell_from[monopoly]) - 1)
                    self.current_development_action = "sell"
                    return "develop"

            else:
                # No valid spaces to sell from.
                pass  # TODO: mortgage logic to raise cash for maintaining emergency buffer.

        # Got to this point -> No active action required.
        if not self.post_roll:
            return "roll"
        else:
            # Reset cash values.
            self.is_emergency_freeze = False

            # Reset action parameters.
            self.current_development_action = None

            # Reset build parameters.
            self.monopoly_build = None
            self.space_build = None
            self.house_built_this_turn = False

            # Reset sell parameters.
            self.monopoly_sell = None
            self.space_sell = None

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
                      f"purchase value and doesn't breach safety buffer")
            return str(potential_bid)

    def raise_cash_logic(self):
        """Automate cash raising."""
        return "automate"

    # Trade #

    def trade_acceptance_logic(self, trade_offer_initiator,
                               initiator_space_offer, initiator_cash_offer, initiator_free_cards_offer,
                               recipient_space_offer, recipient_cash_offer, recipient_free_cards_offer):
        """
        The following trade logic principals are applied:
        1) We don't care who is the trade offer initiator.
        2) Accept trade offer if value is what we get is higher than what we give.

        Trade offer evaluation:
        * Cash.
        * Spaces - Either 10% mortgage value fee if mortgaged else purchase price.
        * 'Get out of jail free' cards - Evaluated the same as paying a jail fine.
        """

        # Evaluate the offer value.
        offer_value = self.trade_offer_evaluation(
            spaces=initiator_space_offer, cash=initiator_cash_offer, free_cards=initiator_free_cards_offer)

        # Evaluate the return value.
        return_value = self.trade_offer_evaluation(
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

    # Development #

    def development_logic(self):
        """Dummy bot can never get to develop, no point to implement logic."""
        return self.current_development_action

    def monopoly_build_selection_logic(self):
        """Dummy bot can never get to build, no point to implement logic."""
        return self.monopoly_build

    def space_build_selection_logic(self):
        """Dummy bot can never get to build, no point to implement logic."""
        return str(self.space_build)

    def monopoly_sell_selection_logic(self):
        """Dummy bot can never get to sell, no point to implement logic."""
        return self.monopoly_sell

    def space_sell_selection_logic(self):
        """Dummy bot can never get to sell, no point to implement logic."""
        return str(self.space_sell)

    # Management #

    def management_logic(self):
        """Dummy bot can never get to management, no point to implement logic."""
        pass

    def mortgage_logic(self):
        """Dummy bot can never get to mortgage, no point to implement logic."""
        pass

    def redeem_logic(self):
        """Never redeem a space."""
        return "n"
