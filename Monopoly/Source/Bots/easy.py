# Imports #
from Monopoly.Source.Bots.bot import Bot


class Easy(Bot):
    """Purpose of this bot is to serve as an amateurish playing partner."""
    def __init__(self, name):
        super().__init__(name=name, role="Easy bot")

        self.safe_buffer = 500       # This buffer is defined for purchasing houses/hotels.
        self.emergency_buffer = 200  # This emergency buffer is used to pay fines and rent.

    def play_turn_logic(self):
        """Roll and end the turn."""
        if not self.post_roll:
            return "roll"
        else:
            return "end"

    def buy_space_logic(self, space):
        # Make sure that the space purchase leaves a safe buffer in the cash balance.
        if self.cash - space.purchase_price < self.safe_buffer:
            return "n"
        else:
            return "y"

    def auction_logic(self, space, latest_bid):
        """
        The auction logic is based on three principals:
        1) Bid increments are fixed at 30$.
        2) Bid value doesn't exceed space purchase value.
        3) Bid value doesn't breach 500$ buffer in the cash balance.
        """

        potential_bid = latest_bid + 30  # Principal (1).

        # Principals (2)+(3).
        if (potential_bid > space.purchase_price) or (self.cash - potential_bid < self.safe_buffer):
            return "pass"
        else:
            # Can afford bid increment.
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
