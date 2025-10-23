# Imports #
import random

from Monopoly.Settings.monopoly_settings import log
from Monopoly.Source.Bots.bot import Bot
from Monopoly.Source.game import find_valid_spaces_to_build_on


class Easy(Bot):
    """Purpose of this bot is to serve as an amateurish playing partner."""
    def __init__(self, name):
        super().__init__(name=name, role="Easy bot")

        # Cash buffers.
        self.safety_buffer = 500       # This buffer is defined for purchasing houses/hotels.
        self.emergency_buffer = 200    # This emergency buffer is used to pay fines and rent.

        # Build.
        self.monopoly_build = None
        self.space_build = None
        self.house_built_this_turn = False
        self.current_development_action = None

    def play_turn_logic(self, board, players):
        if self.cash > self.emergency_buffer:
            # We have enough cash, consider building a house/hotel (one per turn).
            if not self.house_built_this_turn:
                valid_spaces_to_build_on = find_valid_spaces_to_build_on(player=self, board=board)
                if valid_spaces_to_build_on:
                    cash_needed = []  # To track the cash lacking to develop in case we can't develop anything.
                    for monopoly in valid_spaces_to_build_on:
                        # Check if we have enough cash to build without dropping below emergency buffer.
                        if self.cash - valid_spaces_to_build_on[monopoly][0].building_cost > self.emergency_buffer:
                            # Developing monopoly.
                            log.logic(f"{self.name} - Developing a monopoly "
                                      f"(cost - {valid_spaces_to_build_on[monopoly][0].building_cost}$) "
                                      f"without breaching emergency buffer (cash balance after purchase, "
                                      f"{self.cash}$ - {valid_spaces_to_build_on[monopoly][0].building_cost}$ "
                                      f"> {self.emergency_buffer}$)")

                            # Not much thought over monopoly selection - First found that we are able to develop.
                            self.monopoly_build = monopoly
                            # Not much thought over space selection - Select a random space.
                            self.space_build = random.randint(0, len(valid_spaces_to_build_on[monopoly]) - 1)
                            self.house_built_this_turn = True
                            self.current_development_action = "build"
                            return "develop"
                        else:
                            # Lacking the cash to develop.
                            cash_needed.append(self.emergency_buffer - (self.cash - monopoly[0].building_cost))

                    # Check if we lack the cash to develop.
                    if not self.monopoly_build and not self.space_build:
                        log.logic(f"{self.name} - Unable to develop an owned monopoly due to lack of cash, need at "
                                  f"least {min(cash_needed)}$ to develop without breaching emergency buffer")

        if not self.post_roll:
            return "roll"
        else:
            # Reset build values.
            self.monopoly_build = None
            self.space_build = None
            self.house_built_this_turn = False
            self.current_development_action = None
            return "end"

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

    def trade_acceptance_logic(self):
        """Accept all deals."""
        return "y"

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
        pass

    def space_sell_selection_logic(self):
        """Dummy bot can never get to sell, no point to implement logic."""
        pass

    def management_logic(self):
        """Dummy bot can never get to management, no point to implement logic."""
        pass

    def mortgage_logic(self):
        """Dummy bot can never get to mortgage, no point to implement logic."""
        pass

    def redeem_logic(self):
        """Never redeem a space."""
        return "n"
