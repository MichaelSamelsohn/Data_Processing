# Imports #
from Monopoly.Settings.monopoly_settings import log
from Monopoly.Source.Bots.bot import Bot


class Easy(Bot):
    """Purpose of this bot is to serve as an amateurish playing partner."""
    def __init__(self, name):
        super().__init__(name=name, role="Easy bot")

        self.safety_buffer = 500       # This buffer is defined for purchasing houses/hotels.
        self.emergency_buffer = 200    # This emergency buffer is used to pay fines and rent.

    def play_turn_logic(self, board, players):
        if not self.post_roll:
            return "roll"
        else:
            return "end"

    def buy_space_logic(self, space):
        # Make sure that the space purchase leaves a safe buffer in the cash balance.
        balance_after_purchase = self.cash - space.purchase_price

        if balance_after_purchase < self.safety_buffer:
            log.logic(f"{self.name} - Will not buy space due to breach of safety buffer "
                      f"(cash balance after purchase, {balance_after_purchase}$ < {self.safety_buffer}$)")
            return "n"
        else:
            log.logic(f"{self.name} - Buying space without breaching safety buffer "
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
        pass

    def monopoly_build_logic(self):
        """Dummy bot can never get to build, no point to implement logic."""
        pass

    def build_logic(self):
        """Dummy bot can never get to build, no point to implement logic."""
        pass

    def monopoly_sell_logic(self):
        """Dummy bot can never get to sell, no point to implement logic."""
        pass

    def sell_logic(self):
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
