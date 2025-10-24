# Imports #
from abc import abstractmethod, ABC

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
        log.info(f"Cash - {self.cash}$")
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

    @abstractmethod
    def play_turn_logic(self, board, players):
        pass

    @abstractmethod
    def buy_space_logic(self, space):
        pass

    @abstractmethod
    def auction_logic(self, space, latest_bid):
        pass

    @abstractmethod
    def raise_cash_logic(self):
        pass

    @abstractmethod
    def trade_acceptance_logic(self, trade_offer_initiator,
                               initiator_space_offer, initiator_cash_offer, initiator_free_cards_offer,
                               recipient_space_offer, recipient_cash_offer, recipient_free_cards_offer):
        pass

    @abstractmethod
    def post_trade_redeem_logic(self):
        pass

    @abstractmethod
    def development_logic(self):
        pass

    @abstractmethod
    def monopoly_build_selection_logic(self):
        pass

    @abstractmethod
    def space_build_selection_logic(self):
        pass

    @abstractmethod
    def monopoly_sell_selection_logic(self):
        pass

    @abstractmethod
    def space_sell_selection_logic(self):
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


class Human(Player, ABC):
    def __init__(self, name):
        super().__init__(name=name, role="Human")
