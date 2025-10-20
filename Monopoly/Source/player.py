# Imports #
from abc import abstractmethod

from Monopoly.Settings.monopoly_settings import log


class Player:
    def __init__(self, name, role):
        # General attributes.
        self.name = name
        self.role = role
        self.position = 0
        self.is_bankrupt = False
        # Assets.
        self.cash = 1500
        self.spaces = []
        # Jail related.
        self.free_cards = 0
        self.in_jail = False
        self.turns_in_jail = 0
        # Dice roll related.
        self.consecutive_double_rolls = 0
        self.post_roll = False

    def status(self):
        """TODO: Complete the docstring."""

        log.info("")  # Empty line to start the information print.
        log.info("--- Player status ---")

        # General information.
        log.info(f"Name - {self.name} ({self.role})")
        log.info(f"Position - {self.position}")

        # Assets information.
        log.info(f"Cash - {self.cash}")
        if self.spaces:
            log.info("Properties owned:")
            for p in self.spaces:
                p.print_information()

        # Jail related information.
        if self.in_jail:
            log.info(f"In jail - {self.in_jail} (for {self.turns_in_jail} turns)")
            log.info(f"'Get out of jail free' cards owned - {self.free_cards}")

        # Dice roll information.
        log.info(f"Dice rolled this turn - {self.post_roll}")
        if self.consecutive_double_rolls > 0:
            log.info(f"consecutive doubles rolled {self.consecutive_double_rolls}")

        log.info("")  # Empty line to end the information print.


class Human(Player):
    def __init__(self, name):
        super().__init__(name=name, role="Human")


class Bot(Player):
    def __init__(self, name, role):
        super().__init__(name=name, role=role)

    @abstractmethod
    def play_turn_logic(self):
        pass

    @abstractmethod
    def buy_space_logic(self):
        pass

    @abstractmethod
    def auction_logic(self):
        pass

    @abstractmethod
    def raise_cash_logic(self):
        pass

    @abstractmethod
    def trade_acceptance_logic(self):
        pass

    @abstractmethod
    def development_logic(self):
        pass

    @abstractmethod
    def monopoly_build_logic(self):
        pass

    @abstractmethod
    def build_logic(self):
        pass

    @abstractmethod
    def monopoly_sell_logic(self):
        pass

    @abstractmethod
    def sell_logic(self):
        pass

    @abstractmethod
    def management_logic(self):
        pass

    @abstractmethod
    def mortgage_logic(self):
        pass

    @abstractmethod
    def redeem_logic(self):
        pass


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
