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
