# Imports #
from Monopoly.Source.Bots.bot import Bot


class Dummy(Bot):
    """Purpose of this bot is to serve as a completely passive playing partner. Useful for debug purposes."""
    def __init__(self, name):
        super().__init__(name=name, role="Dummy bot")

    def play_turn_logic(self):
        """Roll and end the turn."""
        if not self.post_roll:
            return "roll"
        else:
            return "end"

    def buy_space_logic(self):
        """Never buy any space."""
        return "n"

    def auction_logic(self):
        """Never bid at an auction."""
        return "pass"

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
