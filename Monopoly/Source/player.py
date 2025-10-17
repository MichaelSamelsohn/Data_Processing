# Imports #
from abc import abstractmethod

from Monopoly.Settings.monopoly_settings import log


class Player:
    def __init__(self, name, role):
        # General attributes.
        self.name = name
        self.role = role
        self.position = 0
        # Assets.
        self.cash = 1500
        self.properties = []
        # Jail related.
        self.free_cards = 0
        self.in_jail = False
        self.turns_in_jail = 0
        # Dice roll related.
        self.consecutive_double_rolls = 0
        self.post_roll = False

    def status(self):
        """TODO: Complete the docstring."""

        log.debug("")

        # General information.
        log.info(f"Player {self.name} ({self.role})")
        log.info(f"Position - {self.position}")

        # Assets information.
        log.info(f"Cash - {self.cash}")
        for p in self.properties:
            p.print_information()

        # Jail related information.
        if self.free_cards > 0:
            log.info(f"'Get out of jail free' cards owned - {self.free_cards}")
        log.info(f"In jail - {self.in_jail} {f"(for {self.turns_in_jail} turns)" if self.in_jail else ""}")

        # Dice roll information.
        log.info(f"Dice rolled this turn - {self.post_roll}")
        if self.consecutive_double_rolls > 0:
            log.info(f"consecutive doubles rolled {self.consecutive_double_rolls}")

        log.debug("")


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
    def buy_property_logic(self):
        pass

    @abstractmethod
    def trade_acceptance_logic(self):
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

    def buy_property_logic(self):
        """Decline to buy all properties."""
        return "n"

    def trade_acceptance_logic(self):
        """Decline any trade offer."""
        return "y"
