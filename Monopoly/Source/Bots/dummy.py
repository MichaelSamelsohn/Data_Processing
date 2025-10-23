# Imports #
from Monopoly.Settings.monopoly_settings import log
from Monopoly.Source.Bots.bot import Bot


class Dummy(Bot):
    """Purpose of this bot is to serve as a completely passive playing partner. Useful for debug purposes."""
    def __init__(self, name):
        super().__init__(name=name, role="Dummy bot")

    def play_turn_logic(self, board, players):
        """Roll and end the turn."""
        if not self.post_roll:
            return "roll"
        else:
            return "end"

    def buy_space_logic(self, space):
        """Never buy any space."""
        log.logic(f"{self.name} - Never buy a space")
        return "n"

    def auction_logic(self, space, latest_bid):
        """Never bid at an auction."""
        log.logic(f"{self.name} - Never bidding at an auction")
        return "pass"

    def raise_cash_logic(self):
        """Automate cash raising."""
        return "automate"

    def trade_acceptance_logic(self, trade_offer_initiator,
                               initiator_space_offer, initiator_cash_offer, initiator_free_cards_offer,
                               recipient_space_offer, recipient_cash_offer, recipient_free_cards_offer):
        """Accept all deals."""
        log.logic(f"{self.name} - Accepting all trade offers")
        return "y"

    def development_logic(self):
        """Dummy bot can never get to develop, no point to implement logic."""
        pass

    def monopoly_build_selection_logic(self):
        """Dummy bot can never get to build, no point to implement logic."""
        pass

    def space_build_selection_logic(self):
        """Dummy bot can never get to build, no point to implement logic."""
        pass

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
        log.logic(f"{self.name} - Never redeeming a space")
        return "n"
