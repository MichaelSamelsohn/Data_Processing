# Imports #
from abc import abstractmethod

from Monopoly.Source.player import Player


class Bot(Player):
    def __init__(self, name, role):
        super().__init__(name=name, role=role)

    @abstractmethod
    def play_turn_logic(self):
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