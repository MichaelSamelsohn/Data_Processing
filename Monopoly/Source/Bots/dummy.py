# Imports #
from Monopoly.Settings.monopoly_settings import log, JAIL_FINE
from Monopoly.Source.Game.player import Player


class Dummy(Player):
    """Purpose of this bot is to serve as a completely passive playing partner. Useful for debug purposes."""
    def __init__(self, name):
        super().__init__(name=name, role="Dummy bot")

        # Action parameters.
        self.jail_action = None

    def play_turn_logic(self, board, players):
        """Roll and end the turn."""

        # Check if we are in jail (before rolling the dice).
        if self.in_jail and not self.post_roll:
            # We are in jail. Trying to get as soon as possible.

            # Primary option - Use a 'Get out of jail free' card.
            if self.free_cards > 0:
                log.logic(f"{self.name} - Using a 'Get out of jail free' card to get out of jail")
                self.jail_action = "free"
                return "jail"

            # Secondary option - Pay to get out of jail.
            if self.cash > JAIL_FINE:
                log.logic(f"{self.name} - Paying jail fine ({JAIL_FINE}$)")
                self.jail_action = "pay"
                return "jail"

            # Got to this point, unable to free ourselves from jail this turn. Will try our luck with rolling a double.
            log.logic(f"{self.name} - Unable to forcibly get out of jail, will try rolling a double")

        if not self.post_roll:
            return "roll"
        else:
            # Reset action parameters.
            self.jail_action = None

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

    def post_trade_redeem_logic(self):
        log.logic(f"{self.name} - Never redeeming a space post trade")
        return "n"

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
        """Dummy bot can never get to redeem, no point to implement logic."""
        pass

    def jail_logic(self):
        """"""
        return self.jail_action
